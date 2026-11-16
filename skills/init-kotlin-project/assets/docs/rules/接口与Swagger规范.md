# 接口与 Swagger 规范

适用 `${PROJECT_NAME}-web` 下所有 HTTP 接口与 DTO。Swagger 基于 **Springfox Swagger 2**（`io.swagger.annotations.*`），配置见 `${PROJECT_NAME}-web/src/main/kotlin/com/youzan/cloud/${PACKAGE_PATH}/common/config/SwaggerConfig.kt`。

## 1. 分组（按路径前缀，配置于 SwaggerConfig 各 Docket）

| 分组 | 路径前缀 | Controller 包 |
| --- | --- | --- |
| B端 | `/api/v1/admin/**` | `controller/admin` |
| C端 | `/api/v1/client/**` | `controller/client` |
| 开放端 | `/open/v1/**` | 由 `open` 相关控制器提供 |
| 通用 | `/api/v1/common/**` | `controller/common` |
| 定时任务端 | `/api/v1/scheduled/**` | `controller/task` |

## 2. 入出参命名

| 场景 | 后缀 | 示例 |
| --- | --- | --- |
| Admin / Client 端 API | `Params` / `Result` | `UserGetParams`、`UserGetResult` |
| Open 端与三方对接 | `Request` / `Response` | `UserGetRequest`、`UserGetResponse` |

DTO 统一放 `com.youzan.cloud.${PACKAGE_NAME}.model` 下，按端与业务模块组织（如 `model.admin.dealer`、`model.client.dealer`），**禁止放在 `controller` 包下**。

## 3. 注解要求

所有接口必须有完整的 swagger 注解，覆盖请求参数与响应参数。

| 注解 | 位置 | 要求 |
| --- | --- | --- |
| `@Api(tags = ["业务模块名"])` | Controller 类 | 必填，中文业务模块名 |
| `@ApiOperation(value, nickname, notes)` | 接口方法 | **三者必填**（见第 4 节） |
| `@ApiParam` | 方法参数 | query / path / header 参数必填；`HttpServletRequest`、Cookie 等注入参数标 `@ApiParam(hidden = true)` |
| `@ApiImplicitParam` / `@ApiImplicitParams` | 接口方法 | 数字型 path 变量需按字符串描述时，配合参数上的 `@ApiParam(hidden = true)` 使用，参考 `DealerController` |
| `@ApiModel` / `@ApiModelProperty` | Params / Result / Request / Response | 每个 DTO 类加 `@ApiModel`；每个字段加 `@ApiModelProperty(value = "...")`，说明取值范围、单位与格式 |

`notes` 需写明：鉴权与店铺来源、业务边界、副作用（覆盖式更新、状态流转、幂等约定等）。

## 4. nickname：必须显式指定且全局唯一

**这是硬性要求，不是风格偏好。**

`nickname` 是 Springfox 的 `operationId`，管理后台 SDK 由 `${PROJECT_NAME}-ui/vite-react-page/scripts/prepare-openapi-spec.mjs` 合并 spec 后经 `@hey-api/openapi-ts` 生成，直接以它作为生成方法名（如 `dealerPage`、`stationPage`、`benefitPage`）。

| 写法 | 生成的 SDK 方法名 | 结果 |
| --- | --- | --- |
| `nickname = "dealerPage"` | `dealerPage` | ✅ 语义明确，前端可稳定引用 |
| 不写 nickname | `pageUsingGet`、`createUsingPost`、`updateStatusUsingPost` | ❌ 缺业务模块前缀；且 `page`、`create`、`detail`、`update` 在多个 Controller 中重名 |
| nickname 重复 | `page`、`page2`（openapi-ts 0.99 实测静默追加数字） | ❌ 不报错、不告警，前端拿到的名字与预期不一致，排查成本高 |

### 命名规则

- camelCase，`业务模块 + 动作`，与 Java 方法名解耦：`dealerPage`、`dealerCreate`、`dealerEmployeeDelete`、`benefitLevelList`、`stationFieldSettingUpdate`。
- 动作词统一：`Page`（分页查询）、`List`（不分页列表）、`Detail`、`Create`、`Update`、`UpdateStatus`（状态流转）、`Delete`、`Save`（配置整体覆盖）、`Export`、`Callback`。
- 同一业务跨端、跨分组时加端前缀区分：C端 `clientMaterialImgUpload` 对应 B端 `materialImgUpload`。
- 禁止使用 `page`、`create`、`detail`、`update`、`updateStatus` 等脱离业务模块的通用词（等同于没写 nickname）。
- nickname 等同对外契约：已上线接口不得随意改名，确需改名必须同步更新前端调用点。

## 5. 自检（新增或修改接口后必须执行）

```shell
# 应无输出：nickname 重复
grep -rho 'nickname *= *"[^"]*"' ${PROJECT_NAME}-web/src/main/kotlin | sed 's/.*"\(.*\)"/\1/' | sort | uniq -d

# 应无输出：存在未写 nickname 的接口
grep -rn '@ApiOperation("' ${PROJECT_NAME}-web/src/main/kotlin
```

第二条命令只能覆盖 `@ApiOperation("...")` 单参写法；`@ApiOperation(value = ..., notes = ...)` 这种命名参数但漏写 `nickname` 的写法不会被查出，需人工确认：

```shell
grep -rn '@ApiOperation(value *=' ${PROJECT_NAME}-web/src/main/kotlin | grep -v nickname
```

## 6. 前端生成

- 管理后台：在 `${PROJECT_NAME}-ui/vite-react-page` 执行 `npm run openapi`，产出 `src/api/generated/`，生成文件不得手动修改。
- 消费端：在 `${PROJECT_NAME}-ui/cloud/client` 执行 `yarn openapi`，产出 `src/api/sdk.gen.js`，生成文件不得手动修改。
