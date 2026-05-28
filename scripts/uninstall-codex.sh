#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/lib.sh"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

uninstall_skills_from "$CODEX_HOME/skills"
uninstall_workflows_from "$CODEX_HOME/prompts"

log_info "✅codex uninstall completed"
