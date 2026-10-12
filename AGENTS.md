## 核心原则

撰写清晰的技术回复，并附带精准的代码示例。
尽可能利用 Kotlin 或 Java 的内置功能及 SDK，以最大限度地提升整体性能。
优先考虑代码的可读性和可维护性，了解作者的代码风格，并遵循作者的编码风格和实体命名规范。
使用具有描述性的变量和函数名称，并遵循命名约定（例如，函数和变量采用 camelCase 命名法）。

**整体理解**

在编写或优化代码时，始终对项目逻辑保持整体理解。
确保代码与项目的整体架构、设计模式和业务逻辑保持一致。
避免因局部优化而导致全局问题。
优化代码时，始终考虑其对整个项目的影响。
优先解决性能瓶颈、代码冗余和潜在风险，而非追求不必要的 “完美”。
优化后，不得降低代码的可读性、可维护性或可扩展性。

## 规则约束
-  若非用户说明，不要执行mvn命令、编译操作
-  遇到不确定或复杂问题、选择上的问题时，主动与开发人员沟通，而非自行决策，提供可能的选项供开发人员选择

## 编码规范
- 框架工具：优先使用 Spring MVC 的 @Controller（用于页面渲染）或 @RestController（用于返回 JSON/API 响应），并结合请求映射注解（例如，@GetMapping、@PostMapping）。

- 简单逻辑采用简化控制器：将单一请求处理逻辑（例如，“获取单个用户信息”“返回静态数据”）直接在控制器方法中实现。避免过度分层。

- 不要过度封装方法，除非业务功能一致可复用，优先使用已有的SDK方法：如Date类型解析与格式化使用 hutool `DateUtil` 工具类

- 不要使用兜底编码思想，如Kotlin `coerceAtLeast` 等语法，而是进行业务考虑

- 基于 JSR - 380 规范的验证：使用注解（例如，@NotNull、@NotBlank）定义验证规则，并通过 Spring 的 @Valid 触发验证。避免在控制器中编写手动验证逻辑。

- 当入参已通过 JSR-380 注解完成基础校验（非空、范围、长度、枚举等）时，Service 层禁止重复做同类参数校验；Service 层仅保留业务校验（如存在性、唯一性、权限、并发冲突、状态机约束）

- 查询API（列表查询等）入参若出现类型、状态相关条件优先考虑使用枚举类型接收，减少service层冗余的类型校验

- private方法必须添加方法描述，代码行中核心的方法调用应添加简要明了的注释描述 `// 业务约定....`，但不要过度添加，比如一行一个注释

- Kotlin 服务统一使用 import com.qingyan.extension.extension.logger 获取 logger，在提交、状态流转、外部调用和失败等关键节点记录
- 关键业务需要增加日志的打印，合理使用`log.ingo`、`log.error`、`log.warn` 输出关键内容：`log.info("订单支付,请求3方,orderNo:{}\nreqesut:{}",data.orderNo,data.toJSONString())`

- 关于方法的命名规范：

  普通方法遵循主谓宾

  检查类方法使用`check...()`

  校验类使用`validate...()`

  业务核心方法使用`...core()`
  
  API出入参DTO的创建使用 `build...()`

### 接口规范

- 所有接口都必须有对应的swagger注解，包括请求参数、响应参数
- 接口入参出参数格式：
  Admin/Client端 API使用 Params/Result 后缀命名，例如，`UserGetParams`、`UserGetResult`;
  Open 或对接三方外部API使用 Request/Response 后缀命名，例如，`UserGetRequest`、`UserGetResponse`;

### Kotlin语法

- 灵活使用 `.apply`、`.run`、`.let`、`.also` 语法糖等其他函数
- 当 if else 中业务代码只有一行时，可以省略`{}`

### 数据模型（pojo/model）持久化实现规范

MyBatis Generator 配置文件为 {项目名称}-web/src/main/resources/generatorConfig.xml。
MyBatis Generator 代码生成（生成 Kotlin model/mapper，需在 {项目名称}-web 目录）
```shell
cd {项目名称}-web && mvn mybatis-generator:generate
```

### 动态SQL使用

- 禁止使用 selectMany
- 禁止使用 isInWhenPresent
- 使用 `where{}`、`and{}` 而非 `where()`、`and()`
- 名称相关条件筛选需要支持like 使用 `name?.ifBlank{ null }?.let{ "%it%" }`
- 自定义SQL时创建xxxMapperExt继承xxxMapper使用
- 除 `IFNULL()`、`SUM()`、`COUNT()`、`CONCAT()` 外，减少SQL中的函数方法，用时需要进行原因描述
- 查询列表时非必要禁止使用join查询，而是先获取到列表关键数据在代码层面通过关联键进行in查询后再聚合

```kotlin
val refunds = refundMapper.select {
    where { RefundDynamicSqlSupport.Refund.tid isEqualTo orderNo }
    and { RefundDynamicSqlSupport.Refund.status isNotEqualTo ISVRefundStatus.PRE.name }
  and { RefundDynamicSqlSupport.Refund.flag.isNull() }
}

// 错误案例
val roleIds = userRoleRelMapper.select {
  where { UserRoleRelDynamicSqlSupport.UserRoleRel.userId isEqualTo user.id!! }
  if(status != null){
    and { UserRoleRelDynamicSqlSupport.UserRoleRel.status isEqualTo status!! }
  }
}

// 正确使用
val roleIds = userRoleRelMapper.select {
  where { UserRoleRelDynamicSqlSupport.UserRoleRel.userId isEqualTo user.id!! }
  and { UserRoleRelDynamicSqlSupport.UserRoleRel.status isEqualToWhenPresent status }
  and { UserRoleRelDynamicSqlSupport.UserRoleRel.name isLikeWhenPresent name?.ifBlank{ null }?.let{ "%it%" } }
}

```

## 前端

### 开发前必读
开发前需要先阅读 docs/前端开发文档.md，并按照其中的开放框架、页面配置、组件使用和代码规范执行。涉及具体开放场景、API、插槽或多端组件时，还需要通过https://doc.youzanyun.com/llms.txt继续查阅该文档要求的对应资料。

### 项目概览
- 本项目是有赞消费者端定制项目，使用 Vue 与 Tee 多端框架，支持 H5 和微信小程序。
- src/app.js 是应用级定制入口，src/app.json 是应用级配置入口。
- src/api/sdk.gen.js 存放接口请求与生成的 SDK 代码。
- src/components/ 存放可复用的自定义表单、富文本等组件。
- src/utils/ 存放通用工具、生命周期钩子和状态管理代码。
- 消费端开发目录 {项目名称}-ui/cloud/client (开发消费端前注意阅读 cloud-client 目录下的 README.md 文件，了解项目架构) 
- 有赞店铺后台页面开发目录 {项目名称}-ui/vite-admin-page 供应商独立后台页面开发目录 {项目名称}-ui/vite-supplier-page

### 常用命令
- `yarn openapi`：根据配置生成 API 类型与 SDK 代码。

### 修改约定
- 遵循现有 JavaScript、Vue、SCSS 和 JSON 的代码风格，优先复用已有组件与工具。
- 修改页面、应用配置或开放能力前，先确认 docs/前端开发文档.md 中对应的页面 key、配置格式、平台支持和 API 约束。
- 完成修改后，针对变更范围运行合适的构建、检查或测试命令。

### 前后端并行开发约定

- 消费端 API 非特殊情况不得手写。后端先确定接口契约并提供 Swagger，前端使用 `npm run openapi` 生成 src/api/sdk.gen.js 及类型文件后再对接，不直接编辑生成文件.
- 并行开发时先通过前后端约定字段、路径、错误码和状态流转，页面可以先写逻辑和 mock 数据，但不要单独创建消费端 API 文件； 如确有特殊 API 不能通过 OpenAPI 生成，必须先向用户说明原因并确认方案。

## 最终目标

通过标准化的工作方法和整体思维，协助开发人员高效完成项目，同时确保代码质量高、逻辑清晰且易于维护。（若非用户指定语言始终以中文回应。）