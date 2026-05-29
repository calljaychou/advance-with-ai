#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/skills" ] || [ -d "$SCRIPT_DIR/coding" ] || [ -d "$SCRIPT_DIR/spec" ]; then
    REPO_ROOT="$SCRIPT_DIR"
else
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

log_info() {
    printf '[advance-with-ai] %s\n' "$*"
}

log_error() {
    printf '[advance-with-ai] ERROR: %s\n' "$*" >&2
}

log_warn() {
    printf '[advance-with-ai] WARN: %s\n' "$*" >&2
}

die() {
    log_error "$*"
    exit 1
}

show_usage() {
    cat <<EOF
Usage:
  $0 <tools>

Tools:
  codex
  claude

Examples:
  $0 codex
  $0 claude
  $0 codex,claude
EOF
}

normalize_tools() {
    printf '%s' "$1" | sed 's/，/,/g' | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]'
}

validate_tool() {
    case "$1" in
        codex|claude)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

ensure_safe_target_path() {
    [ -n "$1" ] || die "target path cannot be empty"
    [ "$1" != "/" ] || die "target path cannot be root directory"
}

remove_path() {
    local target_path="$1"

    ensure_safe_target_path "$target_path"
    log_info "remove $target_path"

    if [ "${DRY_RUN:-0}" = "1" ]; then
        return 0
    fi

    rm -rf "$target_path"
}

remove_path_if_exists() {
    local target_path="$1"

    if [ -e "$target_path" ] || [ -L "$target_path" ]; then
        remove_path "$target_path"
        return 0
    fi

    return 1
}

log_items() {
    local item

    for item in "$@"; do
        log_info "  - $item"
    done
}

uninstall_skills_from() {
    local target_root="$1"
    local skill_dir
    local skill_name
    local removed_skills=()

    if [ ! -d "$REPO_ROOT/skills" ]; then
        log_warn "skills source directory does not exist, skip"
        return 0
    fi

    if [ -L "$target_root" ]; then
        remove_path "$target_root"
        log_info "✅ 已卸载 1 个 skills -> $target_root"
        log_items "$target_root"
        return 0
    fi

    for skill_dir in "$REPO_ROOT"/skills/*; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        [ "$skill_name" != "shared" ] || continue

        if remove_path_if_exists "$target_root/$skill_name"; then
            removed_skills+=("$skill_name")
        fi
    done

    log_info "✅ 已卸载 ${#removed_skills[@]} 个 skills -> $target_root"
    [ "${#removed_skills[@]}" -eq 0 ] || log_items "${removed_skills[@]}"
}

uninstall_workflows_from() {
    local target_root="$1"
    local workflow_dir
    local workflow_file
    local workflow_name
    local removed_workflows=()

    for workflow_dir in coding spec; do
        if [ -d "$REPO_ROOT/$workflow_dir" ]; then
            # 仅删除本仓库提供的 workflow 文件，避免影响用户自定义命令。
            while IFS= read -r -d '' workflow_file; do
                workflow_name="$(basename "$workflow_file")"
                [ "$workflow_name" != "README.md" ] || continue
                if remove_path_if_exists "$target_root/$workflow_name"; then
                    removed_workflows+=("$workflow_name")
                fi
            done < <(find "$REPO_ROOT/$workflow_dir" -maxdepth 1 -name "*.md" -type f -print0)
        fi
    done

    log_info "✅ 已卸载 ${#removed_workflows[@]} 个 workflows -> $target_root"
    [ "${#removed_workflows[@]}" -eq 0 ] || log_items "${removed_workflows[@]}"
}

uninstall_codex() {
    local codex_home="${CODEX_HOME:-$HOME/.codex}"

    uninstall_skills_from "$codex_home/skills"
    uninstall_workflows_from "$codex_home/prompts"
    log_info "✅ codex uninstall completed"
}

uninstall_claude() {
    local claude_home="${CLAUDE_HOME:-$HOME/.claude}"

    uninstall_skills_from "$claude_home/skills"
    uninstall_workflows_from "$claude_home/commands"
    log_info "✅ claude uninstall completed"
}

uninstall_tool() {
    case "$1" in
        codex)
            uninstall_codex
            ;;
        claude)
            uninstall_claude
            ;;
    esac
}

main() {
    local raw_tools="${1:-}"

    if [ -z "$raw_tools" ]; then
        show_usage
        exit 1
    fi

    local normalized_tools
    normalized_tools="$(normalize_tools "$raw_tools")"
    [ -n "$normalized_tools" ] || die "tools cannot be empty"

    local old_ifs="$IFS"
    local tools
    IFS=','
    read -r -a tools <<< "$normalized_tools"
    IFS="$old_ifs"

    local tool
    for tool in "${tools[@]}"; do
        [ -n "$tool" ] || continue
        validate_tool "$tool" || die "unsupported tool: $tool"
        uninstall_tool "$tool"
    done
}

main "$@"
