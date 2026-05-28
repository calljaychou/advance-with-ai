# advance-with-ai

## Shell 脚本说明

本仓库提供两套安装脚本：

- `install.sh`：根目录一键安装脚本，会自动检测已安装的 IDE，并安装到对应目录。
- `scripts/*.sh`：按指定工具安装或卸载，目前支持 `codex`、`claude`。

### 根目录一键脚本

执行安装：

```bash
bash install.sh
```

执行卸载：

```bash
bash install.sh uninstall
```

安装规则：

- workflows：扫描仓库内的 `.md` 文件，排除 `skills` 目录和 `README.md`，按文件名平铺复制到目标 workflows 目录。
- skills：扫描 `skills/*` 子目录，跳过 `shared`，按 skill 目录整体复制到目标 skills 目录。
- 复制前会覆盖同名文件或目录。
- 安装后会输出安装数量和安装目标。

卸载规则：

- workflows：只删除本仓库对应的同名 workflow 文件。
- skills：只删除本仓库对应的同名 skill 目录。
- 不会删除整个 IDE 配置目录。

### 指定工具脚本

安装 Codex：

```bash
bash scripts/install.sh codex
```

安装 Claude：

```bash
bash scripts/install.sh claude
```

同时安装 Codex 和 Claude：

```bash
bash scripts/install.sh codex,claude
```

卸载 Codex：

```bash
bash scripts/uninstall.sh codex
```

卸载 Claude：

```bash
bash scripts/uninstall.sh claude
```

同时卸载 Codex 和 Claude：

```bash
bash scripts/uninstall.sh codex,claude
```

指定工具脚本会对工具参数做标准化处理，支持中文逗号、英文逗号、大小写混用和空格，例如：

```bash
bash scripts/install.sh "Codex, Claude"
```

### Codex 与 Claude 安装路径

| 工具 | Workflows 目标目录 | Skills 目标目录 |
| --- | --- | --- |
| Codex | `~/.codex/prompts` | `~/.codex/skills` |
| Claude | `~/.claude/commands` | `~/.claude/skills` |

### 输出信息

脚本执行完成后会输出本次处理的数量和清单。例如：

```text
[advance-with-ai] 已安装 2 个 skills -> /Users/example/.codex/skills
[advance-with-ai]   - plantuml-expert
[advance-with-ai]   - spring-api-regression
[advance-with-ai] 已安装 4 个 workflows -> /Users/example/.codex/prompts
[advance-with-ai]   - code-reviewer.md
[advance-with-ai]   - requirements.md
[advance-with-ai]   - prd-design.md
[advance-with-ai]   - tech-spec-generator.md
```

卸载时会统计实际删除的目标数量。若目标文件或目录不存在，则不会计入已卸载数量。

### Dry Run

指定工具脚本支持通过 `DRY_RUN=1` 预览执行动作：

```bash
DRY_RUN=1 bash scripts/install.sh codex
DRY_RUN=1 bash scripts/uninstall.sh codex
```

Dry Run 不会修改本地文件，只输出将要执行的安装或卸载动作。

