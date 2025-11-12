#!/usr/bin/env bash
set -euo pipefail

# --- Config (override via env) ---
TOKEN_JSON="${FABRIC_TOKEN_JSON:-$HOME/work/id_token.json}"     # JSON with {"id_token": "..."}
#SYSTEM_MD="${FABRIC_SYSTEM_MD:-$PWD/system.md}"                 # Markdown file to use as system prompt
REMOTE_URL="${FABRIC_MCP_URL:-https://reports.fabric-testbed.net/mcp}"

# --- Read token (requires jq) ---
if ! command -v jq >/dev/null 2>&1; then
  echo "[!] jq is required (brew install jq)" >&2
  exit 1
fi
ID_TOKEN="$(jq -r '.id_token' "$TOKEN_JSON")"
if [[ -z "${ID_TOKEN}" || "${ID_TOKEN}" == "null" ]]; then
  echo "[!] Could not read .id_token from: $TOKEN_JSON" >&2
  exit 1
fi

# --- Load system prompt text from Markdown ---
#if [[ ! -f "$SYSTEM_MD" ]]; then
#  echo "[!] System prompt file not found: $SYSTEM_MD" >&2
#  exit 1
#fi
#SYSTEM_PROMPT="$(cat "$SYSTEM_MD")"

# --- Launch mcp-remote with header + system prompt ---
# Note: This relies on mcp-remote supporting --system.
# If your version doesn't, see the notes below for alternatives.
exec npx mcp-remote \
  "$REMOTE_URL" \
  --header "Authorization: Bearer ${ID_TOKEN}" #\
  #--system "$SYSTEM_PROMPT"
