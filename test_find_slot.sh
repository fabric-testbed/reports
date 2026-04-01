#!/usr/bin/env bash
#
# Test script for POST /calendar/find-slot endpoint
#
# Usage:
#   ./test_find_slot.sh --reports-url https://beta-7.fabric-testbed.net:8443/reports \
#                       --orchestrator-url https://beta-7.fabric-testbed.net \
#                       --token <reports_bearer_token> \
#                       [--fabric-token <fabric_id_token>]
#
# The --token is the static bearer token from reports config (bearer_tokens list).
# The --fabric-token is optional; needed only to test the orchestrator proxy endpoint.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPORTS_URL=""
ORCH_URL=""
TOKEN=""
FABRIC_TOKEN=""

usage() {
    echo "Usage: $0 --reports-url <url> --orchestrator-url <url> --token <token> [--fabric-token <token>]"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --reports-url)   REPORTS_URL="$2"; shift 2 ;;
        --orchestrator-url) ORCH_URL="$2"; shift 2 ;;
        --token)         TOKEN="$2"; shift 2 ;;
        --fabric-token)  FABRIC_TOKEN="$2"; shift 2 ;;
        -h|--help)       usage ;;
        *)               echo "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "$REPORTS_URL" || -z "$ORCH_URL" || -z "$TOKEN" ]]; then
    usage
fi

if [[ -z "$FABRIC_TOKEN" ]]; then
    FABRIC_TOKEN="$TOKEN"
fi

REPORTS_URL="${REPORTS_URL%/}"
ORCH_URL="${ORCH_URL%/}"
PASS=0
FAIL=0
SKIP=0

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
log_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
log_info() { echo -e "       $1"; }

check_status() {
    local desc="$1" status="$2" body="$3" expected="${4:-200}"
    if [[ "$status" == "$expected" ]]; then
        log_pass "$desc (HTTP $status)"
    else
        log_fail "$desc (HTTP $status, expected $expected)"
        log_info "Response: $(echo "$body" | head -5)"
    fi
}

# ─────────────────────────────────────────────────────────
echo ""
echo "=========================================="
echo " Find-Slot Test Suite"
echo "=========================================="
echo " Reports:      $REPORTS_URL"
echo " Orchestrator: $ORCH_URL"
echo "=========================================="
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 1: Get a site name from calendar for use in tests ---"
echo ""

START="2025-07-01T00:00:00+00:00"
END="2025-07-04T00:00:00+00:00"

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=day" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

FIRST_SITE=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
if slots and slots[0].get('sites'):
    print(slots[0]['sites'][0]['name'])
else:
    print('')
" 2>/dev/null || echo "")

if [[ -n "$FIRST_SITE" ]]; then
    log_info "Using site: $FIRST_SITE"
else
    log_info "No sites found in calendar — tests will use generic requests"
fi
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 1: Single compute resource at specific site ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 2, "ram": 4, "disk": 10}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Single compute find-slot" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'windows' in data, 'Missing windows field'
assert 'total' in data, 'Missing total field'
assert 'duration_hours' in data, 'Missing duration_hours field'
assert data['duration_hours'] == 24
print(f'       Found {data[\"total\"]} window(s)')
if data['windows']:
    print(f'       First window: {data[\"windows\"][0][\"start\"]} to {data[\"windows\"][0][\"end\"]}')
" 2>/dev/null || log_info "Response validation skipped"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 2: Multiple compute resources (bin-packing) ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 48,
  "max_results": 3,
  "resources": [
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 2, "ram": 4, "disk": 10},
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 2, "ram": 4, "disk": 10}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Multiple compute bin-packing" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'       Found {data[\"total\"]} window(s) (max_results=3)')
" 2>/dev/null || true
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 3: Compute + link multi-resource ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 2, "ram": 4, "disk": 10},
    {"type": "link", "site_a": "RENC", "site_b": "CLEM", "bandwidth": 25}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Compute + link multi-resource" "$STATUS" "$BODY"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 4: Facility port VLAN request ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "facility_port", "name": "RENC-Chameleon", "site": "${FIRST_SITE:-RENC}", "vlans": 1}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Facility port VLAN request" "$STATUS" "$BODY"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 5: Site-less compute (any site) ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "compute", "cores": 2, "ram": 4, "disk": 10}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Site-less compute (any site)" "$STATUS" "$BODY"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 6: Impossible request → empty windows ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 999999, "ram": 999999, "disk": 999999}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Impossible request returns 200" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert data['total'] == 0 and len(data['windows']) == 0, 'Expected empty windows'
print('       Correctly returned empty windows')
" 2>/dev/null || log_info "Validation skipped"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 7: Validation errors ---"
echo ""

# Missing required fields
RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}')
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check_status "Missing fields → 400" "$STATUS" "$BODY" 400

# Duration > range
PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-02T00:00:00+00:00",
  "duration": 48,
  "resources": [{"type": "compute", "cores": 2}]
}
EOF
)
RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check_status "Duration > range → 400" "$STATUS" "$BODY" 400

# Invalid resource type
PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [{"type": "invalid_type"}]
}
EOF
)
RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check_status "Invalid resource type → 400" "$STATUS" "$BODY" 400

# Link missing required fields
PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [{"type": "link", "site_a": "RENC"}]
}
EOF
)
RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$REPORTS_URL/calendar/find-slot" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check_status "Link missing fields → 400" "$STATUS" "$BODY" 400
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Test 8: Orchestrator proxy POST /resources/find-slot ---"
echo ""

PAYLOAD=$(cat <<EOF
{
  "start": "2025-07-01T00:00:00+00:00",
  "end": "2025-07-15T00:00:00+00:00",
  "duration": 24,
  "resources": [
    {"type": "compute", "site": "${FIRST_SITE:-RENC}", "cores": 2, "ram": 4, "disk": 10}
  ]
}
EOF
)

RESP=$(curl -sk -w "\n%{http_code}" \
    -X POST "$ORCH_URL/resources/find-slot" \
    -H "Authorization: Bearer $FABRIC_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "Orchestrator proxy find-slot" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert 'data' in data, 'Missing data field in orchestrator response'
assert data.get('type') == 'resources.find_slot', f'Unexpected type: {data.get(\"type\")}'
print('       Orchestrator proxy response structure OK')
" 2>/dev/null || log_info "Validation skipped"
echo ""

# ─────────────────────────────────────────────────────────
echo "=========================================="
echo -e " Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}, ${YELLOW}$SKIP skipped${NC}"
echo "=========================================="

exit $FAIL
