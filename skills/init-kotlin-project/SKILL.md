---
name: init-kotlin-project
description: Initialize or reset a Youzan/Qingyan Kotlin Spring Boot Maven project using the local QY style. Use when the user asks to initialize a Kotlin project, remove api/biz/dal/deploy submodules, configure root and web POMs, add .ENV OpenSDK/MySQL/Redis settings, add MyBatis Generator config, create Kotlin package directories, or create docs/PRDs docs/RFCs docs/Plans vibe-coding directories.
---

# Init Kotlin Project

## Workflow

1. Confirm the project root and project name. Default to the current working directory name or the root POM artifactId.
2. Collect these values in order:
   - application `clientId`
   - application `clientSecret`
   - local MySQL username
   - local MySQL password
   - QY extension package version
3. Run `scripts/init_kotlin_project.py` from the repository root.
4. Do static checks only unless the user explicitly asks to build:
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
  --mysql-password '<password>' \
  --qy-extension-version '<version>'
```

If any required value is omitted, the script prompts interactively in the required order.

Useful options:

- `--project-name <name>`: override the project name used for package paths and database name.
- `--web-module <module>`: override the web module directory. Defaults to `<project-name>-web`, or the single existing `*-web` module.
- `--dry-run`: print planned changes without writing files.

## What The Script Does

- Delete old split modules: `<project>-api`, `<project>-biz`, `<project>-dal`, `<project>-deploy`.
- Rewrite the root POM for a single web module and Kotlin Maven plugin configuration.
- Rewrite the web POM with QY extension, Youzan, Swagger, MyBatis Generator, Redisson, Hutool, and Aladdin plugin dependencies.
- Remove `src/main/java/com/youzan/cloud/<project>/web`.
- Create `src/main/kotlin/com/youzan/cloud/<project>`.
- Update root `.ENV` with OpenSDK, escrow token, Redis, idempotent, MySQL, MyBatis log, OAuth, and Swagger settings.
- Add `src/main/resources/generatorConfig.xml`.
- Create `docs/PRDs`, `docs/RFCs`, and `docs/Plans`.

## Notes

- The script intentionally keeps `artifactId`, `groupId`, and `version` from existing POMs when possible.
- The database name defaults to the project name.
- It never runs Maven or compilation.
