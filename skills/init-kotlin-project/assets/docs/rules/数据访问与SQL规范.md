# 数据访问与 SQL 规范

适用 `${PROJECT_NAME}-web` 下 `dal` 层、Mapper（MyBatis 3.5.11 + MyBatis Dynamic SQL）与建表变更。

## 1. 建表字段类型

以下字段类型**禁止**在建表中使用：

`TINYBLOB`、`MEDIUMBLOB`、`BLOB`、`LONGBLOB`、`JSON`、`TINYTEXT`、`MEDIUMTEXT`、`TEXT`、`LONGTEXT`

长内容统一用 `VARCHAR` 存储（JSON 内容以 JSON 字符串保存），并设置明确的长度上限。

## 2. MyBatis Generator

配置文件：`${PROJECT_NAME}-web/src/main/resources/generatorConfig.xml`（生成 Kotlin model / mapper）。

- **禁止** 修改生成的mapper、UserRoleRelDynamicSqlSupport、MapperExtensions 文件，而是通过 MyBatis Generator更新

```shell
cd ${PROJECT_NAME}-web && mvn mybatis-generator:generate
```

> 该命令属于例外：仅当用户明确要求生成代码时执行，日常开发不要自行跑 mvn。

## 3. Dynamic SQL 书写规则

- **禁止** `selectMany`（Service 层禁止直接使用生成器底层的 `selectMany`，应使用 `select {}` DSL）。
- **禁止** `isInWhenPresent`。
- 使用 `where {}`、`and {}`，不使用 `where()`、`and()`。
- 名称相关条件筛选需支持 like 时，用 `ifBlank` 归一化空白：

```kotlin
and { UserRoleRelDynamicSqlSupport.UserRoleRel.name isLikeWhenPresent name?.ifBlank { null }?.let { "%it%" } }
```

- 条件不为空才拼接时，用 `isEqualToWhenPresent` 等 `...WhenPresent` 系列，**不要**在 lambda 里写 `if`：

```kotlin
// 错误：在 DSL lambda 内写 if
val roleIds = userRoleRelMapper.select {
  where { UserRoleRelDynamicSqlSupport.UserRoleRel.userId isEqualTo user.id!! }
  if (status != null) {
    and { UserRoleRelDynamicSqlSupport.UserRoleRel.status isEqualTo status!! }
  }
}

// 正确：用 WhenPresent 系列表达"存在才拼"
val roleIds = userRoleRelMapper.select {
  where { UserRoleRelDynamicSqlSupport.UserRoleRel.userId isEqualTo user.id!! }
  and { UserRoleRelDynamicSqlSupport.UserRoleRel.status isEqualToWhenPresent status }
  and { UserRoleRelDynamicSqlSupport.UserRoleRel.name isLikeWhenPresent name?.ifBlank { null }?.let { "%it%" } }
}
```

## 4. 自定义 SQL

- 自定义 SQL 时创建 `xxxMapperExt` 继承 `xxxMapper`，不要改动生成器产物。
- 现有工程中存在 `*MapperExt.kt` 与 `*MapperExtensions.kt` 两种命名（共 40+），**在所在模块内沿用相邻文件的既有写法**，不要混用。

## 5. SQL 函数与联表

- 除 `IFNULL()`、`SUM()`、`COUNT()`、`CONCAT()` 外，减少 SQL 中的函数调用；使用时必须写明原因。
- 查询列表时非必要**禁用 join**：先取主表关键数据，再按关联键用 `in` 查询，最后在代码层聚合。

## 6. 索引与条件顺序

- `where {}` 内优先放区分度高、可命中索引的条件，`and {}` 内放可选筛选条件，便于阅读时区分必选与可选。

## 7. 数据库实体

数据库实体保留在 `dal.model` 包下，接口模型放 `model` 包，二者不得混用。
