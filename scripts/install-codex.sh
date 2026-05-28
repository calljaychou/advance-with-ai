#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "$SCRIPT_DIR/lib.sh"

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

install_skills_to "$CODEX_HOME/skills"
install_workflows_to "$CODEX_HOME/prompts"

log_info "✅codex install completed"
