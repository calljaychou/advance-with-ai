---
name: init-kotlin-project
description: Initialize or reset a Youzan/Qingyan Kotlin Spring Boot Maven project using the local QY style. Use when the user asks to initialize a Kotlin project, remove api/biz/dal/deploy submodules, configure root and web POMs, add .ENV OpenSDK/MySQL/Redis settings, add MyBatis Generator config, create Kotlin package directories and common base files, or optionally create docs/PRDs docs/RFCs docs/Plans and root AGENTS.md vibe-coding workspace.
---

# Init Kotlin Project

## Workflow

1. Confirm the project root and project name. Default to the current working directory name or the root POM artifactId.
2. Collect these values in order:
   - application `clientId`
   - application `clientSecret`
   - local MySQL username
   - local MySQL password
   - QY extension package version defaults to `0.0.8-SNAPSHOT`; collect it only when the developer wants to override the default
3. Run `scripts/init_kotlin_project.py` from the repository root.
4. After the script finishes, ask the developer whether to add the vibe coding workspace. Do not create it by default. If they choose yes, run:

```bash
python3 ~/.codex/skills/init-kotlin-project/scripts/init_kotlin_project.py \
  --project-root . \
  --create-vibe-coding-workspace
```

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
  --client-secret '<clientSecret>' \
  --mysql-username root \
  --mysql-password '<password>'
```

If any required value is omitted, the script prompts interactively in the required order. The QY extension package version is optional and defaults to `0.0.8-SNAPSHOT`; pass `--qy-extension-version` only when the developer wants to override it.

Useful options:

- `--project-name <name>`: override the project name used for package paths and database name.
- `--web-module <module>`: override the web module directory. Defaults to `<project-name>-web`, or the single existing `*-web` module.
- `--qy-extension-version <version>`: override the default QY extension package version `0.0.8-SNAPSHOT`.
- `--create-vibe-coding-workspace`: only create `docs/PRDs`, `docs/RFCs`, `docs/Plans`, and root `AGENTS.md`.
- `--dry-run`: print planned changes without writing files.

## What The Script Does

- Delete old split modules: `<project>-api`, `<project>-biz`, `<project>-dal`, `<project>-deploy`.
- Rewrite the root POM for a single web module and Kotlin Maven plugin configuration.
- Rewrite the web POM with QY extension, Youzan, Swagger, MyBatis Generator, Redisson, Hutool, and Aladdin plugin dependencies.
- Remove `src/main/java/com/youzan/cloud/<project>/web`.
- Create `src/main/kotlin/com/youzan/cloud/<project>` package scaffolding: `common`, `controller`, `dal`, `model`, `service`, `thirdside`, and `youzanopen`.
- Create common base files under `common`: extension helpers, result handler annotation, CORS, Env, global exception/response handlers, and Swagger config.
- Update root `.ENV` with OpenSDK, escrow token, Redis, idempotent, MySQL, MyBatis log, OAuth, and Swagger settings.
- Add `src/main/resources/generatorConfig.xml`.
- Does not create the vibe coding workspace or root `AGENTS.md` by default.

When creating the vibe coding workspace, the script creates `docs/PRDs`, `docs/RFCs`, `docs/Plans`, and root `AGENTS.md`. The generated `AGENTS.md` includes the project guidance and backend structure overview, with project name and web module rendered from the current project. Existing `AGENTS.md` files are kept unchanged.

## Notes

- The script intentionally keeps `artifactId`, `groupId`, and `version` from existing POMs when possible.
- The database name defaults to the project name.
- It never runs Maven or compilation.
