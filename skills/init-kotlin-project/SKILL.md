---
name: init-kotlin-project
description: Initialize or reset a Youzan/Qingyan Kotlin Spring Boot Maven project using the local QY style. Use when the user asks to initialize a Kotlin project, remove api/biz/dal/deploy submodules, configure root and web POMs, add .ENV OpenSDK/MySQL/Redis settings, add MyBatis Generator config, create Kotlin package directories and common base files, and create a docs workspace containing the consumer and admin development guides plus a root AGENTS.md.
---

# Init Kotlin Project

## Workflow

1. Confirm the project root and project name. Default to the current working directory name or the root POM artifactId.
2. Collect these values in order:
   - application `clientId`
   - application `clientSecret`
   - QY extension package version defaults to `0.0.9-SNAPSHOT`; collect it only when the developer wants to override the default
3. Run `scripts/init_kotlin_project.py` from the repository root.
4. The script creates the vibe coding workspace as part of standard initialization: `docs/消费端开发文档.md`, `docs/管理后台开发文档.md`, and root `AGENTS.md`. Do not ask whether to create it.
5. Do static checks only unless the user explicitly asks to build:
   - `xmllint --noout pom.xml`
   - `xmllint --noout <web-module>/pom.xml`
   - `xmllint --noout <web-module>/src/main/resources/generatorConfig.xml`
   - `git diff --name-status`

Do not run Maven, compile, package, or MyBatis Generator unless the user explicitly asks.

## 执行提速约定（务必遵守）

- 项目根与项目名直接取当前工作目录和根 POM `artifactId`，不要扫描工作区或兄弟工程确认命名约定。
- 包名由脚本自动从项目名转换：`-` 替换为 `.`，例如 `yf-brp` → `com.youzan.cloud.yf.brp`；需要强制指定时用 `--package-name`。
- `all-open` 已指向 QY 扩展包注解 `com.qingyan.extension.annotation.AllOpen`，无需再生成项目内 `AllOpen.kt`。
- QY 扩展包版本默认 `0.0.9-SNAPSHOT`，MySQL/Redis 使用固定公司地址，不要就此反问用户。
- 若用户未在对话中给出 `clientId`/`clientSecret`，一次性索要后作为命令行参数传入，避免脚本交互式逐项等待。
- 用户未要求预览时，直接执行一次正式脚本，不要先 `--dry-run` 再正式执行。
- 静态校验合并为一次命令执行，不要逐条单独跑。

## Script

Use the bundled script for the fixed initialization logic:

```bash
python3 ~/.codex/skills/init-kotlin-project/scripts/init_kotlin_project.py \
  --project-root . \
  --client-id '<clientId>' \
  --client-secret '<clientSecret>'
```

If any required value is omitted, the script prompts interactively in the required order. The QY extension package version is optional and defaults to `0.0.9-SNAPSHOT`; pass `--qy-extension-version` only when the developer wants to override it.

Useful options:

- `--project-name <name>`: override the project name used for module names and database name.
- `--package-name <name>`: override the Kotlin package name. Defaults to the project name with `-` replaced by `.`.
- `--web-module <module>`: override the web module directory. Defaults to `<project-name>-web`, or the single existing `*-web` module.
- `--qy-extension-version <version>`: override the default QY extension package version `0.0.9-SNAPSHOT`.
- `--create-vibe-coding-workspace`: only backfill `docs/消费端开发文档.md`, `docs/管理后台开发文档.md`, and root `AGENTS.md` without running full initialization. Standard initialization already creates them automatically.
- `--dry-run`: print planned changes without writing files.

## What The Script Does

- Delete old split modules: `<project>-api`, `<project>-biz`, `<project>-dal`, `<project>-deploy`.
- Rewrite the root POM for a single web module and Kotlin Maven plugin configuration.
- Rewrite the web POM with QY extension, Youzan, Swagger, MyBatis Generator, Redisson, Hutool, and Aladdin plugin dependencies.
- Remove `src/main/java/com/youzan/cloud/<package-path>/web`.
- Create `src/main/kotlin/com/youzan/cloud/<package-path>` package scaffolding: `common`, `controller`, `dal`, `model`, `service`, `thirdside`, and `youzanopen`. `<package-path>` 由项目名把 `-` 换成 `.` 再换成目录 `/` 得到，例如 `yf-brp` → `yf/brp`。
- Create common base files under `common`: extension helpers, result handler annotation, CORS, Env, global exception/response handlers, and Swagger config.
- Update root `.ENV` with OpenSDK, escrow token, Redis, idempotent, MySQL, MyBatis log, OAuth, and Swagger settings.
- Copy the bundled `mysql-connector-java-8.0.19.jar` to `src/main/resources`.
- Add `src/main/resources/generatorConfig.xml`, using the bundled resources jar as its `classPathEntry`.
- Add `**/src/main/resources/generatorConfig.xml` to the root `.gitignore`.
- Create the vibe coding workspace as part of standard initialization: `docs/消费端开发文档.md`, `docs/管理后台开发文档.md`, and root `AGENTS.md`.

The script copies the bundled consumer and admin development guides to `docs/消费端开发文档.md` and `docs/管理后台开发文档.md`, then creates root `AGENTS.md`. The generated `AGENTS.md` combines the QY project guidance, backend structure overview, core principles, development constraints, coding conventions, MyBatis/dynamic SQL rules, and frontend development conventions, with project name and web module rendered from the current project. Existing new guide files and `AGENTS.md` are kept unchanged, while the legacy `docs/前端开发文档.md` is removed when present.

## Notes

- The script intentionally keeps `artifactId`, `groupId`, and `version` from existing POMs when possible.
- The database name defaults to the project name.
- MySQL is fixed to `192.168.2.111:3306`, with username `root` and password `123456`.
- It never runs Maven or compilation.
