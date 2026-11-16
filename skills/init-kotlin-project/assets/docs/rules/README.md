# 分层规则索引

本目录存放按端、按能力的**强制规则**。根 `AGENTS.md` 只保留仓库级概述、结构、硬规则与原则，细则全部下沉到这里，避免每次会话都全量注入。

## 加载约定（重要）

本目录**不会被 AI Agent 自动注入**：DSH 只自动加载 `AGENTS.md` / `CLAUDE.md` 及其 `.local` 覆盖层。因此：

1. 根 `AGENTS.md` 明确要求：动某端代码前先读对应的本目录文件。
2. 读一次后内容进入会话历史，不必重复读。
3. 新增规则文件必须在本表登记，否则等于不存在。

## 文件清单

| 文件 | 适用场景 | 何时必读 |
| --- | --- | --- |
| [后端通用编码规范.md](后端通用编码规范.md) | `${PROJECT_NAME}-web` 后端分层、命名、注释、日志、Kotlin 语法 | 修改任何后端 `.kt` / `.java` 代码前 |
| [接口与Swagger规范.md](接口与Swagger规范.md) | Controller、DTO 命名、Swagger / Springfox 注解与 `nickname` 规约 | 新增或修改任何 HTTP 接口、DTO 前 |
| [数据访问与SQL规范.md](数据访问与SQL规范.md) | MyBatis Dynamic SQL、建表字段类型、MapperExt、查询聚合 | 涉及 Mapper、SQL、建表、MyBatis Generator 前 |
| [前端通用约定.md](前端通用约定.md) | 两个前端工程的边界、并行开发约定、禁止事项 | 修改任意前端代码前 |
| [消费端开发规则.md](消费端开发规则.md) | 消费端 `${PROJECT_NAME}-ui/cloud/client`（Vue + Tee，H5 / 小程序） | 修改消费端代码前，另需读 `docs/client/README.md` 及其分册 |
| [管理后台开发规则.md](管理后台开发规则.md) | 管理后台 `${PROJECT_NAME}-ui/vite-react-page`（React + Vite + TS） | 修改管理后台代码前，另需读 `docs/admin/README.md` 及其分册 |

## 维护规则

- 一处真相：工程细节写进 `docs/client/`、`docs/admin/` 分册（各自 `README`/入口页为索引），本目录只放「必须遵守的判定条件」，并链接到 docs。
- 本目录文件禁止写产品背景、方案叙事、历史沿革。
- 修改后检查根 `AGENTS.md` 的索引表是否仍指向存在的文件。
- 规则与代码冲突时以代码为准，并同步修订本目录，不要留下两套说法。
