#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/lib.sh"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

uninstall_skills_from "$CLAUDE_HOME/skills"
uninstall_workflows_from "$CLAUDE_HOME/commands"

log_info "✅claude uninstall completed"
