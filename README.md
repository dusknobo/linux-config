# Linux configuration

Fedora 44 上的个人 Linux 配置快照，桌面为 **Niri + Noctalia**。这是经过脱敏的公开仓库，不是整个用户目录或系统镜像。

## 保存了什么

| 组件 | 内容 |
| --- | --- |
| Niri | Alt 主修饰键、Vim 风格窗口/跨工作区操作、原方向键、媒体键、XKB 换键 |
| Noctalia | 信息丰富的状态栏、截图、夜间色温、闲置 10 分钟锁屏/11 分钟熄屏，不自动休眠 |
| Fish | 用户开发工具路径、默认终端与输入法相关环境变量 |
| Kitty | 当前生效的设置及 Tokyo Night 配色，省略没有作用的默认注释 |
| Zellij | 默认锁定模式、Win/Super 组合键、保留 Neovim 常用 Ctrl 按键 |
| btop | 当前显示和性能监测选项，省略默认注释 |
| Fcitx5 | Ctrl+Space、Rime 优先的输入法顺序、拼音选项及自动启动项 |
| Rime 定制 | 小鹤双拼/薄荷全拼方案、词库入口及独立的编程/Linux/数学词库；不包含学习数据库 |

完整路径清单与每个源文件的 SHA256 见 [manifest.json](manifest.json)。

Neovim 继续独立维护在 [dusknobo/nvimConfig](https://github.com/dusknobo/nvimConfig)，这里不嵌入另一个 Git 仓库，也不改变它的版本。

## 恢复入口

先安装对应的软件，再恢复配置。没有一键安装系统软件、修改默认 shell、启用服务或重启桌面的操作。

```sh
git clone https://github.com/dusknobo/linux-config.git
cd linux-config

# 默认只预览，不修改文件；默认不包含需要额外依赖的 Rime 定制层。
python3 scripts/restore.py

# 只预览某个组件；--component 可重复。
python3 scripts/restore.py --component niri --component noctalia

# 确认计划后，明确添加 --apply。
python3 scripts/restore.py --component niri --component noctalia --apply
```

脚本只允许清单中的用户配置路径，校验源文件 SHA256，拒绝符号链接和路径越界。在覆盖任何文件前，先把全部已有目标备份到 `~/.local/state/linux-config/backups/`，并记录哪些文件原本不存在。请以普通用户运行，**不要 sudo**。发生错误时，已完成的写入不会自动回滚，请依据备份记录恢复相应文件。

恢复不会自动重载正在运行的程序。请先查看配置差异，再自行重新打开终端、重新部署输入法，或重新登录桌面。

## 重要差异与前置依赖

- `.in` 文件中的 `@HOME@` 会由恢复脚本替换为当前主目录；不把原机器的绝对个人路径写死在仓库里。
- 墙纸及截图目录保留 `Picture/Wallpapers`、`Picture/Screenshots` 的目录约定。图片本身不上传，也不会自动创建目录或设置某张墙纸。
- Noctalia 状态栏 CPU/RAM 点击操作在公开快照中改为 `kitty -e btop`，与本仓库终端一致；原笔记本设置未改。
- Niri 快捷键引用 `kitty`、`pcmanfm-qt` 和 `noctalia`；需要自行安装这些程序。
- Fish 的路径设置不会安装 Rust、uv、Typst 或其他开发工具。原内网代理不上传；[代理示例](examples/70-proxy.fish.example)默认禁用，且不会随恢复脚本安装。
- Kitty 使用默认字体选择，本仓库不附带字体文件。需要 Nerd 图标时，请另行安装合适的 Nerd Font，并按个人需要配置字体。
- Zellij 的 Super 组合键需要支持相应键盘协议的终端。Typst 的 Neovim 内嵌 PDF 预览请在 Kitty 中直接运行，不要放在 Zellij 内。

## Rime：这是定制层，不是完整发行包

先安装 Fcitx5、fcitx5-rime、librime-lua，以及 [oh-my-rime（薄荷）](https://github.com/Mintimate/oh-my-rime) 的配套 Lua、英文、中英混输、反查与基础词库数据。不要将这里几个文件复制进一个空 Rime 目录后就期待可以输入。

万象数据快照来源、七个文件的 Git blob SHA 与条目数量见 [docs/wanxiang-source.json](docs/wanxiang-source.json)。对应官方数据提交为 [`a4c5c5b`](https://github.com/amzxyz/rime-wanxiang-data/tree/a4c5c5bc2ce7aacbcc849378c413724d78c273d6)。上游数据只适配了薄荷词典名称，没有改变条目、声调或权重。大型通用词库不在本仓库重复保存；请安装与当前入口名称匹配的数据，不能直接用上游 `zi`/`jichu` 文件名替代 `rime_mint.chars`/`rime_mint.base`。

独立的 `hz_technical.dict.yaml` 包含 180 个补充词码对（编程 95、Linux 51、数学 34）。另有 99 个筛选词已经在主词库中，因此不重复添加。扩展词带声调全拼交由现有小鹤规则转换，不改变双拼布局。

```sh
# 先确认原有薄荷依赖及匹配名称的万象数据已经存在。
python3 scripts/restore.py --component rime
python3 scripts/restore.py --component rime --apply
```

脚本会在写入前检查必要依赖。恢复后，通过 Fcitx5 的 Rime 菜单执行“重新部署”。默认方案列表保持小鹤双拼优先、薄荷全拼备用；不恢复其他机器的上次会话或个人学习数据库。

## 公开范围与安全

不上传 SSH/GPG/API 密钥、登录凭据、代理真实地址、Wi-Fi/蓝牙连接记录、定位数据、Fish 历史/通用变量、Rime UserDB、剪贴板、通知、会话、缓存、日志、壁纸和截图。不会保存浏览器或 AI 工具的账号目录。不要将整个 `.config` 或维护备份目录直接 `git add`。

以后更新时请只挑选必要文件，重新检查敏感信息。修改受清单管理的文件后，应人工审阅差异，再更新对应 SHA256；恢复脚本不会自动接受不匹配的内容。

## 验证基线

2026-10-24 采集的版本：Fedora 44、Niri 26.04、Noctalia 5.3.0、Fish 4.6.0、Kitty 0.47.1、Zellij 0.45.1、btop 1.4.7、Fcitx5 5.1.23。版本仅记录验证环境，不代表自动安装要求或永远兼容后续版本。

这次发布不会修改笔记本正在使用的配置。Rime 词库此前已通过 279 项技术词和 20 项日常输入测试；仓库恢复脚本及配置格式另行在隔离目录验证。

## 第三方来源

- Rime 方案与词库入口基于 [Mintimate/oh-my-rime](https://github.com/Mintimate/oh-my-rime)，保留原文件注释和 [GPL-3.0 许可证](LICENSES/oh-my-rime-GPL-3.0.txt)。词库入口增加了本地技术词库引用。
- Kitty Tokyo Night 配色保留原作者 Folke Lemaitre、来源及原文件中的 MIT 标注；同时附带下载时 [tokyonight.nvim 上游 LICENSE](LICENSES/tokyonight-upstream-APACHE-2.0.txt)。不把第三方文件的许可扩展为整个个人配置仓库的统一许可。
