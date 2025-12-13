#!/usr/bin/env bash
set -euo pipefail

# MCP servers registration script for user scope
# This script registers all MCP servers to Claude Code user scope

MCP_HOME="$(cd "$(dirname "$0")/.." && pwd)"

echo "Registering MCP servers from: $MCP_HOME"

# Example: Register openai-review server
# claude mcp add-json openai-review \
#   --scope user \
#   "{\"type\":\"stdio\",\"command\":\"python\",\"args\":[\"-m\",\"openai_review.server\"],\"env\":{\"MCP_HOME\":\"$MCP_HOME\"}}"

# Add your server registrations below:

echo "Done. All servers registered to user scope."
