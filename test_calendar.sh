#!/usr/bin/env bash
#
# Test script for Resource Availability Calendar feature
#
# Usage:
#   ./test_calendar.sh --reports-url https://beta-7.fabric-testbed.net:8443/reports \
#                      --orchestrator-url https://beta-7.fabric-testbed.net \
#                      --token <reports_bearer_token> \
#                      [--fabric-token <fabric_id_token>]
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
echo " Resource Calendar Test Suite"
echo "=========================================="
echo " Reports:      $REPORTS_URL"
echo " Orchestrator: $ORCH_URL"
echo "=========================================="
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 1: Fetch host data from orchestrator ---"
echo ""

SUMMARY_RESP=$(curl -sk -w "\n%{http_code}" "$ORCH_URL/portalresources/summary?type=hosts")
SUMMARY_STATUS=$(echo "$SUMMARY_RESP" | tail -1)
SUMMARY_BODY=$(echo "$SUMMARY_RESP" | sed '$d')

check_status "GET /portalresources/summary?type=hosts" "$SUMMARY_STATUS" "$SUMMARY_BODY"

# Extract hosts from summary
HOSTS_JSON=$(echo "$SUMMARY_BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
hosts = []
for item in data.get('data', []):
    if isinstance(item, dict) and 'hosts' in item:
        hosts = item['hosts']
        break
print(json.dumps(hosts))
" 2>/dev/null || echo "[]")

HOST_COUNT=$(echo "$HOSTS_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
log_info "Found $HOST_COUNT hosts in orchestrator summary"

# Grab first host/site for later queries
FIRST_HOST=$(echo "$HOSTS_JSON" | python3 -c "import sys,json; h=json.load(sys.stdin); print(h[0]['name'] if h else '')" 2>/dev/null)
FIRST_SITE=$(echo "$HOSTS_JSON" | python3 -c "import sys,json; h=json.load(sys.stdin); print(h[0]['site'] if h else '')" 2>/dev/null)
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 2: Query calendar - basic (3 days, daily) ---"
echo ""

START="2025-06-01T00:00:00+00:00"
END="2025-06-04T00:00:00+00:00"

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=day" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "GET /calendar (3 days, daily)" "$STATUS" "$BODY"

# Validate response structure
echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
total = data.get('total', 0)
interval = data.get('interval', '')
errors = []
if total != 3:
    errors.append(f'Expected 3 slots, got {total}')
if interval != 'day':
    errors.append(f'Expected interval=day, got {interval}')
for slot in slots:
    if 'hosts' not in slot or 'sites' not in slot:
        errors.append('Slot missing hosts or sites key')
        break
    for h in slot['hosts']:
        for key in ['cores_capacity', 'cores_allocated', 'cores_available', 'components']:
            if key not in h:
                errors.append(f'Host missing key: {key}')
                break
if errors:
    print('VALIDATION ERRORS: ' + '; '.join(errors))
    sys.exit(1)
else:
    print(f'OK: {total} slots, {len(slots[0][\"hosts\"])} hosts, {len(slots[0][\"sites\"])} sites per slot')
" 2>/dev/null && log_pass "Response structure validation" || log_fail "Response structure validation"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 3: Query calendar - weekly interval ---"
echo ""

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=2025-06-01T00:00:00+00:00&end_time=2025-06-30T00:00:00+00:00&interval=week" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "GET /calendar (weekly, June)" "$STATUS" "$BODY"

SLOT_COUNT=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null)
log_info "Got $SLOT_COUNT weekly slots"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 4: Query calendar - site filter ---"
echo ""

if [[ -n "$FIRST_SITE" ]]; then
    RESP=$(curl -sk -w "\n%{http_code}" \
        "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=day&site=$FIRST_SITE" \
        -H "Authorization: Bearer $TOKEN")
    STATUS=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')

    check_status "GET /calendar (site=$FIRST_SITE)" "$STATUS" "$BODY"

    echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
if slots:
    sites = set()
    for s in slots:
        for h in s['hosts']:
            sites.add(h['site'])
    print(f'Sites in response: {sites}')
    if len(sites) == 1 and '$FIRST_SITE' in sites:
        print('OK: Only $FIRST_SITE hosts returned')
    else:
        print(f'WARNING: Expected only $FIRST_SITE, got {sites}')
" 2>/dev/null
else
    log_skip "Site filter test (no hosts found)"
fi
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 5: Query calendar - exclude_site filter ---"
echo ""

if [[ -n "$FIRST_SITE" ]]; then
    RESP=$(curl -sk -w "\n%{http_code}" \
        "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=day&exclude_site=$FIRST_SITE" \
        -H "Authorization: Bearer $TOKEN")
    STATUS=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')

    check_status "GET /calendar (exclude_site=$FIRST_SITE)" "$STATUS" "$BODY"

    echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
if slots:
    sites = set()
    for s in slots:
        for h in s['hosts']:
            sites.add(h['site'])
    if '$FIRST_SITE' not in sites:
        print(f'OK: $FIRST_SITE excluded, got sites: {sites}')
    else:
        print(f'WARNING: $FIRST_SITE still present in response')
" 2>/dev/null
else
    log_skip "Exclude site filter test (no hosts found)"
fi
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 6: Query calendar - host filter ---"
echo ""

if [[ -n "$FIRST_HOST" ]]; then
    RESP=$(curl -sk -w "\n%{http_code}" \
        "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=day&host=$FIRST_HOST" \
        -H "Authorization: Bearer $TOKEN")
    STATUS=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')

    check_status "GET /calendar (host=$FIRST_HOST)" "$STATUS" "$BODY"

    HOST_IN_RESP=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
if slots:
    names = [h['name'] for h in slots[0]['hosts']]
    print(f'{len(names)} host(s): {names}')
" 2>/dev/null)
    log_info "$HOST_IN_RESP"
else
    log_skip "Host filter test (no hosts found)"
fi
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 7: Query calendar - with active slivers (current time range) ---"
echo ""

NOW=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
NEXT_WEEK=$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)+timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S+00:00'))")

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$NOW&end_time=$NEXT_WEEK&interval=day" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "GET /calendar (current week)" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
slots = data.get('data', [])
if not slots:
    print('  No slots returned')
else:
    total_alloc = 0
    for slot in slots:
        for h in slot.get('hosts', []):
            total_alloc += h.get('cores_allocated', 0)
    if total_alloc > 0:
        print(f'  Allocations detected: {total_alloc} total cores allocated across all slots')
        # Show first slot details
        s = slots[0]
        for h in s['hosts']:
            if h['cores_allocated'] > 0:
                print(f'    {h[\"name\"]} ({h[\"site\"]}): {h[\"cores_allocated\"]}/{h[\"cores_capacity\"]} cores, {h[\"ram_allocated\"]}/{h[\"ram_capacity\"]} RAM')
    else:
        print('  No active allocations found (expected if no slivers overlap this time range)')
" 2>/dev/null
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 8: Validation - bad requests ---"
echo ""

# Missing end_time
RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$START" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
check_status "GET /calendar missing end_time -> 400" "$STATUS" "" "400"

# start > end
RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=2025-06-04T00:00:00+00:00&end_time=2025-06-01T00:00:00+00:00" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
check_status "GET /calendar start > end -> 400" "$STATUS" "" "400"

# Invalid interval
RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$START&end_time=$END&interval=month" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
check_status "GET /calendar invalid interval -> 400" "$STATUS" "" "400"

# No auth
RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$START&end_time=$END")
STATUS=$(echo "$RESP" | tail -1)
check_status "GET /calendar no auth -> 401" "$STATUS" "" "401"
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 9: Orchestrator proxy ---"
echo ""

if [[ -n "$FABRIC_TOKEN" ]]; then
    RESP=$(curl -sk -w "\n%{http_code}" \
        "$ORCH_URL/resources/calendar?start_date=$START&end_date=$END&interval=day" \
        -H "Authorization: Bearer $FABRIC_TOKEN")
    STATUS=$(echo "$RESP" | tail -1)
    BODY=$(echo "$RESP" | sed '$d')

    check_status "GET /resources/calendar via orchestrator" "$STATUS" "$BODY"

    SLOT_COUNT=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Orchestrator wraps in Resources: {data: [{...calendar...}]}
for item in data.get('data', []):
    if isinstance(item, dict) and 'total' in item:
        print(item['total'])
        break
" 2>/dev/null || echo "?")
    log_info "Calendar returned $SLOT_COUNT slots via orchestrator proxy"
else
    log_skip "Orchestrator proxy test (no --fabric-token provided)"
fi
echo ""

# ─────────────────────────────────────────────────────────
echo "=========================================="
echo -e " Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}, ${YELLOW}${SKIP} skipped${NC}"
echo "=========================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
