#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


DEFAULT_QY_EXTENSION_VERSION = "0.0.8-SNAPSHOT"


AGENTS_TEMPLATE = """# AGENTS
本文件用于指导 AI Agent 处理当前代码仓库内的项目代码。

## 有赞云定制有容器开发
有赞云定制开发面向有技术能力的商家或服务商，围绕店铺、商品、订单、会员、营销等业务场景，通过开放 API、消息和扩展点，把有赞
店铺与商家自有系统打通，承载个性化商城页面、后端业务流程和行业解决方案。项目通常分为无容器和有容器两类：有容器可在有赞云 PaaS 
环境中开发自用型定制能力，如定制 H5、小程序页面和业务流程。开发过程中必须严格 遵守店铺授权、能力包权限和数据使用边界，
仅在已授权店铺范围内处理数据，不做跨主体聚合或未经授权的数据共享；自用型有容器应用按有赞云接入流程创建，通常需要对应的大客技术套餐和平台授权。


## 项目概述

**技术栈**：
- 后端：Java 8 + Kotlin 1.8.0、Spring Boot、有赞云基座（cloud-parent 1.1.3-RELEASE）
- 数据库：MySQL，持久层框架 MyBatis 3.5.11
- 缓存：Redis，客户端 Redisson 3.16.8
- 前端：React 18 + Vite 5 + TypeScript（后台管理主面板）、Zent UI（商家云应用）、微信小程序

## 整体架构说明

### 后端目录结构

后端为Java + Kotlin 混合开发 Spring Boot 应用：

```plaintext
__WEB_MODULE__/src/main/
├── java/                                     # Java 入口类 & 有赞扩展包装层
│   └── com/youzan/cloud/__PROJECT_NAME__/
│       ├── __PROJECT_CLASS_NAME__Application.java               # Spring Boot 程序启动入口
│       └── open/youzan/extension/            # 有赞扩展点实现包装类
└── kotlin/                                   # Kotlin 源码（核心业务逻辑层）
    └── com/youzan/cloud/__PROJECT_NAME__/
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

### 前端目录结构


## Guide
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
@RestControllerAdvice(basePackages = [\"com.youzan.cloud.__PROJECT_NAME__.controller\"])
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
\t\t\t\t\t\t<option>all-open:annotation=com.youzan.cloud.{project_name}.common.annotation.AllOpen</option>
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
            location="/Users/mac-z/.m2/repository/mysql/mysql-connector-java/8.0.19/mysql-connector-java-8.0.19.jar"/>

    <context id="kotlin" targetRuntime="MyBatis3Kotlin">
        <jdbcConnection driverClass="com.mysql.cj.jdbc.Driver"
                        connectionURL="jdbc:mysql://localhost:3306/youzan-pousheng?
                  characterEncoding=utf8&amp;useSSL=false&amp;serverTimezone=Asia/Shanghai&amp;allowPublicKeyRetrieval=true"
                        userId="{mysql_username}"
                        password="{mysql_password}"/>

        <javaModelGenerator targetPackage="com.youzan.cloud.youzan.{project_name}.dal.model" targetProject="src/main/kotlin"/>
        <javaClientGenerator targetPackage="com.youzan.cloud.youzan.{project_name}.dal.mapper"
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
    "mysql.username",
    "mysql.password",
    "druid.datasource.driverClassName",
    "druid.datasource.url",
    "druid.datasource.username",
    "druid.datasource.password",
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


def build_common_file_text(template: str, project_name: str) -> str:
    package_name = f"com.youzan.cloud.{project_name}"
    return template.replace("__PACKAGE__", package_name).replace("__PROJECT_NAME__", project_name)


def build_project_class_name(project_name: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", project_name) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Application"


def build_agents_text(project_name: str, web_module: str) -> str:
    return (
        AGENTS_TEMPLATE
        .replace("__PROJECT_NAME__", project_name)
        .replace("__PROJECT_CLASS_NAME__", build_project_class_name(project_name))
        .replace("__WEB_MODULE__", web_module)
    )


def create_project_scaffold(kotlin_package: Path, project_name: str, dry_run: bool, changed: list[str]) -> None:
    for relative_dir in PROJECT_PACKAGE_DIRS:
        create_dir_if_absent(kotlin_package / relative_dir, dry_run, changed)
    for relative_file, template in COMMON_FILE_TEMPLATES.items():
        write_text_if_absent(
            kotlin_package / relative_file,
            build_common_file_text(template, project_name),
            dry_run,
            changed,
        )


def env_block(project_name: str, client_id: str, client_secret: str, mysql_username: str, mysql_password: str) -> str:
    return f"""#opensdk
opensdk.clientId={client_id}
opensdk.clientSecret={client_secret}

#token management
escrow.token.deployment=cloud
escrow.token.clientId=${{opensdk.clientId}}
escrow.token.clientSecret=${{opensdk.clientSecret}}
escrow.token.tokenType=silent

#redis
spring.redis.host=127.0.0.1
spring.redis.port=6379

#idempotent component
cloud.idempotent.redis.enabled=true

#mysql
mysql.username={mysql_username}
mysql.password={mysql_password}
druid.datasource.driverClassName=com.mysql.jdbc.Driver
druid.datasource.url=jdbc:mysql://127.0.0.1:3306/{project_name}?characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
druid.datasource.username=${{mysql.username}}
druid.datasource.password=${{mysql.password}}

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


def create_vibe_coding_workspace(root: Path, project_name: str, web_module: str, dry_run: bool, changed: list[str]) -> None:
    for doc_dir in (root / "docs/PRDs", root / "docs/RFCs", root / "docs/Plans"):
        if not doc_dir.exists():
            changed.append(str(doc_dir))
            if not dry_run:
                doc_dir.mkdir(parents=True, exist_ok=True)
    write_text_if_absent(root / "AGENTS.md", build_agents_text(project_name, web_module), dry_run, changed)


def print_changed_paths(changed: list[str]) -> None:
    print("Changed paths:" if changed else "No changes.")
    for item in changed:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a Youzan/Qingyan Kotlin Spring Maven project.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument("--project-name", help="Project name used for package paths and DB name.")
    parser.add_argument("--web-module", help="Web module directory name.")
    parser.add_argument("--client-id", help="OpenSDK clientId.")
    parser.add_argument("--client-secret", help="OpenSDK clientSecret.")
    parser.add_argument("--mysql-username", help="Local MySQL username.")
    parser.add_argument("--mysql-password", help="Local MySQL password.")
    parser.add_argument("--qy-extension-version", help="com.qingyan:youzan-extension version.")
    parser.add_argument("--create-vibe-coding-workspace", action="store_true", help="Only create docs/PRDs, docs/RFCs, docs/Plans, and root AGENTS.md.")
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
        create_vibe_coding_workspace(root, project_name, web_module, args.dry_run, changed)
        print_changed_paths(changed)
        return 0

    project_name = detect_project_name(root, args.project_name)
    web_module = detect_web_module(root, project_name, args.web_module)
    web_root = root / web_module

    client_id = prompt(args.client_id, "application clientId")
    client_secret = prompt(args.client_secret, "application clientSecret", secret=True)
    mysql_username = prompt(args.mysql_username, "local MySQL username")
    mysql_password = prompt(args.mysql_password, "local MySQL password", secret=True)
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

    java_web_package = web_root / "src/main/java/com/youzan/cloud" / project_name / "web"
    if java_web_package.exists():
        changed.append(str(java_web_package))
        if not args.dry_run:
            shutil.rmtree(java_web_package)

    kotlin_package = web_root / "src/main/kotlin/com/youzan/cloud" / project_name
    create_dir_if_absent(kotlin_package, args.dry_run, changed)
    create_project_scaffold(kotlin_package, project_name, args.dry_run, changed)

    update_env(
        root,
        env_block(project_name, client_id, client_secret, mysql_username, mysql_password),
        args.dry_run,
        changed,
    )

    write_text(
        web_root / "src/main/resources/generatorConfig.xml",
        GENERATOR_TEMPLATE.format(
            project_name=project_name,
            mysql_username=mysql_username,
            mysql_password=mysql_password,
        ),
        args.dry_run,
        changed,
    )

    print_changed_paths(changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
