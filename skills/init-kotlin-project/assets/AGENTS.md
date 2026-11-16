# AGENTS

本文件用于指导 AI Agent 处理本仓库代码。始终用中文回复（用户另有指定语言时除外），给出精准、可运行的代码示例。

## 项目概述

- 后端 `${PROJECT_NAME}-web/`：Java 8 + Kotlin 1.8.0、Spring Boot、有赞云基座 `cloud-parent 1.1.3-RELEASE`、MyBatis 3.5.11、MySQL、Redisson 3.16.8
- 前端 `${PROJECT_NAME}-ui/`：两个**独立工程**，技术栈与命令互不通用
  - 消费端 `cloud/client`：Vue + Tee 多端框架，支持 H5 与微信小程序
  - 管理后台 `vite-react-page`：React 18 + Vite 5 + TypeScript + React Router + Ant Design

## 仓库结构

```plaintext
${PROJECT_NAME}-web/src/main/
├── java/com/youzan/cloud/${PACKAGE_PATH}/     # ${PROJECT_CLASS_NAME}Application 入口、有赞扩展点 Java 包装类
└── kotlin/com/youzan/cloud/${PACKAGE_PATH}/
    ├── controller/{admin,client,common,task}/   # REST 控制器（另有 CustomPageController）
    ├── model/{admin,client,common,task}/        # 接口模型，禁止放 controller 包
    ├── service/                                 # 业务逻辑层
    ├── dal/{mapper,model}/                      # MyBatis 映射与数据库实体
    ├── open/youzan/{extension,message,api}/     # 有赞扩展点 / 消息 / 开放 API 客户端
    ├── thirdside/                               # 非有赞的三方系统对接
    └── common/                                  # 通用工具与全局配置
${PROJECT_NAME}-ui/cloud/client/        # 消费端
${PROJECT_NAME}-ui/vite-react-page/     # 管理后台
docs/                          # 工程文档与分层规则
```

接口模型统一放 `com.youzan.cloud.${PACKAGE_NAME}.model.<端>.<业务模块>`（如 `model.admin.dealer`），数据库实体保留 `dal.model`。

## 分层规则索引（按需读取）

细则已按端与能力拆分到 `docs/rules/`，避免每次会话全量载入。**这些文件不会被自动注入，动对应范围代码前必须先读。**

| 范围 | 规则文件 | 何时必读 |
| --- | --- | --- |
| 后端通用 | [docs/rules/后端通用编码规范.md](docs/rules/后端通用编码规范.md) | 改任何后端 `.kt` / `.java` 前 |
| 接口与 Swagger | [docs/rules/接口与Swagger规范.md](docs/rules/接口与Swagger规范.md) | 新增/修改 HTTP 接口、DTO 前 |
| 数据访问与 SQL | [docs/rules/数据访问与SQL规范.md](docs/rules/数据访问与SQL规范.md) | 涉及 Mapper、SQL、建表前 |
| 前端通用 | [docs/rules/前端通用约定.md](docs/rules/前端通用约定.md) | 改任意前端代码前 |
| 消费端 | [docs/rules/消费端开发规则.md](docs/rules/消费端开发规则.md) + [docs/client/README.md](docs/client/README.md) | 改消费端前 |
| 管理后台 | [docs/rules/管理后台开发规则.md](docs/rules/管理后台开发规则.md) + [docs/admin/README.md](docs/admin/README.md) | 改管理后台前 |

规则文件总目录见 [docs/rules/README.md](docs/rules/README.md)。

## 硬性约束

1. **不执行 mvn 与编译**：除非用户明确说明，不运行 `mvn` 命令或编译操作。
2. **不自行决策**：遇到不确定、复杂或需要取舍的问题，主动与开发人员沟通并给出可选方案。
3. **有赞平台能力必须先查文档**：涉及服务端扩展点、消息、开放 API，或任何消费端开发时，必须在方案设计与编码前，按具体需求从 <https://doc.youzanyun.com/llms.txt> 检索对应能力文档，确认是否支持、接入方式、参数与数据结构、平台差异及限制。**不得凭已有经验或项目现状推断平台能力。**
4. **有赞能力放对包**：扩展点 → `open/youzan/extension`；事件消息 → `open/youzan/message`；开放 API 客户端 → `open/youzan/api`。`thirdside` 只放非有赞三方。
5. **数据边界**：严格遵守店铺授权、能力包权限与数据使用边界，仅在已授权店铺范围内处理数据，不做跨主体聚合与未授权共享。
6. **生成文件不得手改**：消费端 `src/api/sdk.gen.js`、管理后台 `src/api/generated/` 均为 OpenAPI 生成产物，只能通过各工程的 `openapi` 脚本（`yarn openapi` / `npm run openapi`）重新生成。
7. **前端不做多媒体适配**：两个前端工程都只按设计稿目标屏幕尺寸实现，不写媒体查询、不用响应式断点（`sm:` / `md:` / `lg:` 等）。
8. **命令在对应工程目录执行**：前端命令不得在仓库根目录或另一端工程中执行；后端命令在 `${PROJECT_NAME}-web` 下执行。消费端用 `yarn`（仓库为 `yarn.lock`），管理后台用 `npm`（仓库为 `package-lock.json`），不混用。

## 核心原则

- **整体理解优先**：改动前先理解项目架构、设计模式与业务逻辑，评估对全局的影响，避免局部优化引入全局问题。
- **遵循既有风格**：沿用作者的代码风格与命名规范，变量与函数用 camelCase 且具描述性；优先复用已有 SDK、工具与公共能力。
- **务实取舍**：优先解决性能瓶颈、代码冗余与潜在风险，不追求不必要的"完美"。
- **不降低质量底线**：任何优化都不得降低代码的可读性、可维护性或可扩展性。

## 最终目标

通过标准化的工作方法与整体思维，协助开发人员高效完成项目，确保代码质量高、逻辑清晰且易于维护。
