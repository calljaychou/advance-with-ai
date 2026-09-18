---
name: script-interface-discovery
description: Discover, explain, and call project HTTP interfaces whose request mapping lives under /script, keyed by the current chat. Use when the user provides a project path and asks to find, list, explain, or call script interfaces, or selects a previously listed interface by number in the same chat. Do not use for general REST API discovery outside the /script scope.
---

# Script Interface Discovery Skill

Discover project HTTP interfaces whose `requestMapping` path is under `/script`, explain their parameters, assign stable numeric keys per group chat, call a user-selected interface, and report the result. This skill does not invent endpoints or parameters; it relies on source inspection and the project's documented/runtime invocation contract.

## When to Use

- Use when the user provides a project path and asks to find, list, explain, or call script interfaces.
- Use when the user selects a previously listed interface by number in the same group chat.
- Use when the user replies with a previously offered invocation sentence (`使用 <key> 号脚本，入参：<参数名>=<值>，环境 DEV|PROD`).
- Do not use for arbitrary REST API discovery outside the `/script` path unless the user explicitly changes the scope.

## Prerequisites

- A readable project directory.
- Prefer the project's controller directory as the scan root. For the Youzan Pousheng project, use `youzan-pousheng-web/src/main/kotlin/com/youzan/cloud/youzan/pousheng/controller` rather than scanning the repository root.
- The controller source must contain `requestMapping` declarations or equivalent Spring route annotations.
- A callable project runtime, CLI, HTTP base URL, or documented invocation command must exist before execution. If none can be identified, report that discovery succeeded but invocation cannot be performed yet.
- Resolve the environment from the invocation sentence or the current chat context before invocation. Alert text containing `DEV` means test and `PROD` means production. If no environment is present, ask instead of choosing one.
- Authentication is never a user-facing input. Resolve it once during discovery into `auth`, and inject it automatically at invocation.
- Use the current group-chat identifier as the cache key. Never use the chat display name as the key.

## Persistent Index

Keep the discovered interface index in a profile-safe JSON file that lives inside this skill's own directory, next to `SKILL.md`:

`<skills_dir>/script-interface-discovery/cache.json`

`<skills_dir>` is the skills root of the agent this skill was installed into (`~/.codex/skills` or `~/.claude/skills`). Treat `cache.json` as runtime state, not source: the repository's `install.sh` replaces the whole skill directory when it copies, so back the file up before reinstalling and expect it to be regenerated otherwise.

The top-level structure is:

```json
{
  "<chat_id>": {
    "project_path": "<absolute-or-user-provided-path>",
    "environments": [
      {
        "environment": "PROD",
        "baseURL": "https://youzan-pousheng.isv.youzan.com"
      },
      {
        "environment": "DEV",
        "baseURL": "https://youzan-pousheng.isv-dev.youzan.com"
      }
    ],
    "selected_environment": "DEV|PROD|unknown",
    "discovered_at": "<ISO-8601>",
    "labels": {
      "<field_name>": "<business label in the user's language>"
    },
    "response_envelope": {
      "wrapper": "<fully.qualified.ResponseWrapper>",
      "fields": ["code", "success", "message", "timestamp", "data"],
      "success_when": "success == true",
      "http_status": "always 200 — every handler of the project's global exception advice returns @ResponseStatus(HttpStatus.OK), so transport status and process exit code never reflect the business outcome"
    },
    "sort_rule": "<normalized path, HTTP method, handler>",
    "interfaces": [
      {
        "key": 1,
        "name": "<short display label>",
        "method": "POST",
        "path": "/script/example",
        "handler": "module.Class.method",
        "summary": "What it does",
        "auth": {
          "required": true,
          "location": "header",
          "name": "Authorization",
          "secret_ref": "script.secret",
          "resolved_from": "annotation-default|config-file|env-var|apollo"
        },
        "parameters": [],
        "response": {
          "returns": "<void|Unit|ResponseType>",
          "data": "<null when the handler returns nothing; otherwise what the payload carries>"
        }
      }
    ]
  }
}
```

`name` is a short **display label only**, used as the item heading in the list. The user never types it: an interface is always addressed by its `key`, so `name` does not need to be unique and no disambiguation scheme is needed. Derive it from the source's Chinese `@ApiOperation` so the list reads well, and keep the full source description in `summary`.

`key` is the only handle the user needs: the stable number shown in the list and spoken as `<key> 号脚本`.

`auth` is settled **once, at discovery time**, and never asked of the user. Record whether auth is required, where the credential goes, and which property supplies it (`secret_ref`) — but never the credential's value, because a literal secret in `cache.json` would leak it into backups and shares. For `@Value("\${script.secret:youzan-pousheng}")` the entry is `{"required": true, "location": "header", "name": "Authorization", "secret_ref": "script.secret", "resolved_from": "annotation-default"}`; `resolved_from` names the layer that actually won. An interface whose handler checks nothing gets `{"required": false}`. Add a `note` when the resolution is only partially verified, so the next invocation knows what was and was not checked.

`labels` maps every field name used anywhere in this index to the business label the user actually speaks (`tid` → `订单号`, `refundId` → `有赞售后单号`). It is what lets an invocation sentence round-trip: the user says the label, the skill resolves the real field name. Take the label from the source's Swagger text (`@ApiModelProperty`) or the source comment when one exists; otherwise use a plain business name that does not contradict the source. Keep exactly one label per field name — when the same word would mean two different fields, choose distinct labels instead of relying on context.

`parameters` is grouped by location (`headers`, `body`, ...). Each leaf is a short string such as `"string, required"`. A leaf may instead be an object (`{"type": "string", "required": true, "example": "R123"}`) when an example value is worth keeping; the invocation sentence uses `example` when present and the literal `<值>` otherwise.

`response_envelope` describes how every interface in the project shapes its reply, and is what makes the outcome judgeable at all. Record the wrapper type, its fields, and — critically — the rule that decides success. When the project's global exception advice forces `@ResponseStatus(HttpStatus.OK)` onto failures, say so in `http_status`: it means the transport status and the process exit code carry **no** information, and only `success`/`code` may be used. Never leave a reader free to assume transport-level signals mean anything here.

`response` records what one interface actually hands back. A handler whose return type is `void`/`Unit` produces no business payload — record that, so the report says "only a processing result" instead of presenting an empty `data` as missing information. When the handler returns a type, record it, because that payload is the only way to verify what the call really did. Also record when a handler discards a meaningful internal return value (a `Boolean` the controller drops, for example): such an interface can report success while the business action never took effect.

Do not reuse keys across different project indexes for the same chat. When rediscovery changes the set, renumber the complete sorted list from 1 and tell the user that the keys were refreshed.

## Procedure

1. **Resolve the chat key.** Obtain the current group chat ID from the platform context or tool output. If only a display name is available, stop and ask for the stable chat ID; never silently use a name.
2. **Resolve the project path and controller root.** Confirm the project path exists with a shell command. Locate the controller directory directly, prioritizing conventional paths such as `<project>/youzan-pousheng-web/src/main/kotlin/**/controller`, `<project>/src/main/kotlin/**/controller`, and `<project>/src/main/java/**/controller`. Once found, scan only that controller directory and its descendants. Do not scan the whole repository or generated frontend/vendor/build directories. Preserve the user's project path exactly in reports.
3. **Scan controller mappings.** Search file contents under the controller root with a narrow include filter for `*.kt`, `*.java`, and relevant route metadata only. Search `RequestMapping`, `GetMapping`, `PostMapping`, `PutMapping`, `DeleteMapping`, and `PatchMapping`, then read only the matching controller files. Retain only mappings whose effective route is `/script` or begins with `/script/`; combine class-level and method-level mappings, including HTTP method annotations and path arrays. Record source file and line when available. If a project uses a configured global prefix, preserve the actual route and document the prefix.
4. **Determine the effective contract.** For every interface, identify HTTP method, complete path, handler, required/optional parameters, parameter location (path/query/header/body), types, defaults, enum constraints, and a safe example. Read DTOs, annotations, validators, route metadata, and nearby documentation as needed. Mark unknown fields as `unknown`; never infer them from parameter names alone. Settle authentication here too, once: does the handler check a credential, where must it be sent, and which property supplies it. Follow that reference down its chain (`@Value` default → `application.properties` / `.ENV` / `app.yaml` → environment variable → Apollo) and record the layer that wins in `auth.resolved_from`, plus a `note` if any layer could not be checked. Record the property name, never the secret value. Doing this at discovery is what lets invocation proceed without ever asking the user about auth. Determine the response shape in the same pass: the wrapper the project applies, the field rule that decides success, and what this particular handler returns. If the project pins failures to HTTP 200, record that verbatim rather than assuming a conventional status code. If the handler's own return value is discarded by the controller, record it — otherwise a success envelope will be over-read.
5. **Explain before calling, invocation sentence included.** Present a compact numbered list sorted by the stable `key`. For each item show method, path, purpose, required parameters, optional parameters, and an example input shape. Then close **every item** with a ready-to-send invocation sentence, so the user can trigger it by chatting instead of composing an HTTP request:

   ```text
   调用方式：你可以对我说「使用 <key> 号脚本，入参：<参数名>=<值>，环境 DEV/PROD」
   ```

   - `<key>` is the item's number — the only handle the user needs. Never make the user type a script name, and never accept one in place of a number.
   - `<参数名>` is the parameter's business label from `labels` — never the raw field name.
   - Include only parameters the caller supplies. Authentication was already settled in `auth` and is injected by the skill, so it must never appear in the `入参` clause and the user must never be asked about it.
   - List required parameters first, then optional parameters each wrapped in `[ ]`, e.g. `入参：有赞售后单号=R123，[事件时间=2026-09-18 12:00:00]`.
   - Take `<值>` from the parameter's `example` when the index has one; otherwise emit the literal placeholder `<值>`.
   - Always end with the environment clause, because routing differs per environment. Write the resolved value (`环境 DEV`) when the conversation already settles it; otherwise write `环境 DEV/PROD` so the user picks. Never drop the clause and never let the environment default silently.
   - For an interface with no parameters, emit `调用方式：你可以对我说「使用 <key> 号脚本，环境 DEV/PROD」` with no `入参` clause.
   - Keep it to one line and free of shell syntax — this is the line the user copies.

   Do not call anything during discovery unless the user explicitly requests execution.
6. **Persist the index.** Merge the complete sorted list into `cache.json` under the current chat ID by reading and writing that JSON file. Verify the written JSON can be parsed and that keys are unique and consecutive.
7. **Resolve the environment by selection, not mutation.** Take the environment from, in order: the `环境` clause of the invocation sentence, an explicit statement in the current turn, alert/context text (`DEV` = test, `PROD` = production). If none of these settles it, ask — never default, and never treat `selected_environment` as evidence, because that field only records the last resolved choice. Keep the `environments` array and each `environment`/`baseURL` pair fixed in the cache, then set only `selected_environment` to `DEV` or `PROD` for the current invocation and select the matching `baseURL`. For Youzan Pousheng, the fixed mappings are `PROD` → `https://youzan-pousheng.isv.youzan.com` and `DEV` → `https://youzan-pousheng.isv-dev.youzan.com`. Never infer production from silence; if the environment is still unknown, leave `selected_environment` as `unknown` and do not invoke.
8. **Resolve a call request.** Accept any of three forms: a numeric key, an exact path, or the invocation sentence from step 5 (`使用 <key> 号脚本，入参：<参数名>=<值>，环境 DEV|PROD`). For the sentence form, load the cache entry for the current chat and resolve each part against the index:
   - `<key>` → the interface with that key. Address interfaces by number only; do not resolve them by name and do not accept a name in place of a number. If the number is not in the index, list the current keys and ask.
   - `<参数名>` → the field name, by reverse lookup in `labels`. If one label maps to more than one field name, ask which one is meant.
   - `<值>` → the value for that field, converted to the type and format recorded in the index.
   - `环境` → the environment, resolved by step 7.

   Confirm the project path matches the requested context. If the key is absent or stale, rediscover before calling. If the user specifies a path instead, match it exactly against the current index; do not fuzzy-match silently. Ask for any required parameter the sentence omitted; never invent a value. Never ask about authentication.
9. **Validate call inputs.** Check all required arguments, types, enum values, path variables, body shape, and environment selection against the discovered contract, and check the resolved credential against `auth`. Ask only for missing information that cannot be obtained from context — authentication is never such information. Redact secrets in logs and feedback.
10. **Invoke the interface.** Use the project's documented command or HTTP invocation through the shell, with the resolved environment-specific base URL. When `auth.required` is true, resolve `auth.secret_ref` through its chain and inject `auth.name` silently — never echo the value into the report, the transcript, or a log line. Set the remaining fields explicitly. Do not use destructive or externally visible operations without the user's explicit request and any required confirmation. Capture exit code, stdout, stderr, HTTP status, and the response body — but treat only the envelope fields named by `response_envelope.success_when` as evidence, since `response_envelope.http_status` may pin the transport status to a success value even when the call failed.
11. **Report outcome.** State the selected key, method/path, and whether the call succeeded. Judge success **only** by `response_envelope.success_when` — never by the process exit code or the HTTP status. Then be precise about what that success proves: when `response.returns` is `void`/`Unit`, say plainly that the interface returns **only a processing result**, so a success envelope means the handler did not throw and nothing more. Do not present an empty `data` as missing information, and do not claim the business action took effect — especially when the handler discards its own return value. When the handler returns a type, report the fields that actually evidence the outcome. Always include the envelope's `code` and `message` on failure, any genuinely relevant payload, and a concise next step. Never claim success from a command that timed out, returned an ambiguous response, or was not verified.

## Quick Reference

- Discovery scope: controller directory only; effective route `/script` and `/script/*`.
- Discovery speed: narrow the content search by controller root and source file type; never repository-wide scan first.
- Key scope: stable per current group-chat ID and project index.
- Key ordering: complete discovered list, deterministic sort, then 1-based numbering.
- Invocation sentence: one line per item — `调用方式：你可以对我说「使用 <key> 号脚本，入参：<参数名>=<值>，环境 DEV/PROD」`; address by number, never by name, and take `<参数名>` from `labels`.
- Environment clause: always present in the sentence; write the resolved value, or `DEV/PROD` to make the user choose. Never let the environment default silently.
- Authentication: settled at discovery into `auth` and injected at invocation; never in the `入参` clause and never asked of the user.
- Response: judge the outcome only by `response_envelope.success_when`; when `http_status` pins failures to 200, neither the transport status nor the process exit code is evidence.
- Processing-result-only: when `response.returns` is `void`/`Unit` the envelope carries no business payload, so report "only a processing result" and never read an empty `data` as missing information.
- Label lookup: `labels` maps field name → business label; reverse it to turn what the user says back into the real field name.
- Environment: `DEV` → `https://youzan-pousheng.isv-dev.youzan.com`; `PROD` → `https://youzan-pousheng.isv.youzan.com` for Youzan Pousheng.
- Environment profiles: fixed `environment` + `baseURL` pairs for `PROD` and `DEV`; select by `selected_environment`.
- Cache: `<skills_dir>/script-interface-discovery/cache.json`, next to this `SKILL.md`.
- Evidence: source file/line for discovery; environment source; the response envelope's `code`/`success`/`message` for invocation — never the transport status alone.

## Sorting Rule

Sort interfaces deterministically by normalized path, then HTTP method, then handler name. Use this order for numeric keys. If the project explicitly declares an order and the user asks to preserve it, document that exception and use the declared order consistently for that index.

## Pitfalls

- A class mapping plus method mapping must be joined; scanning only method annotations produces wrong paths.
- Scan the controller directory first. Repository-wide search is a fallback only when the controller root cannot be located.
- `/api/script` is not `/script` unless the project explicitly configures `/api` as a removable global prefix; retain the actual runtime route and explain the prefix.
- Do not confuse `requestMapping` in comments, tests, or unrelated configuration with a live route; mark uncertain matches and exclude them from callable results.
- `DEV` and `PROD` are routing data, not descriptive labels. Never call an environment-specific endpoint until the environment is resolved from the invocation sentence's `环境` clause, the conversation, or an explicit instruction.
- Do not execute a handler merely to discover its purpose when source inspection is sufficient.
- A cached key is not proof that the endpoint still exists. Revalidate the source or route metadata when the project changes, the key is missing, or invocation fails with a route-not-found error.
- Preserve secrets and authentication headers; never write tokens or full secret-bearing payloads to the cache.
- `cache.json` holds chat identifiers and local project paths. It lives inside the installed skill directory and is overwritten by a reinstall; keep it out of unrelated backups or shares.
- A successful process exit is not an application success, and neither is an HTTP 200: when the global exception advice pins failures to 200, only the response envelope's `success`/`code` decide the outcome.
- Do not present an empty `data` as missing information. When `response.returns` is `void`/`Unit`, that emptiness is the contract itself — the call only yields a processing result.
- A success envelope is not proof that the business action took effect when the handler discards its own return value. State what the evidence covers and what it does not.
- The invocation sentence is a promise the skill can keep only if `labels` covers every parameter it names and `key` matches the index. Never print a raw field name (`tid`) in the sentence, and never reverse-map an ambiguous label without asking.
- Never address an interface by name. `name` is a display label and may repeat; the number is the contract.
- Never ask the user which endpoints need auth, and never ask for the credential. If an interface's `auth` is missing, that is a discovery gap: re-read the handler and fill it in.
- Never let the environment default, and never read `selected_environment` as evidence that the user chose it. A call without a resolved environment is an error, not a guess.
- When the source offers no Swagger text, say so rather than presenting an invented label as if it came from the source.

## Verification

Before reporting discovery complete, verify that every listed item came from the controller root, has an effective `/script` path, a unique consecutive key, and a source or route-metadata reference. Verify that every interface carries an `auth` entry, that no `auth` entry stores a credential value, that every parameter named in an invocation sentence has a `labels` entry, that each presented item carries exactly one `调用方式` line ending in an environment clause, and that no such line leaks a raw field name or a credential. Verify the cache is valid JSON, indexed by the exact current chat ID, contains the `labels` map, contains a `response_envelope` whose `success_when` and `http_status` are stated explicitly, carries a `response` entry for every interface, and contains fixed `environments` entries with `environment` and `baseURL`, plus `selected_environment`.

Before reporting a call complete, verify the invocation target matches the selected cache entry, the environment was resolved from the invocation sentence or an explicit instruction, the matching fixed `baseURL` was selected without editing the environment profiles, the credential came from `auth.secret_ref` and was never printed, the process finished without timeout, success or failure was decided by `response_envelope.success_when` rather than by exit code or transport status, the report states whether the interface returns a payload or only a processing result, and the quoted envelope supports the claim. If any check fails, report the uncertainty explicitly.
