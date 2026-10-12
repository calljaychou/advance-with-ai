---
name: init-kotlin-project
description: Initialize or reset a Youzan/Qingyan Kotlin Spring Boot Maven project using the local QY style. Use when the user asks to initialize a Kotlin project, remove api/biz/dal/deploy submodules, configure root and web POMs, add .ENV OpenSDK/MySQL/Redis settings, add MyBatis Generator config, create Kotlin package directories and common base files, and create a docs workspace containing the frontend development guide plus a root AGENTS.md.
---

# Init Kotlin Project

## Workflow

1. Confirm the project root and project name. Default to the current working directory name or the root POM artifactId.
2. Collect these values in order:
   - application `clientId`
   - application `clientSecret`
   - QY extension package version defaults to `0.0.8-SNAPSHOT`; collect it only when the developer wants to override the default
3. Run `scripts/init_kotlin_project.py` from the repository root.
4. The script creates the vibe coding workspace as part of standard initialization: `docs/前端开发文档.md` and root `AGENTS.md`. Do not ask whether to create it.
5. Do static checks only unless the user explicitly asks to build:
   - `xmllint --noout pom.xml`
   - `xmllint --noout <web-module>/pom.xml`
   - `xmllint --noout <web-module>/src/main/resources/generatorConfig.xml`
   - `git diff --name-status`

Do not run Maven, compile, package, or MyBatis Generator unless the user explicitly asks.

## Script

Use the bundled script for the fixed initialization logic:

```bash
python3 ~/.codex/skills/init-kotlin-project/scripts/init_kotlin_project.py \
  --project-root . \
  --client-id '<clientId>' \
  --client-secret '<clientSecret>'
```

If any required value is omitted, the script prompts interactively in the required order. The QY extension package version is optional and defaults to `0.0.8-SNAPSHOT`; pass `--qy-extension-version` only when the developer wants to override it.

Useful options:

- `--project-name <name>`: override the project name used for package paths and database name.
- `--web-module <module>`: override the web module directory. Defaults to `<project-name>-web`, or the single existing `*-web` module.
- `--qy-extension-version <version>`: override the default QY extension package version `0.0.8-SNAPSHOT`.
- `--create-vibe-coding-workspace`: only backfill `docs/前端开发文档.md` and root `AGENTS.md` without running full initialization. Standard initialization already creates them automatically.
- `--dry-run`: print planned changes without writing files.

## What The Script Does

- Delete old split modules: `<project>-api`, `<project>-biz`, `<project>-dal`, `<project>-deploy`.
- Rewrite the root POM for a single web module and Kotlin Maven plugin configuration.
- Rewrite the web POM with QY extension, Youzan, Swagger, MyBatis Generator, Redisson, Hutool, and Aladdin plugin dependencies.
- Remove `src/main/java/com/youzan/cloud/<project>/web`.
- Create `src/main/kotlin/com/youzan/cloud/<project>` package scaffolding: `common`, `controller`, `dal`, `model`, `service`, `thirdside`, and `youzanopen`.
- Create common base files under `common`: extension helpers, result handler annotation, CORS, Env, global exception/response handlers, and Swagger config.
- Update root `.ENV` with OpenSDK, escrow token, Redis, idempotent, MySQL, MyBatis log, OAuth, and Swagger settings.
- Copy the bundled `mysql-connector-java-8.0.19.jar` to `src/main/resources`.
- Add `src/main/resources/generatorConfig.xml`, using the bundled resources jar as its `classPathEntry`.
- Add `**/src/main/resources/generatorConfig.xml` to the root `.gitignore`.
- Create the vibe coding workspace as part of standard initialization: `docs/前端开发文档.md` and root `AGENTS.md`.

The script copies the bundled frontend development guide to `docs/前端开发文档.md` and creates root `AGENTS.md`. The generated `AGENTS.md` combines the QY project guidance, backend structure overview, core principles, development constraints, coding conventions, MyBatis/dynamic SQL rules, and frontend development conventions, with project name and web module rendered from the current project. Existing `docs/前端开发文档.md` and `AGENTS.md` files are kept unchanged.

## Notes

- The script intentionally keeps `artifactId`, `groupId`, and `version` from existing POMs when possible.
- The database name defaults to the project name.
- MySQL is fixed to `192.168.2.111:3306`, with username `root` and password `123456`.
- It never runs Maven or compilation.
