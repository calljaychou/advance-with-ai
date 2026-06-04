---
name: youzan-rds-select
description: 通过有赞 RDS DML 接口执行 SELECT 查询并判断数据是否存在、同步是否成功或业务状态是否满足预期。当用户需要按项目关键词匹配有赞 RDS 库配置、按业务问题匹配 SQL 模板、使用 sid Cookie 调用 youzan_rds_select 脚本，或分析有赞 RDS 查询返回的 rows、登录失效、表不存在等结果时使用。
---

# 有赞 RDS Select 查询

使用此 skill 时，通过项目映射、查询方法模板和 `scripts/youzan_rds_select.sh` 调用有赞 RDS 查询接口，并基于模板中的 `resultValidate` 回答开发者问题。

## 默认原则

- 只执行 `SELECT` 查询，禁止生成或执行 `INSERT`、`UPDATE`、`DELETE`、`DDL` 等变更语句。
- 在用户未明确要求执行查询前，先说明将使用的库、方法和 SQL。
- 不要在回复中暴露完整 `sid`；需要引用时只展示前后少量字符或直接说明已使用用户提供的 sid。
- 若项目关键词或查询方法无法唯一匹配，先让用户补充关键词，不要猜测业务库。

## 输入收集

从用户请求中收集这些信息：

- 项目关键词：例如 `宝胜`、`YYSPORTS`、`YY`、`pousheng`。
- 查询方法或业务问题：例如 `查询订单是否推送成功`。
- SQL 模板变量：例如订单号、退款单号、业务值等。
- `zone`：默认使用用户提供值；未提供时询问，常见值为 `prod`。
- `sid`：必须由用户提供。缺失时提示用户登录有赞后从 Cookie 中获取 `sid`。

如果缺少 `sid`、`zone` 或 SQL 模板变量，先询问用户补齐。

## 匹配流程

1. 读取 `references/project-mapping.json`，用用户项目关键词匹配 `keyword` 字段，获取 `dbName`、`bizInsId`、`appId`。
2. 读取 `references/query-methods.json`，先按第一步命中的 `dbName` 过滤，再根据用户的问题或方法名称匹配 `method`。
3. 用用户提供的变量替换 `statement` 中的占位符，例如 `{订单号}`。
4. 确认最终 SQL 仍为只读 `SELECT`。
5. 调用 `scripts/youzan_rds_select.sh` 发送请求，并分析返回 JSON。

## 脚本调用

优先使用 bundled shell 脚本执行请求：

```bash
skills/youzan-rds-select/scripts/youzan_rds_select.sh \
  --sid "<sid>" \
  --zone "prod" \
  --db-name "youzan-pousheng" \
  --biz-ins-id "404874cf96a1459dbe725ea2b99c3cfb" \
  --app-id "10006653" \
  --statement "SELECT * FROM order_sync_log WHERE biz_value='E20260424111842046600053' AND sync_status = 1"
```

脚本固定使用：

- URL：`https://diy.youzanyun.com/api/rds/exec-dml?`
- `limit`：`500`
- Cookie：`sid=<用户提供的 sid>`

## 结果分析

按以下顺序处理返回：

1. 如果返回 `code=400` 且 `msg` 或 `message` 为 `登录失效`，说明 sid 已失效。提示用户重新访问 `https://account.youzan.com/login` 登录，并从 Cookie 获取新的 `sid`。
2. 如果返回 `code=700200034`，且提示 `table [...] not exist or offline`，说明当前项目 mapping 很可能不正确。让用户重新提供项目关键词或补充正确项目名称。
3. 如果 `success=false` 或 HTTP 请求失败，说明接口调用失败。返回错误码、错误消息和建议动作。
4. 如果查询成功，读取 `data[0].result.rows`：
   - 第一行通常是列名。
   - 第二行开始是数据行。
   - `rows` 数量大于等于 2 表示至少存在一条业务数据。
5. 根据命中的方法模板中的 `resultValidate` 给出判断。模板中写 `获取到的rows数量大于等一1` 时，按“数据行数量大于等于 1”理解，即 `rows.size >= 2`。

## 返回格式

按固定格式回答：

```text
库：<第一步选择的 dbName>
执行方法名称：<第二步选择的方法>
结果：<resultValidate 的判断结果>
原因：<说明判断依据，例如 rows 中数据行数量、关键字段值、错误码或异常信息>
```

如果无法执行查询，也使用相同结构，并在 `结果` 中写明失败原因。

## 资源文件

- `references/project-mapping.json`：项目关键词到 RDS 调用参数的映射。
- `references/query-methods.json`：业务查询方法、校验规则和 SQL 模板。
- `scripts/youzan_rds_select.sh`：调用有赞 RDS 查询接口的 shell 脚本。
