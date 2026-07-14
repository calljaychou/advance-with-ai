#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


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


def prompt(value: Optional[str], label: str, secret: bool = False) -> str:
    if value:
        return value
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
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not (root / "pom.xml").exists():
        print(f"error: pom.xml not found under {root}", file=sys.stderr)
        return 2

    project_name = detect_project_name(root, args.project_name)
    web_module = detect_web_module(root, project_name, args.web_module)
    web_root = root / web_module

    client_id = prompt(args.client_id, "application clientId")
    client_secret = prompt(args.client_secret, "application clientSecret", secret=True)
    mysql_username = prompt(args.mysql_username, "local MySQL username")
    mysql_password = prompt(args.mysql_password, "local MySQL password", secret=True)
    qy_extension_version = prompt(args.qy_extension_version, "QY extension package version")

    changed: list[str] = []
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
    if not kotlin_package.exists():
        changed.append(str(kotlin_package))
        if not args.dry_run:
            kotlin_package.mkdir(parents=True, exist_ok=True)

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

    for doc_dir in (root / "docs/PRDs", root / "docs/RFCs", root / "docs/Plans"):
        if not doc_dir.exists():
            changed.append(str(doc_dir))
            if not args.dry_run:
                doc_dir.mkdir(parents=True, exist_ok=True)

    print("Changed paths:" if changed else "No changes.")
    for item in changed:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
