#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


DEFAULT_QY_EXTENSION_VERSION = "0.0.9-SNAPSHOT"
MYSQL_HOST = "192.168.2.111"
MYSQL_PORT = 3306
MYSQL_USERNAME = "root"
MYSQL_PASSWORD = "123456"
MYSQL_CONNECTOR_JAR_NAME = "mysql-connector-java-8.0.19.jar"
GENERATOR_CONFIG_IGNORE_ENTRY = "**/src/main/resources/generatorConfig.xml"
CONSUMER_DEVELOPMENT_DOC_NAME = "消费端开发文档.md"
ADMIN_DEVELOPMENT_DOC_NAME = "管理后台开发文档.md"
LEGACY_FRONTEND_DEVELOPMENT_DOC_NAME = "前端开发文档.md"
SKILL_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
CONSUMER_DEVELOPMENT_DOC = SKILL_ASSETS_DIR / CONSUMER_DEVELOPMENT_DOC_NAME
ADMIN_DEVELOPMENT_DOC = SKILL_ASSETS_DIR / ADMIN_DEVELOPMENT_DOC_NAME
MYSQL_CONNECTOR_JAR = SKILL_ASSETS_DIR / MYSQL_CONNECTOR_JAR_NAME


AGENTS_TEMPLATE = r"""# AGENTS
本文件用于指导 AI Agent 处理当前代码仓库内的项目代码。

## 有赞云定制有容器开发
有赞云定制开发面向有技术能力的商家或服务商，围绕店铺、商品、订单、会员、营销等业务场景，通过开放 API、消息和扩展点，把有赞
店铺与商家自有系统打通，承载个性化商城页面、后端业务流程和行业解决方案。项目通常分为无容器和有容器两类：有容器可在有赞云 PaaS 
环境中开发自用型定制能力，如定制 H5、小程序页面和业务流程。开发过程中必须严格遵守店铺授权、能力包权限和数据使用边界，
仅在已授权店铺范围内处理数据，不做跨主体聚合或未经授权的数据共享；自用型有容器应用按有赞云接入流程创建，通常需要对应的大客技术套餐和平台授权。


## 项目概述

**技术栈**：
- 后端：Java 8 + Kotlin 1.8.0、Spring Boot、有赞云基座（cloud-parent 1.1.3-RELEASE）
- 数据库：MySQL，持久层框架 MyBatis 3.5.11
- 缓存：Redis，客户端 Redisson 3.16.8
- 前端：React 18 + Vite 5 + TypeScript（后台管理主面板）、Zent UI（商家云应用）、消费者端 Vue 与 Tee 多端框架（H5、微信小程序）

## 整体架构说明

### 后端目录结构

后端为 Java + Kotlin 混合开发 Spring Boot 应用：

```plaintext
__WEB_MODULE__/src/main/
├── java/                                     # Java 入口类 & 有赞扩展包装层
│   └── com/youzan/cloud/__PACKAGE_PATH__/
│       ├── __PROJECT_CLASS_NAME__Application.java               # Spring Boot 程序启动入口
│       └── open/youzan/extension/            # 有赞扩展点实现包装类
└── kotlin/                                   # Kotlin 源码（核心业务逻辑层）
    └── com/youzan/cloud/__PACKAGE_PATH__/
        ├── controller/                       # REST 接口控制器
        │   ├── admin/                        # 商家后台管理接口
        │   ├── client/                       # C端用户访问接口
        │   ├── open/                         # 对外开放接口
        │   ├── script/                       # 脚本执行接口
        │   ├── common/                       # 通用接口
        │   └── task/                         # 定时任务管控接口
        ├── service/                          # 业务逻辑层
        ├── dal/                              # 数据访问层
        │   ├── mapper/                       # MyBatis 数据库映射
        │   └── model/                        # 数据库实体模型
        ├── youzanopen/                       # 有赞开放能力对接模块
        │   ├── extension/                    # 有赞平台扩展逻辑实现
        │   ├── message/                      # 有赞平台事件消息处理器
        │   └── api/                          # 有赞开放API调用客户端
        ├── thirdside/                        # 三方系统能力对接模块
        └── common/                           # 通用工具类、全局配置
```

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
-  涉及服务端有赞扩展点、消息、开放 API 等平台能力，或任何消费端开发时，必须在方案设计和编码前，根据具体需求先从 https://doc.youzanyun.com/llms.txt 检索并查阅对应的有赞云能力文档，确认能力是否支持、接入方式、参数与数据结构、平台差异及使用限制；不得仅凭已有经验或项目现状推断平台能力

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

MyBatis Generator 配置文件为 __WEB_MODULE__/src/main/resources/generatorConfig.xml。
MyBatis Generator 代码生成（生成 Kotlin model/mapper，需在 __WEB_MODULE__ 目录）
```shell
cd __WEB_MODULE__ && mvn mybatis-generator:generate
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

### 工程边界与必读文档

前端代码分为消费端与管理后台两个独立工程。开始开发前必须先确认目标端，不得混用两个工程的技术栈、目录结构、组件、API 生成文件或运行命令。

| 类型     | 开发目录                    | 技术栈                                                | 必读文档                   |
| -------- | --------------------------- | ----------------------------------------------------- | -------------------------- |
| 消费端   | `__PROJECT_NAME__-ui/cloud/client`    | Vue + Tee 多端框架，支持 H5 和微信小程序              | `docs/消费端开发文档.md`   |
| 管理后台 | `__PROJECT_NAME__-ui/vite-react-page` | React + Vite + TypeScript + React Router + Ant Design | `docs/管理后台开发文档.md` |

- 修改代码前必须先阅读对应端的开发文档，再结合现有代码确认实现方式。
- 涉及消费端开放页面、开放 API、开放插槽、开放组件或多端组件时，还必须通过 https://doc.youzanyun.com/llms.txt 查阅对应的有赞云资料。
- 所有前端命令必须在对应工程目录中执行，不要在仓库根目录或另一端工程中执行。
- 完成修改后，根据变更范围运行对应工程已有的 TypeScript、ESLint、Prettier、测试或构建检查，不为检查额外引入依赖。

### 消费端开发

#### 工程入口与目录职责

- 开发目录：`__PROJECT_NAME__-ui/cloud/client`。
- 必读文档：`docs/消费端开发文档.md`。
- `src/app.js`：应用级定制入口，负责通过 `extendApp` 注册应用生命周期和公共能力。
- `src/app.json`：应用级配置入口，负责配置开放页面、插槽和自定义页面等能力。
- `src/pages/`：消费端页面逻辑、配置和视图代码。
- `src/components/`：消费端可复用的 Vue/Tee 组件。
- `src/utils/`：消费端公共工具、生命周期辅助和状态管理代码。
- `src/api/sdk.gen.js`：通过 OpenAPI 生成的消费端 SDK，不得手动修改。

#### 开发与 API 约定

- 遵循现有 JavaScript、Vue、SCSS 和 JSON 风格，优先复用 Tee UI、现有组件与工具。
- 修改页面、应用配置或开放能力前，必须先从 `docs/消费端开发文档.md` 确认页面 key、配置格式、平台支持范围及 API 约束。
- 同时考虑 H5 与微信小程序兼容性，不得仅按浏览器 DOM 或单一平台行为实现。
- 消费端 API 非特殊情况不得手写。后端提供 Swagger/OpenAPI 后，在消费端工程中执行 `npm run openapi` 生成 `src/api/sdk.gen.js`。
- 如确有无法通过 OpenAPI 生成的特殊 API，必须先说明原因并确认方案，再修改 `src/api/index.js` 等手动接口文件。

#### 常用命令

- `npm run dev`：启动 H5 开发环境。
- `npm run dev:weapp`：启动微信小程序开发环境。
- `npm run openapi`：生成消费端 API SDK。
- `npm run build`：构建消费端工程，仅在任务需要构建验证时执行。

### 管理后台开发

#### 工程入口与目录职责

- 开发目录：`__PROJECT_NAME__-ui/vite-react-page`。
- 必读文档：`docs/管理后台开发文档.md`。
- `src/main.tsx`：默认管理后台应用挂载入口。
- `src/pages/`：管理后台页面及独立页面构建入口。
- `src/components/`：跨页面复用的公共 React 组件，新增页面前必须优先检查和复用。
- `src/hooks/`：请求、列表、弹窗和事件等公共 Hook，禁止在页面中重复实现已有能力。
- `src/router/`：默认应用路由、路由工具和路由公共组件。
- `src/api/generated/`：通过 OpenAPI 生成的管理后台 SDK，不得手动修改。
- `src/api/config.ts`：统一请求实例、拦截器和生成 SDK 的运行时配置。

#### 页面、组件与样式约定

- 页面按需拆分为 `App.tsx`、`components/`、`hooks/`、`utils.ts`、`constants.ts`、`types.ts` 和 `styles.ts`，不得把业务组件、工具、类型和样式全部堆积在 `App.tsx`。
- 一个组件文件只定义一个 React 组件；可独立命名、接收独立 Props 或维护独立状态的子组件必须拆分为单独文件。
- 优先使用 Tailwind CSS 实现布局和常规样式；复杂选择器、动态主题或第三方组件覆盖再使用 styled-components。
- 不同页面、不同组件的 styled-components 必须放入各自独立的样式文件，不得集中到单个页面级或全局样式文件。
- 开发新能力前依次检查 `src/components/`、`src/hooks/`、`src/utils/`、`src/types/` 和 `src/api/`，能够复用或小范围扩展时不得重复实现。

#### 独立页面与路由约定

`__PROJECT_NAME__-ui/vite-react-page/vite.config.ts` 使用 `MultiPageAutoPlugin`（`vite-plugin-multipage-auto`）自动发现多页面入口：

- `__PROJECT_NAME__-ui/vite-react-page/src/pages/` 下的页面目录如果存在 `main.tsx`，该目录会被识别并打包为一个独立页面。
- 新增独立页面时，必须在 `src/pages/<页面目录>/main.tsx` 中配置 React 挂载入口，并按现有页面结构引入该独立页面的 Router、全局样式及必要的 Provider。
- 如果该独立页面还包含详情页、编辑页或其他关联页面，应通过该独立页面的 `router` 配置统一引入，优先使用路由懒加载；不要为这些关联页面分别添加 `main.tsx`。
- 一个独立页面目录只保留一个 `main.tsx` 构建入口，其关联页面由 Router 组织，最终将该入口打包为一个单页应用（SPA）。
- 可参考 `src/pages/list/main.tsx` 与 `src/pages/list/router/index.tsx` 的目录结构和配置方式。

推荐目录结构：

```plaintext
src/pages/<页面目录>/
├── main.tsx                 # MultiPageAutoPlugin 识别的独立构建入口
├── App.tsx                  # 入口页面组件
├── router/
│   └── index.tsx            # 该单页应用的路由配置
└── <关联页面>/              # 详情、编辑等路由页面，不单独添加 main.tsx
```

#### API 与常用命令

- 后端提供 Swagger/OpenAPI 后，在管理后台工程中执行 `npm run openapi` 生成 `src/api/generated/`。
- 页面应复用 `src/api/config.ts` 的统一请求配置，不得绕开拦截器重复创建请求实例。
- `npm run dev`：启动管理后台开发环境。
- `npm run dev:scan`：启动带 React Scan 的开发环境。
- `npm run openapi`：生成管理后台 API SDK。
- `npm run build`：构建管理后台工程，仅在任务需要构建验证时执行。

### 前后端并行开发约定

- 前后端并行开发前先约定接口路径、请求方法、字段、分页结构、错误码和状态流转，再分别实现。
- 页面可以先实现交互逻辑并使用 Mock 数据，但不得因此创建一套绕开 OpenAPI 的临时 API 层。
- 消费端生成文件是 `__PROJECT_NAME__-ui/cloud/client/src/api/sdk.gen.js`，管理后台生成目录是 `__PROJECT_NAME__-ui/vite-react-page/src/api/generated/`；两者均不得手动编辑。
- 如接口暂时无法生成，先保留页面逻辑和 Mock，或说明原因并确认临时方案，不得自行固化未经确认的接口契约。

## 最终目标

通过标准化的工作方法和整体思维，协助开发人员高效完成项目，同时确保代码质量高、逻辑清晰且易于维护。（若非用户指定语言始终以中文回应。）
"""


PROJECT_PACKAGE_DIRS = (
    "common",
    "common/annotation",
    "common/config",
    "controller",
    "dal",
    "dal/mapper",
    "dal/model",
    "model",
    "service",
    "thirdside",
    "youzanopen",
    "youzanopen/api",
    "youzanopen/extension",
    "youzanopen/message",
)


COMMON_FILE_TEMPLATES = {
    "common/Extensions.kt": """package __PACKAGE__.common

import cn.hutool.core.util.ZipUtil
import com.youzan.cloud.metadata.common.OutParam
import java.nio.charset.StandardCharsets
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * OutParam 成功构造返回
 *
 * @param data 返回数据
 */
fun <T> OutParam<T>.success(data: T) = apply {
    this.data = data
    this.success = true
    this.code = "200"
}

fun <T> OutParam<T>.fail(data: T, message: String, code: Int) = apply {
    this.success = false
    this.code = code.toString()
    this.message = message
    this.data = data.apply { }
}

/**
 * 序列化 压缩json
 */
fun serialize(json: String): String {
    val gzip = ZipUtil.gzip(json.toByteArray())
    return String(gzip, StandardCharsets.ISO_8859_1)
}

fun String.gzip() = serialize(this)

/**
 * 解压
 */
fun deserialize(serialized: String): String {
    val unzip = ZipUtil.unGzip(serialized.toByteArray(StandardCharsets.ISO_8859_1))
    return String(unzip)
}

fun String.unGzip() = deserialize(this)

/**
 * 火星坐标系 (GCJ-02) 与百度坐标系 (BD-09) 的转换算法 将 GCJ-02 坐标转换成 BD-09 坐标
 *
 * @param lat
 * @param lng
 * @return object
 */
fun gcjToBaidu(lng: Double, lat: Double): Pair<Double, Double> {
    val delta = (Math.PI * 3000.0) / 180.0
    val z = sqrt(lng * lng + lat * lat) + 0.00002 * sin(lat * delta)
    val theta = atan2(lat, lng) + 0.000003 * cos(lng * delta)
    val baiduLng = z * cos(theta) + 0.0065
    val baiduLat = z * sin(theta) + 0.006
    return Pair(baiduLng, baiduLat)
}

/**
 * * 火星坐标系 (GCJ-02) 与百度坐标系 (BD-09) 的转换算法 * * 将 BD-09 坐标转换成GCJ-02 坐标
 * @param [lng] lng
 * @param [lat] lat
 * @return [Pair<Double, Double>]
 */
fun baiduToGcj(lng: Double, lat: Double): Pair<Double, Double> {
    val delta = (Math.PI * 3000.0) / 180.0
    val x = lng - 0.0065
    val y = lat - 0.006
    val z = sqrt(x * x + y * y) - 0.00002 * sin(y * delta)
    val theta = atan2(y, x) - 0.000003 * cos(x * delta)
    val gcjLng = z * cos(theta)
    val gcjLat = z * sin(theta)
    return Pair(gcjLng, gcjLat)
}
""",
    "common/annotation/ExcludeResultHandler.kt": """package __PACKAGE__.common.annotation

/**
 * @author JayCHou <a href="calljaychou@qq.com">Email</a>
 */
annotation class ExcludeResultHandler
""",
    "common/config/CORSConfig.kt": """package __PACKAGE__.common.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.cors.CorsConfiguration
import org.springframework.web.cors.UrlBasedCorsConfigurationSource
import org.springframework.web.filter.CorsFilter

@Configuration
class CORSConfig {
    @Bean
    fun corsFilter(): CorsFilter {
        val config = CorsConfiguration()
        config.addAllowedOrigin("*")
        //是否发送Cookie信息
        config.allowCredentials = true
        //放行哪些原始域(请求方式)
        config.addAllowedMethod("*")
        //放行哪些原始域(头部信息)
        config.addAllowedHeader("*")

        //2.添加映射路径
        val configSource = UrlBasedCorsConfigurationSource()
        configSource.registerCorsConfiguration("/**", config)

        return CorsFilter(configSource)
    }
}
""",
    "common/config/Env.kt": """package __PACKAGE__.common.config

import org.springframework.stereotype.Component

@Component
class Env {



}
""",
    "common/config/GlobalControllerExceptionHandler.kt": """package __PACKAGE__.common.config

import cn.dev33.satoken.exception.SaTokenException
import cn.dev33.satoken.oauth2.exception.SaOAuth2Exception
import com.qingyan.extension.auth.manage.ManageAuthPermissionException
import com.qingyan.extension.exception.BizException
import com.qingyan.extension.exception.YzApiException
import com.qingyan.extension.extension.logger
import com.qingyan.extension.model.vo.ApiResult
import io.swagger.annotations.ApiOperation
import org.springframework.http.HttpStatus
import org.springframework.validation.BindException
import org.springframework.web.bind.MethodArgumentNotValidException
import org.springframework.web.bind.MissingServletRequestParameterException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.ResponseStatus
import org.springframework.web.bind.annotation.RestControllerAdvice
import org.springframework.web.method.HandlerMethod

@RestControllerAdvice
class GlobalControllerExceptionHandler {

    private val log = logger()

    private fun getExtLogInfo(handlerMethod: HandlerMethod): String {
        val apiOperation = handlerMethod.getMethodAnnotation(ApiOperation::class.java)
        val exiLogInfo = if (apiOperation != null) {
            "接口[${apiOperation.value}], "
        } else "接口[${handlerMethod.method.declaringClass.typeName}.${handlerMethod.method.name}], "
        return exiLogInfo
    }

    @ExceptionHandler(MethodArgumentNotValidException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun methodArgumentNotValidExceptionHandler(
        exception: MethodArgumentNotValidException,
        handlerMethod: HandlerMethod
    ): Any? {
        log.error("${getExtLogInfo(handlerMethod)}全局参数异常捕获", exception)
        return ApiResult.fail<Unit>(
            400,
            exception.bindingResult.fieldErrors.firstOrNull()?.defaultMessage ?: "参数异常"
        )
    }

    @ExceptionHandler(MissingServletRequestParameterException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun missingServletRequestParameterExceptionHandler(
        exception: MissingServletRequestParameterException,
        handlerMethod: HandlerMethod
    ): Any? {
        log.error("${getExtLogInfo(handlerMethod)}缺少必填参数", exception)
        return ApiResult.fail<Unit>(400, "缺少必填参数: ${exception.parameterName}")
    }

    @ExceptionHandler(BindException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun bindExceptionHandler(exception: BindException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}全局参数异常捕获", exception)
        return ApiResult.fail<Unit>(
            400,
            exception.bindingResult.fieldErrors.firstOrNull()?.defaultMessage ?: "参数异常"
        )
    }

    @ExceptionHandler(SaOAuth2Exception::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun saOAuth2ExceptionHandler(exception: SaOAuth2Exception, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}SaOAuth2异常捕获", exception)
        return ApiResult.fail<Unit>(exception.code, exception.message)
    }

    @ExceptionHandler(SaTokenException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun saTokenExceptionHandler(exception: SaTokenException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}SaToken异常捕获", exception)
        return ApiResult.fail<Unit>(exception.code, exception.message)
    }

    @ExceptionHandler(Exception::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun exceptionHandler(exception: Exception, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}全局异常捕获", exception)
        return ApiResult.fail<Unit>(500, "系统繁忙，请稍后重试")
    }

    @ExceptionHandler(IllegalArgumentException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun argumentExceptionHandler(exception: IllegalArgumentException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}参数异常捕获", exception)
        return ApiResult.fail<Unit>(400, exception.message)
    }

    @ExceptionHandler(BizException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun bizExceptionHandler(exception: BizException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}业务异常捕获", exception)
        return ApiResult.fail<Unit>(exception.code, exception.message)
    }

    @ExceptionHandler(YzApiException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun bizExceptionHandler(exception: YzApiException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}有赞API异常捕获", exception)
        return ApiResult.fail<Unit>(exception.code, exception.message)
    }

    @ExceptionHandler(IllegalStateException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun illegalStateExceptionHandler(exception: IllegalStateException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}数据校验异常", exception)
        return ApiResult.fail<Unit>(400, exception.message)
    }

    @ExceptionHandler(ManageAuthPermissionException::class)
    @ResponseStatus(value = HttpStatus.OK)
    fun manageAuthPermissionExceptionHandler(exception: ManageAuthPermissionException, handlerMethod: HandlerMethod): Any? {
        log.error("${getExtLogInfo(handlerMethod)}数据鉴权异常", exception)
        return ApiResult.fail<Unit>(401, exception.message)
    }

}
""",
    "common/config/GlobalControllerResponseHandler.kt": """package __PACKAGE__.common.config

import com.qingyan.extension.model.vo.ApiResult
import __PACKAGE__.common.annotation.ExcludeResultHandler
import org.springframework.core.MethodParameter
import org.springframework.core.io.InputStreamResource
import org.springframework.http.MediaType
import org.springframework.http.converter.HttpMessageConverter
import org.springframework.http.server.ServerHttpRequest
import org.springframework.http.server.ServerHttpResponse
import org.springframework.web.bind.annotation.RestControllerAdvice
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice

/**
 * response 包装器
 * 禁止范围为全局，必须指定basePackages
 */
@RestControllerAdvice(basePackages = [\"com.youzan.cloud.__PACKAGE__.controller\"])
class GlobalControllerResponseHandler : ResponseBodyAdvice<Any?> {

    override fun supports(returnType: MethodParameter, converterType: Class<out HttpMessageConverter<*>>) =
        returnType.method?.isAnnotationPresent(
            ExcludeResultHandler::class.java
        ) == false

    override fun beforeBodyWrite(
        body: Any?,
        returnType: MethodParameter,
        selectedContentType: MediaType,
        selectedConverterType: Class<out HttpMessageConverter<*>>,
        request: ServerHttpRequest,
        response: ServerHttpResponse,
    ): Any? {
        return if (body is String || body is ApiResult<*> || body is InputStreamResource) body else ApiResult.success(
            body
        )
    }
}
""",
    "common/config/SwaggerConfig.kt": """package __PACKAGE__.common.config

import com.google.common.base.Predicates
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import springfox.documentation.builders.ApiInfoBuilder
import springfox.documentation.builders.PathSelectors
import springfox.documentation.builders.RequestHandlerSelectors
import springfox.documentation.spi.DocumentationType
import springfox.documentation.spring.web.plugins.Docket
import springfox.documentation.swagger2.annotations.EnableSwagger2

@Configuration
@EnableSwagger2
@ConditionalOnProperty(name = ["swagger.enable"], havingValue = "true")
class SwaggerConfig {

    private val host = "__PROJECT_NAME__.isv-dev.youzan.com"

    @Bean
    fun scheduledDocket(): Docket? {
        return Docket(DocumentationType.SWAGGER_2)
            .groupName("定时任务端")
            .apiInfo(
                ApiInfoBuilder()
                    .title("定时任务端接口文档")
                    .version("v1.0")
                    .description("定时任务端接口文档")
                    .build()
            )
            .host(host)
            .select() //指定接口的位置
            .apis(RequestHandlerSelectors.basePackage("__PACKAGE__"))
            .paths(Predicates.or(PathSelectors.ant("/api/v1/scheduled/**")))
            .build()
    }


    @Bean
    fun openDocket(): Docket? {
        return Docket(DocumentationType.SWAGGER_2)
            .groupName("开放端")
            .apiInfo(
                ApiInfoBuilder()
                    .title("接口文档")
                    .version("v1.0")
                    .description("接口文档")
                    .build()
            )
            .host(host)
            .select() //指定接口的位置
            .apis(RequestHandlerSelectors.basePackage("__PACKAGE__"))
            .paths(Predicates.or(PathSelectors.ant("/open/v1/**")))
            .build()
    }

    @Bean
    fun adminDocket(): Docket? {
        return Docket(DocumentationType.SWAGGER_2)
            .groupName("B端")
            .apiInfo(
                ApiInfoBuilder()
                    .title("接口文档")
                    .version("v1.0")
                    .description("接口文档")
                    .build()
            )
            .host(host)
            .select() //指定接口的位置
            .apis(RequestHandlerSelectors.basePackage("__PACKAGE__"))
            .paths(Predicates.or(PathSelectors.ant("/api/v1/admin/**")))
            .build()
    }

    @Bean
    fun clientDocket(): Docket? {
        return Docket(DocumentationType.SWAGGER_2)
            .groupName("C端")
            .apiInfo(
                ApiInfoBuilder()
                    .title("接口文档")
                    .version("v1.0")
                    .description("接口文档")
                    .build()
            )
            .host(host)
            .select() //指定接口的位置
            .apis(RequestHandlerSelectors.basePackage("__PACKAGE__"))
            .paths(Predicates.or(PathSelectors.ant("/api/v1/client/**")))
            .build()
    }

    @Bean
    fun commonDocket(): Docket? {
        return Docket(DocumentationType.SWAGGER_2)
            .groupName("通用")
            .apiInfo(
                ApiInfoBuilder()
                    .title("接口文档")
                    .version("v1.0")
                    .description("接口文档")
                    .build()
            )
            .host(host)
            .select() //指定接口的位置
            .apis(RequestHandlerSelectors.basePackage("__PACKAGE__"))
            .paths(Predicates.or(PathSelectors.ant("/api/v1/common/**")))
            .build()
    }


}
""",
}


ROOT_POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
\txsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
\t<modelVersion>4.0.0</modelVersion>

{parent}
\t<groupId>{group_id}</groupId>
\t<artifactId>{artifact_id}</artifactId>
\t<version>{version}</version>
\t<packaging>pom</packaging>

\t<name>{name}</name>

\t<properties>
\t\t<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
\t\t<project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
\t\t<java.version>1.8</java.version>
\t\t<kotlin.version>1.8.0</kotlin.version>
\t\t<lombok.version>1.18.30</lombok.version>

\t\t<redisson.version>3.16.8</redisson.version>
\t\t<spring-redis.version>2.1.2.RELEASE</spring-redis.version>
\t\t<kotlinx-coroutines-core.version>1.6.2</kotlinx-coroutines-core.version>

\t\t<extension-point-api.version>1.11.3.27</extension-point-api.version>
\t\t<youzan-api-rpc.version>2.0.2-RELEASE</youzan-api-rpc.version>
\t\t<sdk-gen.version>1.0.28.10005026202411191134-RELEASE</sdk-gen.version>
\t\t<push-sdk.version>1.0.0.202103121559-RELEASE</push-sdk.version>
\t</properties>

\t<modules>
\t\t<module>{web_module}</module>
\t</modules>

\t<dependencyManagement>
\t\t<dependencies>
\t\t\t<dependency>
\t\t\t\t<groupId>com.youzan.cloud</groupId>
\t\t\t\t<artifactId>extension-point-api</artifactId>
\t\t\t\t<version>${{extension-point-api.version}}</version>
\t\t\t</dependency>
\t\t\t<dependency>
\t\t\t\t<groupId>com.youzan.boot</groupId>
\t\t\t\t<artifactId>youzan-api-rpc</artifactId>
\t\t\t\t<version>${{youzan-api-rpc.version}}</version>
\t\t\t</dependency>
\t\t\t<dependency>
\t\t\t\t<groupId>com.youzan.cloud</groupId>
\t\t\t\t<artifactId>open-sdk-gen</artifactId>
\t\t\t\t<version>${{sdk-gen.version}}</version>
\t\t\t</dependency>
\t\t\t<dependency>
\t\t\t\t<artifactId>okio</artifactId>
\t\t\t\t<groupId>com.squareup.okio</groupId>
\t\t\t\t<version>1.13.0</version>
\t\t\t</dependency>
\t\t</dependencies>
\t</dependencyManagement>

\t<build>
\t\t<plugins>
\t\t\t<!-- Kotlin compile plugins -->
\t\t\t<plugin>
\t\t\t\t<groupId>org.jetbrains.kotlin</groupId>
\t\t\t\t<artifactId>kotlin-maven-plugin</artifactId>
\t\t\t\t<executions>
\t\t\t\t\t<execution>
\t\t\t\t\t\t<id>compile</id>
\t\t\t\t\t\t<phase>process-sources</phase>
\t\t\t\t\t\t<goals>
\t\t\t\t\t\t\t<goal>compile</goal>
\t\t\t\t\t\t</goals>
\t\t\t\t\t\t<configuration>
\t\t\t\t\t\t\t<sourceDirs>
\t\t\t\t\t\t\t\t<source>src/main/java</source>
\t\t\t\t\t\t\t\t<source>src/main/kotlin</source>
\t\t\t\t\t\t\t</sourceDirs>
\t\t\t\t\t\t</configuration>
\t\t\t\t\t</execution>
\t\t\t\t</executions>
\t\t\t\t<configuration>
\t\t\t\t\t<compilerPlugins>
\t\t\t\t\t\t<plugin>no-arg</plugin>
\t\t\t\t\t\t<plugin>all-open</plugin>
\t\t\t\t\t\t<plugin>spring</plugin>
\t\t\t\t\t</compilerPlugins>
\t\t\t\t\t<pluginOptions>
\t\t\t\t\t\t<option>no-arg:annotation=com.qingyan.extension.annotation.NoArg</option>
\t\t\t\t\t\t<option>no-arg:annotation=com.qingyan.extension.annotation.AllOpen</option>
\t\t\t\t\t\t<option>all-open:annotation=com.youzan.api.rpc.annotation.ExtensionService</option>
\t\t\t\t\t\t<option>all-open:annotation=com.youzan.cloud.metadata.annotation.Topic</option>
\t\t\t\t\t\t<option>all-open:annotation=com.qingyan.extension.annotation.AllOpen</option>
\t\t\t\t\t</pluginOptions>
\t\t\t\t\t<args>
\t\t\t\t\t\t<arg>-Xjsr305=strict</arg>
\t\t\t\t\t</args>
\t\t\t\t</configuration>
\t\t\t\t<dependencies>
\t\t\t\t\t<dependency>
\t\t\t\t\t\t<groupId>org.jetbrains.kotlin</groupId>
\t\t\t\t\t\t<artifactId>kotlin-maven-noarg</artifactId>
\t\t\t\t\t\t<version>${{kotlin.version}}</version>
\t\t\t\t\t</dependency>
\t\t\t\t\t<dependency>
\t\t\t\t\t\t<groupId>org.jetbrains.kotlin</groupId>
\t\t\t\t\t\t<artifactId>kotlin-maven-allopen</artifactId>
\t\t\t\t\t\t<version>${{kotlin.version}}</version>
\t\t\t\t\t</dependency>
\t\t\t\t</dependencies>
\t\t\t</plugin>
\t\t</plugins>
\t</build>
</project>
"""


WEB_POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
\txsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
\t<modelVersion>4.0.0</modelVersion>

\t<parent>
\t\t<groupId>{parent_group_id}</groupId>
\t\t<artifactId>{parent_artifact_id}</artifactId>
\t\t<version>{parent_version}</version>
\t</parent>
\t<artifactId>{artifact_id}</artifactId>
\t<name>{name}</name>

\t<dependencies>
\t\t<!-- 轻研扩展工具 -->
\t\t<dependency>
\t\t\t<groupId>com.qingyan</groupId>
\t\t\t<artifactId>youzan-extension</artifactId>
\t\t\t<version>{qy_extension_version}</version>
\t\t</dependency>

\t\t<dependency>
\t\t\t<groupId>org.slf4j</groupId>
\t\t\t<artifactId>slf4j-api</artifactId>
\t\t</dependency>

\t\t<dependency>
\t\t\t<groupId>com.youzan</groupId>
\t\t\t<artifactId>cloud-base-all</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.cloud</groupId>
\t\t\t<artifactId>extension-point-api</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.boot</groupId>
\t\t\t<artifactId>youzan-api-rpc</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.cloud</groupId>
\t\t\t<artifactId>open-sdk-gen</artifactId>
\t\t</dependency>

\t\t<dependency>
\t\t\t<groupId>com.youzan</groupId>
\t\t\t<artifactId>cloud-base-bifrost-open-sdk</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.boot</groupId>
\t\t\t<artifactId>youzan-boot-starter-druid</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.boot</groupId>
\t\t\t<artifactId>youzan-boot-starter-mybatis</artifactId>
\t\t</dependency>
\t\t<!--指定mybatis版本，解决youzan低版本与dynamic-sql不兼容问题-->
\t\t<dependency>
\t\t\t<groupId>org.mybatis</groupId>
\t\t\t<artifactId>mybatis</artifactId>
\t\t\t<version>3.5.11</version>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.cloud.boot</groupId>
\t\t\t<artifactId>cloud-boot-starter-idempotent</artifactId>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>com.youzan.cloud</groupId>
\t\t\t<artifactId>cloud-component-httpproxy</artifactId>
\t\t\t<version>1.0.1-RELEASE</version>
\t\t</dependency>

\t\t<!--easyexcel依赖-->
\t\t<dependency>
\t\t\t<groupId>com.alibaba</groupId>
\t\t\t<artifactId>easyexcel</artifactId>
\t\t\t<version>3.2.1</version>
\t\t</dependency>

\t\t<!--swagger2依赖-->
\t\t<dependency>
\t\t\t<groupId>io.springfox</groupId>
\t\t\t<artifactId>springfox-swagger2</artifactId>
\t\t\t<version>2.7.0</version>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>io.springfox</groupId>
\t\t\t<artifactId>springfox-swagger-ui</artifactId>
\t\t\t<version>2.7.0</version>
\t\t</dependency>

\t\t<!-- MyBatis 生成器 -->
\t\t<dependency>
\t\t\t<groupId>org.mybatis.generator</groupId>
\t\t\t<artifactId>mybatis-generator-core</artifactId>
\t\t\t<version>1.4.1</version>
\t\t</dependency>
\t\t<!-- bcprov -->
\t\t<dependency>
\t\t\t<groupId>org.bouncycastle</groupId>
\t\t\t<artifactId>bcprov-jdk15to18</artifactId>
\t\t\t<version>1.69</version>
\t\t</dependency>
\t\t<!-- janino -->
\t\t<dependency>
\t\t\t<groupId>org.codehaus.janino</groupId>
\t\t\t<artifactId>janino</artifactId>
\t\t\t<version>2.6.1</version>
\t\t</dependency>

\t\t<dependency>
\t\t\t<groupId>org.redisson</groupId>
\t\t\t<artifactId>redisson-spring-boot-starter</artifactId>
\t\t\t<version>3.16.8</version>
\t\t\t<exclusions>
\t\t\t\t<exclusion>
\t\t\t\t\t<groupId>org.redisson</groupId>
\t\t\t\t\t<artifactId>redisson-spring-data-25</artifactId>
\t\t\t\t</exclusion>
\t\t\t</exclusions>
\t\t</dependency>
\t\t<dependency>
\t\t\t<groupId>org.redisson</groupId>
\t\t\t<artifactId>redisson-spring-data-21</artifactId>
\t\t\t<version>3.16.8</version>
\t\t</dependency>
\t\t<!-- 强制制定redisson -->
\t\t<dependency>
\t\t\t<groupId>org.redisson</groupId>
\t\t\t<artifactId>redisson</artifactId>
\t\t\t<version>3.16.8</version>
\t\t</dependency>

\t\t<!-- HuTool -->
\t\t<dependency>
\t\t\t<groupId>cn.hutool</groupId>
\t\t\t<artifactId>hutool-all</artifactId>
\t\t\t<version>5.8.10</version>
\t\t</dependency>
\t</dependencies>

\t<build>
\t\t<plugins>
\t\t\t<!--   MyBatis逆向工程Maven Plugin-->
\t\t\t<plugin>
\t\t\t\t<groupId>org.mybatis.generator</groupId>
\t\t\t\t<artifactId>mybatis-generator-maven-plugin</artifactId>
\t\t\t\t<version>1.4.0</version>
\t\t\t\t<configuration>
\t\t\t\t\t<overwrite>true</overwrite>
\t\t\t\t\t<configurationFile>src/main/resources/generatorConfig.xml</configurationFile>
\t\t\t\t</configuration>
\t\t\t</plugin>
\t\t\t<plugin>
\t\t\t\t<groupId>com.youzan.aladdin</groupId>
\t\t\t\t<artifactId>aladdin-maven-plugin</artifactId>
\t\t\t\t<executions>
\t\t\t\t\t<execution>
\t\t\t\t\t\t<goals>
\t\t\t\t\t\t\t<goal>repackage</goal>
\t\t\t\t\t\t</goals>
\t\t\t\t\t</execution>
\t\t\t\t</executions>
\t\t\t</plugin>
\t\t</plugins>
\t</build>

</project>
"""


GENERATOR_TEMPLATE = """<!DOCTYPE generatorConfiguration PUBLIC
        "-//mybatis.org//DTD MyBatis Generator Configuration 1.0//EN"
        "http://mybatis.org/dtd/mybatis-generator-config_1_0.dtd">
<generatorConfiguration>

    <classPathEntry
            location="src/main/resources/{mysql_connector_jar_name}"/>

    <context id="kotlin" targetRuntime="MyBatis3Kotlin">
        <jdbcConnection driverClass="com.mysql.cj.jdbc.Driver"
                        connectionURL="jdbc:mysql://{mysql_host}:{mysql_port}/{project_name}?
                  characterEncoding=utf8&amp;useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;allowPublicKeyRetrieval=true"
                        userId="{mysql_username}"
                        password="{mysql_password}">
            <property name="nullCatalogMeansCurrent" value="true"/>
        </jdbcConnection>

        <javaModelGenerator targetPackage="com.youzan.cloud.{package_name}.dal.model" targetProject="src/main/kotlin"/>
        <javaClientGenerator targetPackage="com.youzan.cloud.{package_name}.dal.mapper"
                             targetProject="src/main/kotlin"/>

        <table tableName="table">
            <generatedKey column="id" sqlStatement="JDBC" identity="true"/>
        </table>

    </context>
</generatorConfiguration>
"""


ENV_KEYS = {
    "opensdk.clientId",
    "opensdk.clientSecret",
    "escrow.token.deployment",
    "escrow.token.clientId",
    "escrow.token.clientSecret",
    "escrow.token.tokenType",
    "spring.redis.host",
    "spring.redis.port",
    "cloud.idempotent.redis.enabled",
    "mysql.host",
    "mysql.username",
    "mysql.password",
    "druid.datasource.driverClassName",
    "druid.datasource.url",
    "druid.datasource.username",
    "druid.datasource.password",
    "mybatis.basePackage",
    "mybatis.typeAliasesPackage",
    "mybatis.mapperLocations",
    "mybatis.configuration.logImpl",
    "extension.rootKdtId",
    "isv.oauth.url",
    "swagger.enable",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, text: str, dry_run: bool, changed: list[str]) -> None:
    if path.exists() and read_text(path) == text:
        return
    changed.append(str(path))
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def write_text_if_absent(path: Path, text: str, dry_run: bool, changed: list[str]) -> None:
    if path.exists():
        return
    changed.append(str(path))
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def copy_file_if_absent(source: Path, target: Path, dry_run: bool, changed: list[str]) -> None:
    if target.exists():
        return
    changed.append(str(target))
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def prompt(value: Optional[str], label: str, secret: bool = False, default: Optional[str] = None) -> str:
    if value and value.strip():
        return value.strip()
    if default is not None:
        answer = input(f"{label} [{default}]: ").strip()
        return answer or default
    if secret:
        import getpass
        return getpass.getpass(f"{label}: ").strip()
    return input(f"{label}: ").strip()


def find_tag(xml: str, tag: str) -> Optional[str]:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.S)
    return match.group(1).strip() if match else None


def without_parent(xml: str) -> str:
    return re.sub(r"\s*<parent>.*?</parent>\s*", "\n", xml, count=1, flags=re.S)


def find_own_tag(xml: str, tag: str) -> Optional[str]:
    return find_tag(without_parent(xml), tag)


def find_parent(xml: str) -> str:
    match = re.search(r"(\s*<parent>.*?</parent>\s*)", xml, re.S)
    return match.group(1) + "\n" if match else ""


def detect_project_name(root: Path, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    artifact = find_own_tag(read_text(root / "pom.xml"), "artifactId")
    return artifact or root.name


def detect_web_module(root: Path, project_name: str, explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    expected = f"{project_name}-web"
    if (root / expected / "pom.xml").exists():
        return expected
    modules = [p.name for p in root.glob("*-web") if (p / "pom.xml").exists()]
    if len(modules) == 1:
        return modules[0]
    return expected


def create_dir_if_absent(path: Path, dry_run: bool, changed: list[str]) -> None:
    if path.exists():
        return
    changed.append(str(path))
    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)


def build_package_name(project_name: str) -> str:
    """把工件名转换为合法包名，例如 yf-brp -> yf.brp。"""
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", project_name) if part]
    return ".".join(parts) or "app"


def build_package_path(package_name: str) -> str:
    """把包名转换为源码目录，例如 yf.brp -> yf/brp。"""
    return package_name.replace(".", "/")


def build_common_file_text(template: str, project_name: str, package_name: str) -> str:
    return (
        template
        .replace("__PACKAGE__", f"com.youzan.cloud.{package_name}")
        .replace("__PROJECT_NAME__", project_name)
    )


def build_project_class_name(project_name: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", project_name) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Application"


def build_agents_text(project_name: str, web_module: str, package_path: str) -> str:
    return (
        AGENTS_TEMPLATE
        .replace("__PACKAGE_PATH__", package_path)
        .replace("__PROJECT_NAME__", project_name)
        .replace("__PROJECT_CLASS_NAME__", build_project_class_name(project_name))
        .replace("__WEB_MODULE__", web_module)
    )


def create_project_scaffold(kotlin_package: Path, project_name: str, package_name: str, dry_run: bool, changed: list[str]) -> None:
    for relative_dir in PROJECT_PACKAGE_DIRS:
        create_dir_if_absent(kotlin_package / relative_dir, dry_run, changed)
    for relative_file, template in COMMON_FILE_TEMPLATES.items():
        write_text_if_absent(
            kotlin_package / relative_file,
            build_common_file_text(template, project_name, package_name),
            dry_run,
            changed,
        )


def env_block(project_name: str, package_name: str, client_id: str, client_secret: str) -> str:
    return f"""#opensdk
opensdk.clientId={client_id}
opensdk.clientSecret={client_secret}

#token management
escrow.token.deployment=cloud
escrow.token.clientId=${{opensdk.clientId}}
escrow.token.clientSecret=${{opensdk.clientSecret}}
escrow.token.tokenType=silent

#redis
spring.redis.host=192.168.2.111
spring.redis.port=6379

#idempotent component
cloud.idempotent.redis.enabled=true

#mysql
mysql.host={MYSQL_HOST}
mysql.username={MYSQL_USERNAME}
mysql.password={MYSQL_PASSWORD}
druid.datasource.driverClassName=com.mysql.jdbc.Driver
druid.datasource.url=jdbc:mysql://${{mysql.host}}:{MYSQL_PORT}/{project_name}?characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
druid.datasource.username=${{mysql.username}}
druid.datasource.password=${{mysql.password}}

#mybatis
mybatis.basePackage=com.youzan.cloud.{package_name}.dal.mapper
mybatis.typeAliasesPackage=com.youzan.cloud.{package_name}.dal.model
mybatis.mapperLocations=classpath:mapper/*.xml,classpath*:mybatis/mapper/*.xml
mybatis.configuration.logImpl=org.apache.ibatis.logging.stdout.StdOutImpl

extension.rootKdtId=

isv.oauth.url=https://oauth.isv-dev.youzan.com

swagger.enable=true
"""


def update_env(root: Path, block: str, dry_run: bool, changed: list[str]) -> None:
    path = root / ".ENV"
    existing = read_text(path).splitlines()
    kept: list[str] = []
    previous_blank = False
    for line in existing:
        key = line.split("=", 1)[0].strip() if "=" in line else None
        if key in ENV_KEYS:
            continue
        if line.strip() == "" and previous_blank:
            continue
        kept.append(line)
        previous_blank = line.strip() == ""
    text = "\n".join(kept).rstrip()
    text = (text + "\n\n" if text else "") + block.rstrip() + "\n"
    write_text(path, text, dry_run, changed)


def update_gitignore(root: Path, dry_run: bool, changed: list[str]) -> None:
    path = root / ".gitignore"
    existing = read_text(path)
    if GENERATOR_CONFIG_IGNORE_ENTRY in {line.strip() for line in existing.splitlines()}:
        return
    separator = "" if not existing or existing.endswith("\n") else "\n"
    write_text(path, f"{existing}{separator}{GENERATOR_CONFIG_IGNORE_ENTRY}\n", dry_run, changed)


def create_vibe_coding_workspace(root: Path, project_name: str, web_module: str, package_path: str, dry_run: bool, changed: list[str]) -> None:
    docs_dir = root / "docs"
    if not docs_dir.exists():
        changed.append(str(docs_dir))
        if not dry_run:
            docs_dir.mkdir(parents=True, exist_ok=True)
    legacy_frontend_doc = docs_dir / LEGACY_FRONTEND_DEVELOPMENT_DOC_NAME
    if legacy_frontend_doc.exists():
        changed.append(str(legacy_frontend_doc))
        if not dry_run:
            legacy_frontend_doc.unlink()
    copy_file_if_absent(
        CONSUMER_DEVELOPMENT_DOC,
        docs_dir / CONSUMER_DEVELOPMENT_DOC_NAME,
        dry_run,
        changed,
    )
    copy_file_if_absent(
        ADMIN_DEVELOPMENT_DOC,
        docs_dir / ADMIN_DEVELOPMENT_DOC_NAME,
        dry_run,
        changed,
    )
    write_text_if_absent(root / "AGENTS.md", build_agents_text(project_name, web_module, package_path), dry_run, changed)


def print_changed_paths(changed: list[str]) -> None:
    print("Changed paths:" if changed else "No changes.")
    for item in changed:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Youzan/Qingyan Kotlin Spring Maven project.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--project-name", help="Project name used for module names, database name, and default package name.")
    parser.add_argument("--package-name", help="Kotlin package name, defaults to project name with '-' replaced by '.'.")
    parser.add_argument("--web-module", help="Web module directory name.")
    parser.add_argument("--client-id", help="OpenSDK clientId.")
    parser.add_argument("--client-secret", help="OpenSDK clientSecret.")
    parser.add_argument("--qy-extension-version", help="com.qingyan:youzan-extension version.")
    parser.add_argument("--create-vibe-coding-workspace", action="store_true", help="Only create the workspace with the consumer and admin development guides and root AGENTS.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not (root / "pom.xml").exists():
        print(f"error: pom.xml not found under {root}", file=sys.stderr)
        return 2

    changed: list[str] = []
    if args.create_vibe_coding_workspace:
        project_name = detect_project_name(root, args.project_name)
        web_module = detect_web_module(root, project_name, args.web_module)
        package_name = args.package_name.strip() if args.package_name else build_package_name(project_name)
        create_vibe_coding_workspace(root, project_name, web_module, build_package_path(package_name), args.dry_run, changed)
        print_changed_paths(changed)
        return 0

    project_name = detect_project_name(root, args.project_name)
    web_module = detect_web_module(root, project_name, args.web_module)
    web_root = root / web_module
    package_name = args.package_name.strip() if args.package_name else build_package_name(project_name)

    client_id = prompt(args.client_id, "application clientId")
    client_secret = prompt(args.client_secret, "application clientSecret", secret=True)
    qy_extension_version = args.qy_extension_version.strip() if args.qy_extension_version else DEFAULT_QY_EXTENSION_VERSION

    root_xml = read_text(root / "pom.xml")
    root_parent = find_parent(root_xml)
    root_group = find_own_tag(root_xml, "groupId") or "com.youzan.cloud"
    root_artifact = find_own_tag(root_xml, "artifactId") or project_name
    root_version = find_own_tag(root_xml, "version") or "1.0.0-SNAPSHOT"
    root_name = find_own_tag(root_xml, "name") or root_artifact

    for suffix in ("api", "biz", "dal", "deploy"):
        module = root / f"{project_name}-{suffix}"
        if module.exists():
            changed.append(str(module))
            if not args.dry_run:
                shutil.rmtree(module)

    write_text(
        root / "pom.xml",
        ROOT_POM_TEMPLATE.format(
            parent=root_parent,
            group_id=root_group,
            artifact_id=root_artifact,
            version=root_version,
            name=root_name,
            web_module=web_module,
            project_name=project_name,
        ),
        args.dry_run,
        changed,
    )

    web_xml = read_text(web_root / "pom.xml")
    web_artifact = find_own_tag(web_xml, "artifactId") or web_module
    web_name = find_own_tag(web_xml, "name") or web_artifact
    write_text(
        web_root / "pom.xml",
        WEB_POM_TEMPLATE.format(
            parent_group_id=root_group,
            parent_artifact_id=root_artifact,
            parent_version=root_version,
            artifact_id=web_artifact,
            name=web_name,
            qy_extension_version=qy_extension_version,
        ),
        args.dry_run,
        changed,
    )

    java_web_package = web_root / "src/main/java/com/youzan/cloud" / build_package_path(package_name) / "web"
    if java_web_package.exists():
        changed.append(str(java_web_package))
        if not args.dry_run:
            shutil.rmtree(java_web_package)

    kotlin_package = web_root / "src/main/kotlin/com/youzan/cloud" / build_package_path(package_name)
    create_dir_if_absent(kotlin_package, args.dry_run, changed)
    create_project_scaffold(kotlin_package, project_name, package_name, args.dry_run, changed)

    update_env(
        root,
        env_block(project_name, package_name, client_id, client_secret),
        args.dry_run,
        changed,
    )

    copy_file_if_absent(
        MYSQL_CONNECTOR_JAR,
        web_root / "src/main/resources" / MYSQL_CONNECTOR_JAR_NAME,
        args.dry_run,
        changed,
    )

    write_text(
        web_root / "src/main/resources/generatorConfig.xml",
        GENERATOR_TEMPLATE.format(
            project_name=project_name,
            package_name=package_name,
            mysql_host=MYSQL_HOST,
            mysql_port=MYSQL_PORT,
            mysql_username=MYSQL_USERNAME,
            mysql_password=MYSQL_PASSWORD,
            mysql_connector_jar_name=MYSQL_CONNECTOR_JAR_NAME,
        ),
        args.dry_run,
        changed,
    )
    update_gitignore(root, args.dry_run, changed)

    create_vibe_coding_workspace(root, project_name, web_module, build_package_path(package_name), args.dry_run, changed)

    print_changed_paths(changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
