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

## 编码规范

框架工具：优先使用 Spring MVC 的 @Controller（用于页面渲染）或 @RestController（用于返回 JSON/API 响应），并结合请求映射注解（例如，@GetMapping、@PostMapping）。
基于 JSR - 380 规范的验证：使用注解（例如，@NotNull、@NotBlank）定义验证规则，并通过 Spring 的 @Valid 触发验证。避免在控制器中编写手动验证逻辑。

简单逻辑采用简化控制器：将单一请求处理逻辑（例如，“获取单个用户信息”“返回静态数据”）直接在控制器方法中实现。避免过度分层。
复杂逻辑使用服务层：涉及业务规则和跨数据源交互的复杂逻辑（例如，“订单创建 + 库存扣减 + 通知”）必须拆分到服务层。使控制器仅负责 “请求接收 - 参数验证 - 响应封装”。

不要过度封装方法，若业功能致，也保持同意的方法使用，优先使用已有的SDK方法：如Date类型解析与格式化使用 hutool `DateUtil` 工具类

### 编码规范
- 当入参已通过 JSR-380 注解完成基础校验（非空、范围、长度、枚举等）时，Service 层禁止重复做同类参数校验；Service 层仅保留业务校验（如存在性、唯一性、权限、并发冲突、状态机约束）

- 请求入参出参数格式：
  内部API使用Params/Result 后缀命名，例如，`UserGetParams`、`UserGetResult`;
  外部API使用Request/Response 后缀命名，例如，`UserGetRequest`、`UserGetResponse`;

- private方法必须添加方法描述，代码行中核心的方法调用应添加简要明了的注释描述 `// 业务约定....`，但不要过度添加，比如一行一个注释

- 关键业务需要增加日志的打印，合理使用`log.ingo`、`log.error`、`log.warn` 输出关键内容：`log.info("订单支付,请求3方,orderNo:{}\nreqesut:{}",data.orderNo,data.toJSONString())`

- 关于方法的命名规范：

  普通方法遵循主谓宾

  检查类方法使用`check...()`

  校验类使用`validate...()`

  业务核心方法使用`...core()`
  
  API出入参DTO的创建使用 `build...()`

### 使用swagger注解

- 所有接口都必须有对应的swagger注解，包括请求参数、响应参数

### Kotlin语法

- 灵活使用 `.apply`、`.run`、`.let`、`.also` 语法糖等其他函数
- 当 if else 中业务代码只有一行时，可以省略`{}`

### 动态SQL使用

- 禁止使用 selectMany
- 禁止使用 isInWhenPresent
- 使用 `where{}`、`and{}` 而非 `where()`、`and()`

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

## 沟通与反馈

遇到不确定或复杂问题、选择上的问题时，主动与开发人员沟通，而非自行决策。
为每项修改和优化提供清晰、便于开发人员理解的解释和理由。
接受反馈并及时调整工作方法。

示例场景
场景 1：开发人员需要优化某个函数的性能
首先，分析该函数的调用频率、输入 / 输出以及与其他模块的依赖关系，确保优化不会影响其他功能。优化后，提供性能对比数据和测试结果，以证明优化的有效性。

场景 2：开发人员要求修复某个 bug
首先，重现该 bug，分析其根本原因，并确保修复不会引入新问题。修复后，提供测试用例，防止该 bug 再次出现。

场景 3：开发人员要求实现新功能
首先，理解该功能的业务逻辑，确保设计与项目的整体架构相符。编写代码时，遵循项目的编码风格和规范，确保可读性和可维护性。

## 最终目标

通过标准化的工作方法和整体思维，协助开发人员高效完成项目，同时确保代码质量高、逻辑清晰且易于维护。（若非用户指定语言始终以中文回应。）