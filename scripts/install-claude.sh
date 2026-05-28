#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/lib.sh"

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

install_skills_to "$CLAUDE_HOME/skills"
install_workflows_to "$CLAUDE_HOME/commands"

log_info "✅claude install completed"
