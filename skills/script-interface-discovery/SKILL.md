---
name: script-interface-discovery
description: Discover, explain, and call project HTTP interfaces whose request mapping lives under /script, keyed by the current chat. Use when the user provides a project path and asks to find, list, explain, or call script interfaces, or selects a previously listed interface by number in the same chat. Do not use for general REST API discovery outside the /script scope.
---

# Script Interface Discovery Skill

Discover project HTTP interfaces whose `requestMapping` path is under `/script`, explain their parameters, assign stable numeric keys per group chat, call a user-selected interface, and report the result. This skill does not invent endpoints or parameters; it relies on source inspection and the project's documented/runtime invocation contract.

## When to Use

- Use when the user provides a project path and asks to find, list, explain, or call script interfaces.
- Use when the user selects a previously listed interface by number in the same group chat.
- Use when the user replies with a previously offered invocation sentence (`使用<脚本名>，入参：<参数名>=<值>`).
- Do not use for arbitrary REST API discovery outside the `/script` path unless the user explicitly changes the scope.

## Prerequisites

- A readable project directory.
- Prefer the project's controller directory as the scan root. For the Youzan Pousheng project, use `youzan-pousheng-web/src/main/kotlin/com/youzan/cloud/youzan/pousheng/controller` rather than scanning the repository root.
- The controller source must contain `requestMapping` declarations or equivalent Spring route annotations.
- A callable project runtime, CLI, HTTP base URL, or documented invocation command must exist before execution. If none can be identified, report that discovery succeeded but invocation cannot be performed yet.
- Resolve the environment from the current chat context before invocation. Alert text containing `DEV` means test and `PROD` means production. If no environment is present, ask instead of choosing one.
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
    "interfaces": [
      {
        "key": 1,
        "name": "<short unique script name>",
        "method": "POST",
        "path": "/script/example",
        "handler": "module.Class.method",
        "summary": "What it does",
        "parameters": [],
        "invocation": {}
      }
    ]
  }
}
```

`name` is the short script name the user says out loud, and it must be unique within the index — uniqueness is what makes step 8's resolution unambiguous. Derive it from the source's Chinese `@ApiOperation`/`summary`, but shorten it and add a disambiguating suffix when two items share a prefix: `退单推送：买家仅退款` and `退单推送：买家退货退款` must become `退单推送-买家仅退款` and `退单推送-买家退货退款`, never both `退单推送`. Keep the long source description in `summary`; do not paste it into `name`.

`labels` maps every field name used anywhere in this index to the business label the user actually speaks (`tid` → `订单号`, `refundId` → `有赞售后单号`). It is what lets an invocation sentence round-trip: the user says the label, the skill resolves the real field name. Take the label from the source's Swagger text (`@ApiModelProperty`) or the source comment when one exists; otherwise use a plain business name that does not contradict the source. Keep exactly one label per field name — when the same word would mean two different fields, choose distinct labels instead of relying on context.

`parameters` is grouped by location (`headers`, `body`, ...). Each leaf is a short string such as `"string, required"`. A leaf may instead be an object (`{"type": "string", "required": true, "example": "R123"}`) when an example value is worth keeping; the invocation sentence uses `example` when present and the literal `<值>` otherwise.

Do not reuse keys across different project indexes for the same chat. When rediscovery changes the set, renumber the complete sorted list from 1 and tell the user that the keys were refreshed.

## Procedure

1. **Resolve the chat key.** Obtain the current group chat ID from the platform context or tool output. If only a display name is available, stop and ask for the stable chat ID; never silently use a name.
2. **Resolve the project path and controller root.** Confirm the project path exists with a shell command. Locate the controller directory directly, prioritizing conventional paths such as `<project>/youzan-pousheng-web/src/main/kotlin/**/controller`, `<project>/src/main/kotlin/**/controller`, and `<project>/src/main/java/**/controller`. Once found, scan only that controller directory and its descendants. Do not scan the whole repository or generated frontend/vendor/build directories. Preserve the user's project path exactly in reports.
3. **Scan controller mappings.** Search file contents under the controller root with a narrow include filter for `*.kt`, `*.java`, and relevant route metadata only. Search `RequestMapping`, `GetMapping`, `PostMapping`, `PutMapping`, `DeleteMapping`, and `PatchMapping`, then read only the matching controller files. Retain only mappings whose effective route is `/script` or begins with `/script/`; combine class-level and method-level mappings, including HTTP method annotations and path arrays. Record source file and line when available. If a project uses a configured global prefix, preserve the actual route and document the prefix.
4. **Determine the effective contract.** For every interface, identify HTTP method, complete path, handler, required/optional parameters, parameter location (path/query/header/body), types, defaults, enum constraints, and a safe example. Read DTOs, annotations, validators, route metadata, and nearby documentation as needed. Mark unknown fields as `unknown`; never infer them from parameter names alone.
5. **Explain before calling, invocation sentence included.** Present a compact numbered list sorted by the stable `key`. For each item show method, path, purpose, required parameters, optional parameters, and an example input shape. Then close **every item** with a ready-to-send invocation sentence, so the user can trigger it by chatting instead of composing an HTTP request:

   ```text
   调用方式：你可以对我说「使用<脚本名>脚本，入参：<参数名>=<值>」
   ```

   - `<脚本名>` is the item's `name`: short and unique within the index. Never substitute the raw `summary` when the summary carries a long description or shares a prefix with another item. If an item has no `name`, emit `#<key>` instead of a possibly ambiguous summary.
   - `<参数名>` is the parameter's business label from `labels` — never the raw field name.
   - Include only parameters the caller actually supplies. Authentication headers such as `Authorization` are injected by the skill from configuration, so they belong in the item's parameter list but must never appear in the `入参` clause.
   - List required parameters first, then optional parameters each wrapped in `[ ]`, e.g. `入参：有赞售后单号=R123，[事件时间=2026-09-18 12:00:00]`.
   - Take `<值>` from the parameter's `example` when the index has one; otherwise emit the literal placeholder `<值>`.
   - For an interface with no parameters, emit `调用方式：你可以对我说「使用<脚本名>脚本」` with no `入参` clause.
   - Keep it to one line and free of shell syntax — this is the line the user copies.

   Do not call anything during discovery unless the user explicitly requests execution.
6. **Persist the index.** Merge the complete sorted list into `cache.json` under the current chat ID by reading and writing that JSON file. Verify the written JSON can be parsed and that keys are unique and consecutive.
7. **Resolve the environment by selection, not mutation.** Keep the `environments` array and each `environment`/`baseURL` pair fixed in the cache. Inspect the current conversation and the alert/context that prompted the call, then set only `selected_environment` to `DEV` or `PROD` for the current invocation. Select the matching object from `environments` to obtain `baseURL`. For Youzan Pousheng, the fixed mappings are `PROD` → `https://youzan-pousheng.isv.youzan.com` and `DEV` → `https://youzan-pousheng.isv-dev.youzan.com`. Do not infer production from silence. If no environment is known, leave `selected_environment` as `unknown` and do not invoke.
8. **Resolve a call request.** Accept any of three forms: a numeric key, an exact path, or the invocation sentence from step 5 (`使用<脚本名>，入参：<参数名>=<值>`). For the sentence form, load the cache entry for the current chat and resolve each part against the index:
   - `<脚本名>` → the interface whose `name` matches exactly, after trimming a trailing `脚本`. If it matches zero interfaces, or more than one, list the candidates with their keys and ask; never guess.
   - `<参数名>` → the field name, by reverse lookup in `labels`. If one label maps to more than one field name, ask which one is meant.
   - `<值>` → the value for that field, converted to the type and format recorded in the index.

   Confirm the project path and environment match the requested context. If the key is absent or stale, rediscover before calling. If the user specifies a path instead, match it exactly against the current index; do not fuzzy-match silently. Ask for any required parameter the sentence omitted; never invent a value.
9. **Validate call inputs.** Check all required arguments, types, enum values, path variables, body shape, authentication requirements, and environment selection against the discovered contract. Ask only for missing information that cannot be obtained from context. Redact secrets in logs and feedback.
10. **Invoke the interface.** Use the project's documented command or HTTP invocation through the shell, with the resolved environment-specific base URL. Set fields explicitly. Do not use destructive or externally visible operations without the user's explicit request and any required confirmation. Capture exit code, stdout, stderr, HTTP status, and response body.
11. **Report outcome.** State the selected key, method/path, and whether the call succeeded. Define success from the actual contract: normally exit code 0 plus a successful HTTP status and/or explicit response success field. Include the relevant returned data, error message, and a concise next step. Never claim success from a command that timed out, returned an ambiguous response, or was not verified.

## Quick Reference

- Discovery scope: controller directory only; effective route `/script` and `/script/*`.
- Discovery speed: narrow the content search by controller root and source file type; never repository-wide scan first.
- Key scope: stable per current group-chat ID and project index.
- Key ordering: complete discovered list, deterministic sort, then 1-based numbering.
- Invocation sentence: one line per item — `调用方式：你可以对我说「使用<脚本名>脚本，入参：<参数名>=<值>」`; `<脚本名>` is the item's unique `name`, and `<参数名>` comes from `labels`, never from `parameters`.
- Script name: short and unique per index; never the raw `summary`, which can share a prefix across items or carry a long description.
- Label lookup: `labels` maps field name → business label; reverse it to turn what the user says back into the real field name.
- Environment: `DEV` → `https://youzan-pousheng.isv-dev.youzan.com`; `PROD` → `https://youzan-pousheng.isv.youzan.com` for Youzan Pousheng.
- Environment profiles: fixed `environment` + `baseURL` pairs for `PROD` and `DEV`; select by `selected_environment`.
- Cache: `<skills_dir>/script-interface-discovery/cache.json`, next to this `SKILL.md`.
- Evidence: source file/line for discovery; environment source; exit code/status/body for invocation.

## Sorting Rule

Sort interfaces deterministically by normalized path, then HTTP method, then handler name. Use this order for numeric keys. If the project explicitly declares an order and the user asks to preserve it, document that exception and use the declared order consistently for that index.

## Pitfalls

- A class mapping plus method mapping must be joined; scanning only method annotations produces wrong paths.
- Scan the controller directory first. Repository-wide search is a fallback only when the controller root cannot be located.
- `/api/script` is not `/script` unless the project explicitly configures `/api` as a removable global prefix; retain the actual runtime route and explain the prefix.
- Do not confuse `requestMapping` in comments, tests, or unrelated configuration with a live route; mark uncertain matches and exclude them from callable results.
- `DEV` and `PROD` are routing data, not descriptive labels. Never call an environment-specific endpoint until the environment is resolved from the conversation or explicitly supplied.
- Do not execute a handler merely to discover its purpose when source inspection is sufficient.
- A cached key is not proof that the endpoint still exists. Revalidate the source or route metadata when the project changes, the key is missing, or invocation fails with a route-not-found error.
- Preserve secrets and authentication headers; never write tokens or full secret-bearing payloads to the cache.
- `cache.json` holds chat identifiers and local project paths. It lives inside the installed skill directory and is overwritten by a reinstall; keep it out of unrelated backups or shares.
- A successful process exit is not necessarily an application success. Inspect HTTP status and the response's success/error fields.
- The invocation sentence is a promise the skill can keep only if `labels` covers every parameter it names and `name` is unique across the index. Never print a raw field name (`tid`) in the sentence, and never reverse-map an ambiguous label or script name without asking.
- When the source offers no Swagger text, say so rather than presenting an invented label as if it came from the source.

## Verification

Before reporting discovery complete, verify that every listed item came from the controller root, has an effective `/script` path, a unique consecutive key, and a source or route-metadata reference. Verify that every parameter named in an invocation sentence has a `labels` entry, that each presented item carries exactly one `调用方式` line, and that no such line leaks a raw field name. Verify the cache is valid JSON, indexed by the exact current chat ID, contains the `labels` map, every `name` is present and unique, and contains fixed `environments` entries with `environment` and `baseURL`, plus `selected_environment`.

Before reporting a call complete, verify the invocation target matches the selected cache entry, `selected_environment` was explicitly resolved, the matching fixed `baseURL` was selected without editing the environment profiles, the process finished without timeout, and the returned status/body supports the success or failure claim. If any check fails, report the uncertainty explicitly.
