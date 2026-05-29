---
name: spring-api-regression
description: Create Python-based API regression test scripts for Spring Web or Spring MVC projects when the user wants to avoid or supplement MockMvc tests, build readable API replay scenarios, keep mock request data inline in the Python runner, or print complete request and response payloads for debugging and review. Use this skill whenever the user mentions Spring Web regression testing, MockMvc limitations, Python API scripts, interface replay, API smoke checks, or readable request/response logs.
---

# Spring API Regression

Use this skill to generate a lightweight regression testing package for Spring Web APIs with Python scripts instead of relying only on `MockMvc`.

This skill is best when the user wants:

- A Python script that can replay HTTP requests against a running local service or a remote test environment
- Mock request data stored in an inline Python configuration and easy to replace in one file
- Complete and readable request and response logs for debugging, comparison, and review
- A low-coupling regression path that is less tied to Spring test context, database fixtures, or `MockMvc` behavior

## Default Goal

Default to **generating scripts and templates only**.

Do not execute requests unless the user explicitly asks for execution or verification.

## Invoke When

Use this skill when any of the following is true:

- The user says Spring MVC or `MockMvc` tests are not enough or are hard to maintain
- The user wants to test HTTP interfaces from outside the application process
- The user wants Python scripts to mock API requests or replay regression scenarios
- The user wants request and response payloads printed in full for troubleshooting
- The user wants mock data grouped in a clear inline configuration so that scenarios are easy to read and replace

## First Step

Before generating files, confirm these inputs if the user has not already provided them:

1. Target mode: local running service or remote test environment
2. Base URL: for example `http://127.0.0.1:8080`
3. Authentication method: none, token, cookie, signature, or custom header
4. Target endpoints and HTTP methods
5. Whether the user wants pure regression replay, smoke checks, or assertion-rich verification

If information is missing, ask concise follow-up questions before writing the script.

## Output Contract

Unless the user asks for a different shape, generate:

- `regression_api_test.py`: the main Python runner
- `README.md` or short usage notes when execution steps need explanation

Keep names descriptive and stable. Prefer `snake_case` for Python files and variables.

## Script Design Rules

### 1. Keep Mock Data Inline But Structured

Put request scenarios, headers, path, query, body, and simple expectations in the `TEST_CONFIG` dictionary near the top of `regression_api_test.py`.

The Python script should focus on:

- Reading inline configuration
- Replacing placeholders
- Sending HTTP requests
- Printing readable logs
- Summarizing pass or fail

Keep request bodies as readable Python dictionaries and lists. Do not generate a separate `test_cases.json` file unless the user explicitly asks for externalized data.

### 2. Keep Mock Data Clear And Replaceable

Use a structure that is obvious to edit in batches:

- `variables`: shared placeholders such as `token`, `user_id`, `tenant_id`
- `default_headers`: shared headers
- `cases`: a list of independent request scenarios

Each case should usually include:

- `name`
- `method`
- `path`
- `headers`
- `query`
- `body`
- `expected_status`
- `expected_contains` or another lightweight expectation field when useful

Prefer JSON-like Python literals that can be replaced by copy-paste with minimal Python changes.

### 3. Print Full Request And Response

Readable logs are the core of this skill. The generated script should print:

- Case name
- Full URL
- Method
- Final headers after placeholder replacement
- Query parameters
- Request body
- Response status code
- Response headers when useful
- Full response body, pretty-printed when JSON

Prefer clear separators and pretty JSON formatting over compressed one-line output.

### 4. Support Both Local And Remote Targets

The script should let the user switch between:

- Local mode: calling a started Spring service on localhost
- Remote mode: calling a provided test environment base URL

Do not bind the script to Spring internals, `MockMvc`, or application context startup.

### 5. Keep Assertions Lightweight By Default

Default to simple checks that are easy to maintain:

- HTTP status code
- Response body contains expected fields or fragments

Only add heavy assertion logic when the user clearly wants richer verification.

## Generation Workflow

When this skill is triggered, follow this order:

1. Confirm missing environment and endpoint information
2. Decide whether the deliverable is script-only or script plus usage notes
3. Generate `regression_api_test.py` with a visible `TEST_CONFIG` dictionary near the top
4. Keep the runner functions aligned with that inline configuration structure
5. Ensure logs print full request and response content in a readable way
6. Explain how to replace mock data, switch environments, and extend cases

## Recommended Python Structure

When generating the Python file, prefer this structure:

- `replace_placeholders()`
- `build_url()`
- `send_case()`
- `print_request_log()`
- `print_response_log()`
- `evaluate_case()`
- `main()`

Keep helper functions small and descriptive.

## Logging Style

Use obvious visual sections, for example:

```
    ========== CASE START ==========
    case name
    ========== CASE START ==========
    🍀REQUEST
    🍀RESPONSE
    CASS ✅通过/❌失败
    ========== CASE END ============
```

If the response is JSON, pretty-print with indentation and preserve non-ASCII characters when present.

## Safety And Restraints

- Do not silently execute destructive endpoints unless the user explicitly confirms they want that
- Warn before generating replay cases for create, update, or delete operations in shared environments
- If authentication details are missing, leave placeholders rather than invent fake credentials
- If the user asks for sensitive headers to be printed, follow the request; otherwise mask obvious secrets in examples

## Example Deliverable Pattern

### Example 1

User intent: "MockMvc 覆盖不住联调场景，帮我写 Python 回归脚本回放 `POST /v1/chat/completions`。"

Expected result:

- A Python runner using `requests`
- Inline `TEST_CONFIG` data for cases
- Complete request and response logs
- Notes explaining where to replace token, host, and request body

### Example 2

User intent: "给我一个可以切换本地和测试环境的 Spring API 冒烟脚本模板。"

Expected result:

- Environment-aware base URL handling
- Shared headers and variables
- Multiple cases in the inline `TEST_CONFIG` dictionary
- Simple status and body fragment checks

## Bundled Resources

If needed, read these bundled files before generating output:

- `templates/regression_api_test.py`
- `references/case-schema.md`
