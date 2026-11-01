# dsh-skill-hub

给 DeepSeek Harness（dsh）用的**技能仓库管理器**：配置一个或多个公开 GitHub 仓库，扫描其中的 `SKILL.md`，一键安装或更新到本机，并立即注册给正在运行的 Harness。

## 功能

- **多仓库配置**：填 `owner/repo` 或 GitHub 链接即可，可指定分支 / Tag。
- **扫描**：解析仓库默认分支（或指定 ref）的 HEAD commit，列出其中所有技能及其描述。
- **单技能安装 / 更新**：扫描结果里每个技能都有独立按钮——未安装显示「安装」、可更新显示「更新」、已最新显示「重装」、仓库中已移除只显示「卸载」；点击只处理该技能，不影响同仓库其它技能。
- **一键安装 / 更新**：按 commit SHA 对比，按钮自带「未安装 / 可更新 / 已最新」状态判断，按仓库批量处理。
- **列表折叠**：技能超过 5 个的仓库默认折叠成一行摘要（显示前几个技能名与状态计数），可单独「展开技能」，也可用顶部的「全部展开 / 全部折叠」，避免长列表把设置页拉得很长。
- **运行时注册**：安装后通过 `ctx.skills.register()` 直接注册进 Harness，**不依赖**被 web profile 禁用的文件系统技能 provider。
- **注册表核对**：面板直接读 Harness 的技能注册表（`ctx.skills.list()`），显示「共 N 个、其中本插件注册 M 个」，用于确认注册真的生效，而不是只看插件自己的计数。
- **卸载与移除**：可单独卸载某个技能，或移除仓库时连同其技能一并删除。

> 单技能的「安装 / 更新」安装的是**当前扫描**锁定的 commit，与整仓按钮用的是同一个 pin；想让按钮看到最新提交，先点「扫描」。

## 安装

```sh
# 在插件目录的父目录执行；相对路径会按当前目录解析
dsh plugin --profile web add ./dsh-skill-hub
```

安装后**重启 `dsh web`**（bundle 列表只在启动时读取），然后在 **设置 → 技能仓库** 里使用。

## 使用

1. 打开 **设置 → 技能仓库**。
2. 输入仓库，例如 `liustack/modlens`，点「添加并扫描」。
3. 查看扫描到的技能与状态（未安装 / 可更新 / 已最新）；技能多于 5 个时列表默认折叠，点仓库行的「展开技能（N）」查看，或用「全部展开 / 全部折叠」。
4. 单独处理某个技能：点该技能行右侧的「安装 / 更新 / 重装」按钮。
5. 或整仓批量：点仓库行的「一键安装 / 更新」、顶部的「一键安装 / 更新全部」。
6. 装好的技能立刻可用：在对话里点 `skill` 工具或直接按名称调用。

## 数据布局

```text
$DSH_HOME/skill-hub/                 # DSH_HOME 默认 ~/.dsh
├── config.json                      # 配置的仓库列表
├── state.json                       # 扫描结果与已安装技能记录（含来源 SHA）
├── cache/<owner>__<repo>/<sha>/     # 按 commit 缓存的仓库快照
└── skills/<owner>__<repo>/<skill>/  # 已安装的技能目录（含 scripts/references 等全部文件）
```

## 安全设计

- **网络**：每个仓库一次扫描只发 2~3 个请求（仓库信息、commit、tarball），中间结果按 commit 缓存，避免 GitHub 未认证限流（60 次/小时）。
- **仅公开仓库**：不保存任何 token。
- **接口围栏**：`/skill-hub/api` 只接受**本机同源**请求——校验 `host` 必须为 loopback、拒绝 `sec-fetch-site: cross-site`、`origin` 必须与 host 一致。
- **不自动执行**：安装只做文件复制与技能注册，不会运行仓库中的脚本；技能里的脚本只有在你（或模型）按技能说明主动调用时才会执行。

## 已知限制

- 仅支持公开仓库（私有仓库需要 token，尚未实现）。
- 扫描需要下载整个仓库 tarball，超大仓库会较慢（首次扫描可能十几秒）。
- `SKILL.md` 必须声明 kebab-case 的 `name` 与非空 `description`，否则会被跳过并在「跳过的条目」中列出原因。
- 同名技能跨仓库冲突时，先注册者生效，冲突项会在「未注册的技能」里报告。
- 客户端 bundle 是手写的 lazy-CJS 包装（DSH 未发布 client 构建预设），因此不使用 JSX。

## 开发与测试

```sh
pnpm install

node test/smoke.mjs  liustack/modlens   # GitHub 层：解析 commit、下载解压、缓存命中
node test/service.mjs liustack/modlens  # 30 项：扫描 → 整仓/单技能安装 → 注册 → 更新判定 → 卸载
node test/api.mjs                        # 16 项：同源围栏、方法、分发（含 installSkill）
node test/host.mjs  liustack/modlens    # 26 项：假 ctx 装载真实插件，走真实 HTTP 全链路
node test/client.mjs                     # 41 项：bundle 注册、槽位契约、加载态、有数据渲染、单技能按钮、列表折叠
```

共 113 项检查，全部不需要运行中的 Harness：

- 每个测试都通过 `test/helpers.mjs` 把 `DSH_HOME` 指向临时目录，因此**互不干扰、也不会写你的 `~/.dsh`**（仓库缓存会从真实目录播种，保持离线快速）；
- `service` 用一个假的 skill registry 捕获注册行为；
- `host` 用假 cordis ctx 装载真实插件，并直接驱动真实 HTTP handler；
- `client` 在 `node:vm` 里模拟 `window.__ModuleLoader__` 与 React，连渲染路径一起跑。

集成验证（真机）可用隔离 HOME 复刻 profile，不干扰正在使用的实例：

```sh
mkdir -p /tmp/dsh-verify
DSH_HOME=/tmp/dsh-verify dsh plugin --profile web add /path/to/dsh-skill-hub
DSH_HOME=/tmp/dsh-verify dsh web --port 3099 --no-open
curl http://127.0.0.1:3099/skill-hub/api
```

## 结构

```text
dsh-skill-hub/
├── package.json          # dsh.bundle / dsh.client 声明
├── cordis.patch.yml      # 宿主插件挂载层
├── lib/
│   ├── index.js          # cordis 宿主插件（name / inject / apply）
│   ├── api.js            # /skill-hub/api 接口与同源围栏
│   ├── service.js        # 扫描 / 安装 / 更新 / 注册编排
│   ├── skills.js         # SKILL.md 解析、发现、复制、运行时注册
│   ├── github.js         # GitHub 解析与 tarball 拉取
│   └── store.js          # 配置与状态持久化
├── client/client.js      # 设置页「技能仓库」面板
└── test/                 # smoke / service / api / host / client
```
