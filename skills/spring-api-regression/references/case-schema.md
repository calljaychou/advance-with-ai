# 用例数据结构说明

在生成或扩展 `test_cases.json` 时，使用本文档作为字段说明。

## 顶层字段

- `base_url`：目标服务地址，例如 `http://127.0.0.1:8080`
- `variables`：全局共享占位变量，供所有用例复用
- `default_headers`：每个请求默认携带的公共请求头
- `cases`：按顺序执行的测试场景列表

## 用例字段

每个用例都应当能够独立表达一个清晰的业务场景。

- `name`：用例名称，建议使用便于日志阅读的描述
- `method`：HTTP 请求方法，例如 `GET`、`POST`、`PUT`、`DELETE`
- `path`：接口路径，支持占位符替换
- `headers`：当前用例专属请求头，可覆盖或补充 `default_headers`
- `query`：URL 查询参数
- `body`：请求体，通常为 JSON 结构
- `variables`：当前用例专属变量，会覆盖同名全局变量
- `expected_status`：期望的 HTTP 状态码
- `expected_contains`：期望在响应文本中出现的关键片段

## 占位符规则

统一使用 `{{key}}` 格式。Python 模板会按以下顺序替换占位符：

1. 顶层 `variables`
2. 当前用例下的 `variables`

如果同名变量同时存在，则当前用例的 `variables` 优先级更高。

## 推荐约定

- 一个用例只表达一个业务场景，避免职责过多
- 认证信息、租户信息等公共数据优先放在顶层 `variables`
- 较大的请求体内容放在 `body` 中，不要写死在 Python 脚本里
- 默认使用 `expected_contains` 做轻量回归校验，便于维护
- 如果是共享环境，默认避免新增、修改、删除等破坏性请求

## 示例

```json
{
  "name": "query order detail",
  "method": "GET",
  "path": "/api/orders/{{order_id}}",
  "headers": {},
  "query": {
    "verbose": true
  },
  "body": null,
  "variables": {
    "order_id": "SO202605200001"
  },
  "expected_status": 200,
  "expected_contains": [
    "\"orderId\": \"SO202605200001\""
  ]
}
```
