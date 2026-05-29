# advance-with-ai

## Shell 脚本说明

### 一键脚本

安装：

```bash
bash install.sh
```

卸载：

```bash
bash uninstall.sh
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

