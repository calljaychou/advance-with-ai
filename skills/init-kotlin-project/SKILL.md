---
name: init-kotlin-project
description: Initialize or reset a Youzan/Qingyan Kotlin Spring Boot Maven project using the local QY style. Use when the user asks to initialize a Kotlin project, remove api/biz/dal/deploy submodules, configure root and web POMs, add .ENV OpenSDK/MySQL/Redis/MyBatis settings, add MyBatis Generator config, create Kotlin package directories and common base files, and create a docs workspace containing the client, admin, and rules guides plus a root AGENTS.md.
---

# Init Kotlin Project

## Workflow

1. Confirm the project root and project name. Prefer `--project-name`, then the `PROJECT_NAME` environment variable, then the root POM artifactId or current working directory name.
2. Collect these values in order:
   - application `clientId`
   - application `clientSecret`
   - QY extension package version defaults to `0.1.0-SNAPSHOT`; collect it only when the developer wants to override the default
3. Run `scripts/init_kotlin_project.py` from the repository root.
4. The script creates the vibe coding workspace as part of standard initialization: `docs/client/`, `docs/admin/`, `docs/rules/`, and root `AGENTS.md`. Do not ask whether to create it.
5. Do static checks only unless the user explicitly asks to build:
   - `xmllint --noout pom.xml`
   - `xmllint --noout <web-module>/pom.xml`
   - `xmllint --noout <web-module>/src/main/resources/generatorConfig.xml`
   - `git diff --name-status`

Do not run Maven, compile, package, or MyBatis Generator unless the user explicitly asks.

## 执行提速约定（务必遵守）

- 项目根与项目名直接取当前工作目录和根 POM `artifactId`，不要扫描工作区或兄弟工程确认命名约定。`--project-name` 优先，其次读取环境变量 `PROJECT_NAME`。
- 包名由脚本自动从项目名转换：`-` 替换为 `.`，例如 `my-project` → `com.youzan.cloud.my.project`；需要强制指定时用 `--package-name`。
- 文档模板使用 `${PROJECT_NAME}`、`${PACKAGE_NAME}`、`${PACKAGE_PATH}`、`${PROJECT_CLASS_NAME}` 占位符，由脚本按当前项目渲染，禁止在模板中写死具体项目名。
- `all-open` 已指向 QY 扩展包注解 `com.qingyan.extension.annotation.AllOpen`，无需再生成项目内 `AllOpen.kt`。
- QY 扩展包版本默认 `0.1.0-SNAPSHOT`，MySQL/Redis 使用固定公司地址，不要就此反问用户。
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

If any required value is omitted, the script prompts interactively in the required order. The QY extension package version is optional and defaults to `0.1.0-SNAPSHOT`; pass `--qy-extension-version` only when the developer wants to override it.

Useful options:

- `--project-name <name>`: override the project name used for module names, database name, and the default package name. When omitted, `PROJECT_NAME` is used if set, otherwise the root POM artifactId.
- `--package-name <name>`: override the Kotlin package name. Defaults to the project name with `-` replaced by `.`.
- `--web-module <module>`: override the web module directory. Defaults to `<project-name>-web`, or the single existing `*-web` module.
- `--qy-extension-version <version>`: override the default QY extension package version `0.1.0-SNAPSHOT`.
- `--create-vibe-coding-workspace`: only backfill `docs/client/`, `docs/admin/`, `docs/rules/`, and root `AGENTS.md` without running full initialization. Standard initialization already creates them automatically.
- `--dry-run`: print planned changes without writing files.

## What The Script Does

- Delete old split modules: `<project>-api`, `<project>-biz`, `<project>-dal`, `<project>-deploy`.
- Rewrite the root POM for a single web module and Kotlin Maven plugin configuration.
- Rewrite the web POM with QY extension, Youzan, Swagger, MyBatis Generator, Redisson, Hutool, and Aladdin plugin dependencies.
- Remove `src/main/java/com/youzan/cloud/<package-path>/web`.
- Create `src/main/kotlin/com/youzan/cloud/<package-path>` package scaffolding: `common`, `controller`, `dal`, `model`, `service`, `thirdside`, and `youzanopen`. `<package-path>` 由项目名把 `-` 换成 `.` 再换成目录 `/` 得到，例如 `my-project` → `my/project`。
- Create common base files under `common`: extension helpers, result handler annotation, CORS, Env, global exception/response handlers, and Swagger config.
- Update root `.ENV` with OpenSDK, escrow token, Redis, idempotent, MySQL, MyBatis mapper/package/log, OAuth, and Swagger settings.
- Copy the bundled `mysql-connector-java-8.0.19.jar` to `src/main/resources`.
- Add `src/main/resources/generatorConfig.xml`, using the bundled resources jar as its `classPathEntry`.
- Add `**/src/main/resources/generatorConfig.xml` to the root `.gitignore`.
- Create the vibe coding workspace as part of standard initialization: `docs/client/`, `docs/admin/`, `docs/rules/`, and root `AGENTS.md`.

The script copies the bundled `assets/docs/` tree to `docs/`, rendering `${PROJECT_NAME}`, `${PACKAGE_NAME}`, `${PACKAGE_PATH}`, and `${PROJECT_CLASS_NAME}` from the current project. It creates root `AGENTS.md` from `assets/AGENTS.md` with the same variables. Existing docs and `AGENTS.md` are kept unchanged. Legacy root docs `前端开发文档.md`, `消费端开发文档.md`, and `管理后台开发文档.md` are removed when present.

## Notes

- The script intentionally keeps `artifactId`, `groupId`, and `version` from existing POMs when possible.
- The database name is derived from `--project-name`, for example `isho`.
- MySQL is fixed to `192.168.2.111:3306`, with username `root` and password `123456`.
- It never runs Maven or compilation.
- `assets/AGENTS.md` and `assets/docs/` are the single source of truth for generated project documentation; update the assets instead of hardcoding project names in the script.
