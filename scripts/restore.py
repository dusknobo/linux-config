#!/usr/bin/env python3
"""Review or restore an explicit component set; dry-run unless --apply is given."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]

def reject_links(path, base):
    relative = path.relative_to(base)
    current = base
    if base.is_symlink():
        raise ValueError(f'Symbolic link is not allowed: {base}')
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symbolic link is not allowed: {current}')
        if current.exists() and current != path and not current.is_dir():
            raise ValueError(f'Non-directory parent: {current}')

def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version') != 1:
        raise ValueError('Unsupported manifest version')
    components = sorted({entry['component'] for entry in manifest['files']})
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', action='append', choices=components + ['all'],
                        help='Repeat to select components. Default: all except the Rime overlay.')
    parser.add_argument('--apply', action='store_true', help='Back up existing files, then write selected settings')
    args = parser.parse_args()
    if os.name != 'posix' or os.geteuid() == 0:
        raise ValueError('Run as your normal Linux user, never with sudo')
    home = Path.home().absolute()
    if home == Path('/') or not home.is_dir():
        raise ValueError('Invalid home directory')
    # The rendered value is inside quoted KDL/TOML strings in these templates.
    if any(c in str(home) for c in ('"', '\\', '\n', '\r', '@')):
        raise ValueError('Home path contains unsupported template characters')
    selected = set(args.component or [c for c in components if c != 'rime'])
    if 'all' in selected:
        selected = set(components)
    plan, targets = [], set()
    for entry in manifest['files']:
        if entry['component'] not in selected:
            continue
        source_rel = PurePosixPath(entry['source'])
        target_rel = PurePosixPath(entry['target'])
        if source_rel.is_absolute() or target_rel.is_absolute() or '..' in source_rel.parts or '..' in target_rel.parts:
            raise ValueError('Unsafe manifest path')
        target_name = str(target_rel)
        if not (target_name.startswith('.config/') or target_name.startswith('.local/share/fcitx5/rime/')):
            raise ValueError('Unexpected target location')
        if target_name in targets:
            raise ValueError('Duplicate target')
        targets.add(target_name)
        source = ROOT / source_rel
        target = home / target_rel
        reject_links(source, ROOT)
        reject_links(target, home)
        if not source.is_file() or (target.exists() and not target.is_file()):
            raise ValueError(f'Expected a regular configuration file: {target_rel}')
        payload = source.read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry['sha256']:
            raise ValueError(f'Snapshot checksum differs: {source_rel}; review and update manifest.json before restoring')
        if entry.get('template'):
            payload = payload.decode('utf-8').replace('@HOME@', str(home)).encode('utf-8')
        plan.append((entry, target, payload))
    if 'rime' in selected:
        rime = home / '.local/share/fcitx5/rime'
        required = ['rime.lua', 'melt_eng.schema.yaml', 'melt_eng.dict.yaml',
                    'stroke.schema.yaml', 'stroke.dict.yaml', 'radical_pinyin.schema.yaml',
                    'radical_pinyin.dict.yaml', 'wubi98_mint.schema.yaml', 'wubi98_mint.dict.yaml',
                    'symbols.yaml', 'dicts/rime_ice.cn_en_flypy.txt']
        dictionary = (ROOT / 'home/.local/share/fcitx5/rime/rime_mint.dict.yaml').read_text(encoding='utf-8')
        for name in re.findall(r'^\s+- (dicts/[A-Za-z0-9_.-]+)\s*(?:#.*)?$', dictionary, re.M):
            if name != 'dicts/hz_technical':
                required.append(name + '.dict.yaml')
        missing = [name for name in required if not (rime / name).is_file()]
        if not (rime / 'lua').is_dir():
            missing.append('lua/')
        if missing:
            raise ValueError('Rime overlay needs the existing Mint installation and dictionary dependencies first: ' + ', '.join(missing))
    for entry, target, _ in plan:
        print(f"{entry['component']:9} {'replace' if target.exists() else 'create ':7} ~/{entry['target']}")
    if not args.apply:
        print(f'Dry-run: {len(plan)} files, nothing changed. Add --apply only after review.')
        return
    backup = home / '.local/state/linux-config/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    reject_links(backup, home)
    backup.mkdir(parents=True, mode=0o700, exist_ok=False)
    record = []
    # Complete all backups before overwriting any configuration file.
    for entry, target, payload in plan:
        existed = target.exists()
        if existed:
            saved = backup / entry['target']
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        record.append({'target': entry['target'], 'previously_existed': existed,
                       'new_sha256': hashlib.sha256(payload).hexdigest()})
    (backup / 'restore-record.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(f'Backup: {backup}')
    for entry, target, payload in plan:
        reject_links(target, home)
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
        with tempfile.NamedTemporaryFile(prefix='.linux-config-', dir=target.parent, delete=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        temporary.chmod(mode)
        os.replace(temporary, target)
    print(f'Restored {len(plan)} files. No services or applications were restarted.')
    print('Use the backup record to restore only prior files; do not replace newer user-learning data.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f'Refused/failed: {error}')
