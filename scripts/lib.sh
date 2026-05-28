#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

show_tools_usage() {
    cat <<EOF
Usage:
  $1 <tools>

Tools:
  codex
  claude

Examples:
  $1 codex
  $1 codex,claude
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

run_for_tools() {
    local action="$1"
    local raw_tools="${2:-}"

    if [ -z "$raw_tools" ]; then
        show_tools_usage "$SCRIPT_DIR/$action.sh"
        exit 1
    fi

    local normalized_tools
    normalized_tools="$(normalize_tools "$raw_tools")"
    [ -n "$normalized_tools" ] || die "tools cannot be empty"

    local old_ifs="$IFS"
    IFS=','
    read -r -a tools <<< "$normalized_tools"
    IFS="$old_ifs"

    local tool
    for tool in "${tools[@]}"; do
        [ -n "$tool" ] || continue
        validate_tool "$tool" || die "unsupported tool: $tool"
        "$SCRIPT_DIR/$action-$tool.sh"
    done
}

ensure_source_dir() {
    [ -d "$1" ] || die "source directory does not exist: $1"
}

ensure_safe_target_path() {
    [ -n "$1" ] || die "target path cannot be empty"
    [ "$1" != "/" ] || die "target path cannot be root directory"
}

copy_dir() {
    local source_dir="$1"
    local target_dir="$2"

    ensure_source_dir "$source_dir"
    ensure_safe_target_path "$target_dir"
    log_info "install $source_dir -> $target_dir"

    if [ "${DRY_RUN:-0}" = "1" ]; then
        return 0
    fi

    rm -rf "$target_dir"
    cp -R "$source_dir" "$target_dir"
    chmod -R a+r "$target_dir" 2>/dev/null || true
}

copy_file() {
    local source_file="$1"
    local target_file="$2"

    [ -f "$source_file" ] || die "source file does not exist: $source_file"
    ensure_safe_target_path "$target_file"
    log_info "install $source_file -> $target_file"

    if [ "${DRY_RUN:-0}" = "1" ]; then
        return 0
    fi

    rm -f "$target_file"
    cp -f "$source_file" "$target_file"
    chmod a+r "$target_file" 2>/dev/null || true
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

install_skills_to() {
    local target_root="$1"
    local skill_dir
    local skill_name
    local installed_skills=()

    if [ ! -d "$REPO_ROOT/skills" ]; then
        log_warn "skills source directory does not exist, skip"
        return 0
    fi
    if [ "${DRY_RUN:-0}" != "1" ]; then
        if [ -L "$target_root" ]; then
            rm "$target_root"
            log_info "remove legacy skills symlink: $target_root"
        fi
        mkdir -p "$target_root"
    fi

    for skill_dir in "$REPO_ROOT"/skills/*; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        [ "$skill_name" != "shared" ] || continue
        copy_dir "$skill_dir" "$target_root/$skill_name"
        installed_skills+=("$skill_name")

        if [ "${DRY_RUN:-0}" != "1" ] && [ -f "$target_root/$skill_name/skill.md" ] && [ ! -f "$target_root/$skill_name/SKILL.md" ]; then
            mv "$target_root/$skill_name/skill.md" "$target_root/$skill_name/SKILL.md"
        fi
    done

    log_info "✅已安装 ${#installed_skills[@]} 个 skills -> $target_root"
    [ "${#installed_skills[@]}" -eq 0 ] || log_items "${installed_skills[@]}"
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
        log_info "✅已卸载 1 个 skills -> $target_root"
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

    log_info "✅已卸载 ${#removed_skills[@]} 个 skills -> $target_root"
    [ "${#removed_skills[@]}" -eq 0 ] || log_items "${removed_skills[@]}"
}

install_workflows_to() {
    local target_root="$1"
    local workflow_dir
    local workflow_file
    local workflow_name
    local installed_workflows=()

    if [ "${DRY_RUN:-0}" != "1" ]; then
        mkdir -p "$target_root"
    fi

    for workflow_dir in coding spec; do
        if [ -d "$REPO_ROOT/$workflow_dir" ]; then
            # 与根目录 install.sh 保持一致：workflow 按文件名平铺到目标目录。
            while IFS= read -r -d '' workflow_file; do
                workflow_name="$(basename "$workflow_file")"
                [ "$workflow_name" != "README.md" ] || continue
                copy_file "$workflow_file" "$target_root/$workflow_name"
                installed_workflows+=("$workflow_name")
            done < <(find "$REPO_ROOT/$workflow_dir" -maxdepth 1 -name "*.md" -type f -print0)
        fi
    done

    log_info "✅已安装 ${#installed_workflows[@]} 个 workflows -> $target_root"
    [ "${#installed_workflows[@]}" -eq 0 ] || log_items "${installed_workflows[@]}"
}

uninstall_workflows_from() {
    local target_root="$1"
    local workflow_dir
    local workflow_file
    local workflow_name
    local removed_workflows=()

    for workflow_dir in coding spec; do
        if [ -d "$REPO_ROOT/$workflow_dir" ]; then
            while IFS= read -r -d '' workflow_file; do
                workflow_name="$(basename "$workflow_file")"
                [ "$workflow_name" != "README.md" ] || continue
                if remove_path_if_exists "$target_root/$workflow_name"; then
                    removed_workflows+=("$workflow_name")
                fi
            done < <(find "$REPO_ROOT/$workflow_dir" -maxdepth 1 -name "*.md" -type f -print0)
        fi
    done

    log_info "✅已卸载 ${#removed_workflows[@]} 个 workflows -> $target_root"
    [ "${#removed_workflows[@]}" -eq 0 ] || log_items "${removed_workflows[@]}"
}
