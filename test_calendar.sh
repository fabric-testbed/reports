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

# Default fabric-token to token if not provided separately
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
for slot in slots:
    for lk in slot.get('links', []):
        for key in ['bandwidth_capacity', 'bandwidth_allocated', 'bandwidth_available']:
            if key not in lk:
                errors.append(f'Link missing key: {key}')
                break
    for fp in slot.get('facility_ports', []):
        for key in ['total_vlans', 'vlans_allocated', 'vlans_available']:
            if key not in fp:
                errors.append(f'Facility port missing key: {key}')
                break
        if not isinstance(fp.get('vlans_allocated'), list):
            errors.append(f'vlans_allocated should be a list, got {type(fp.get(\"vlans_allocated\")).__name__}')
            break
        if not isinstance(fp.get('vlans_available'), str):
            errors.append(f'vlans_available should be a string, got {type(fp.get(\"vlans_available\")).__name__}')
            break
if errors:
    print('VALIDATION ERRORS: ' + '; '.join(errors))
    sys.exit(1)
else:
    links_count = len(slots[0].get('links', []))
    fps_count = len(slots[0].get('facility_ports', []))
    print(f'OK: {total} slots, {len(slots[0][\"hosts\"])} hosts, {len(slots[0][\"sites\"])} sites, {links_count} links, {fps_count} facility ports per slot')
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
echo "--- Step 3b: Query calendar - hourly interval (single day) ---"
echo ""

HOUR_START="2025-06-01T00:00:00+00:00"
HOUR_END="2025-06-02T00:00:00+00:00"

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$HOUR_START&end_time=$HOUR_END&interval=hour" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "GET /calendar (hourly, 1 day)" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('total', 0)
interval = data.get('interval', '')
errors = []
if total != 24:
    errors.append(f'Expected 24 hourly slots, got {total}')
if interval != 'hour':
    errors.append(f'Expected interval=hour, got {interval}')
if errors:
    print('VALIDATION ERRORS: ' + '; '.join(errors))
    sys.exit(1)
else:
    print(f'OK: {total} hourly slots')
" 2>/dev/null && log_pass "Hourly interval validation (24 slots)" || log_fail "Hourly interval validation"
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
echo "--- Step 8: Display resource availability calendar ---"
echo ""

CAL_START=$(date -u +%Y-%m-%dT00:00:00%z)
CAL_END=$(python3 -c "from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)+timedelta(days=14)).strftime('%Y-%m-%dT00:00:00+00:00'))")

RESP=$(curl -sk -w "\n%{http_code}" \
    "$REPORTS_URL/calendar?start_time=$CAL_START&end_time=$CAL_END&interval=day" \
    -H "Authorization: Bearer $TOKEN")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')

check_status "GET /calendar (next 14 days)" "$STATUS" "$BODY"

echo "$BODY" | python3 -c "
import sys, json
from collections import defaultdict

data = json.load(sys.stdin)
slots = data.get('data', [])
if not slots:
    print('  No calendar data available')
    sys.exit(0)

dates = [slot['start'][:10] for slot in slots]
date_hdrs = [d[5:] for d in dates]  # MM-DD

# Collect all sites and component types
all_sites = set()
all_comp_types = set()
for slot in slots:
    for s in slot.get('sites', []):
        all_sites.add(s['name'])
    for h in slot.get('hosts', []):
        for comp_name, comp_data in h.get('components', {}).items():
            if isinstance(comp_data, dict) and comp_data.get('capacity', 0) > 0:
                all_comp_types.add(comp_name)

W = 9  # column width

# ── CORES: Site-level availability ──
print()
print('┌─────────────────────────────────────────────────────────────────────────────────────┐')
print('│                     Cores Available / Capacity  (by Site, per Day)                  │')
print('├─────────────────────────────────────────────────────────────────────────────────────┤')
hdr = f'  {\"Site\":<12}' + ''.join(f' {d:>{W}}' for d in date_hdrs)
print(hdr)
print('  ' + '─' * (12 + len(dates) * (W+1)))

for site_name in sorted(all_sites):
    row = f'  {site_name:<12}'
    for slot in slots:
        site_data = next((s for s in slot.get('sites', []) if s['name'] == site_name), None)
        if site_data:
            avail = site_data.get('cores_available', 0)
            cap = site_data.get('cores_capacity', 0)
            cell = f'{avail}/{cap}'
            row += f' {cell:>{W}}'
        else:
            row += f' {\"─\":>{W}}'
    print(row)
print()

# ── RAM: Site-level availability ──
print('┌─────────────────────────────────────────────────────────────────────────────────────┐')
print('│                    RAM Available / Capacity GB  (by Site, per Day)                  │')
print('├─────────────────────────────────────────────────────────────────────────────────────┤')
hdr = f'  {\"Site\":<12}' + ''.join(f' {d:>{W}}' for d in date_hdrs)
print(hdr)
print('  ' + '─' * (12 + len(dates) * (W+1)))

for site_name in sorted(all_sites):
    row = f'  {site_name:<12}'
    for slot in slots:
        site_data = next((s for s in slot.get('sites', []) if s['name'] == site_name), None)
        if site_data:
            avail = site_data.get('ram_available', 0)
            cap = site_data.get('ram_capacity', 0)
            cell = f'{avail}/{cap}'
            row += f' {cell:>{W}}'
        else:
            row += f' {\"─\":>{W}}'
    print(row)
print()

# ── COMPONENTS: Per component type, per site, per day ──
# Group component types (e.g. all GPUs together, all SmartNICs together)
gpu_types = sorted(t for t in all_comp_types if 'GPU' in t.upper())
nic_types = sorted(t for t in all_comp_types if 'NIC' in t.upper() or 'ConnectX' in t)
fpga_types = sorted(t for t in all_comp_types if 'FPGA' in t.upper())
nvme_types = sorted(t for t in all_comp_types if 'NVME' in t.upper() or 'NVMe' in t)
other_types = sorted(t for t in all_comp_types if t not in gpu_types + nic_types + fpga_types + nvme_types)

def print_component_table(comp_types, title):
    if not comp_types:
        return
    print(f'┌─────────────────────────────────────────────────────────────────────────────────────┐')
    print(f'│  {title:<83}│')
    print(f'├─────────────────────────────────────────────────────────────────────────────────────┤')

    for comp_type in comp_types:
        # Aggregate by site: for each site+slot, sum available/capacity across hosts
        site_comp = {}  # site -> list of (avail, cap) per slot
        for site_name in sorted(all_sites):
            site_comp[site_name] = []
            for slot in slots:
                total_avail = 0
                total_cap = 0
                for h in slot.get('hosts', []):
                    if h.get('site') != site_name:
                        continue
                    cd = h.get('components', {}).get(comp_type)
                    if isinstance(cd, dict):
                        total_cap += cd.get('capacity', 0)
                        total_avail += cd.get('available', 0)
                site_comp[site_name].append((total_avail, total_cap))

        # Only show sites that have this component
        sites_with_comp = [s for s in sorted(all_sites) if any(c[1] > 0 for c in site_comp[s])]
        if not sites_with_comp:
            continue

        short_name = comp_type
        if len(short_name) > 30:
            short_name = short_name[:28] + '..'
        print(f'  {short_name}')

        hdr = f'    {\"Site\":<10}' + ''.join(f' {d:>{W}}' for d in date_hdrs)
        print(hdr)
        print('    ' + '─' * (10 + len(dates) * (W+1)))

        for site_name in sites_with_comp:
            row = f'    {site_name:<10}'
            for avail, cap in site_comp[site_name]:
                if cap > 0:
                    cell = f'{avail}/{cap}'
                    row += f' {cell:>{W}}'
                else:
                    row += f' {\"─\":>{W}}'
            print(row)
        print()

print_component_table(gpu_types, 'GPU Available / Capacity  (by Site, per Day)')
print_component_table(nic_types, 'SmartNIC Available / Capacity  (by Site, per Day)')
print_component_table(fpga_types, 'FPGA Available / Capacity  (by Site, per Day)')
print_component_table(nvme_types, 'NVMe Available / Capacity  (by Site, per Day)')
print_component_table(other_types, 'Other Components Available / Capacity  (by Site, per Day)')

# ── Per-host GPU detail ──
if gpu_types:
    print('┌─────────────────────────────────────────────────────────────────────────────────────┐')
    print('│                    GPU Detail by Host  (available / capacity)                       │')
    print('├─────────────────────────────────────────────────────────────────────────────────────┤')

    for comp_type in gpu_types:
        short_name = comp_type if len(comp_type) <= 30 else comp_type[:28] + '..'
        print(f'  {short_name}')
        hdr = f'    {\"Host\":<35} {\"Site\":<6}' + ''.join(f' {d:>{W}}' for d in date_hdrs)
        print(hdr)
        print('    ' + '─' * (35 + 6 + len(dates) * (W+1)))

        # Find hosts that have this GPU
        hosts_with_gpu = set()
        for slot in slots:
            for h in slot.get('hosts', []):
                cd = h.get('components', {}).get(comp_type)
                if isinstance(cd, dict) and cd.get('capacity', 0) > 0:
                    hosts_with_gpu.add((h['name'], h.get('site', '')))

        for host_name, site_name in sorted(hosts_with_gpu, key=lambda x: (x[1], x[0])):
            row = f'    {host_name:<35} {site_name:<6}'
            for slot in slots:
                host_data = next((h for h in slot.get('hosts', []) if h['name'] == host_name), None)
                if host_data:
                    cd = host_data.get('components', {}).get(comp_type, {})
                    if isinstance(cd, dict) and cd.get('capacity', 0) > 0:
                        avail = cd.get('available', 0)
                        cap = cd.get('capacity', 0)
                        cell = f'{avail}/{cap}'
                        # highlight fully available
                        row += f' {cell:>{W}}'
                    else:
                        row += f' {\"─\":>{W}}'
                else:
                    row += f' {\"─\":>{W}}'
            print(row)
        print()

print('└─────────────────────────────────────────────────────────────────────────────────────┘')

# ── LINKS: Bandwidth availability ──
all_links = {}
for slot in slots:
    for lk in slot.get('links', []):
        all_links[lk['name']] = lk
if all_links:
    print()
    print('┌─────────────────────────────────────────────────────────────────────────────────────┐')
    print('│               Link Bandwidth Available / Capacity Gbps  (per Day)                   │')
    print('├─────────────────────────────────────────────────────────────────────────────────────┤')
    hdr = f'  {\"Link\":<20}' + ''.join(f' {d:>{W}}' for d in date_hdrs)
    print(hdr)
    print('  ' + '─' * (20 + len(dates) * (W+1)))
    for link_name in sorted(all_links.keys()):
        row = f'  {link_name:<20}'
        for slot in slots:
            lk_data = next((l for l in slot.get('links', []) if l['name'] == link_name), None)
            if lk_data:
                avail = lk_data.get('bandwidth_available', 0)
                cap = lk_data.get('bandwidth_capacity', 0)
                cell = f'{avail}/{cap}'
                row += f' {cell:>{W}}'
            else:
                row += f' {\"─\":>{W}}'
        print(row)
    print()

# ── FACILITY PORTS: VLAN availability (per port) ──
all_fps = {}
for slot in slots:
    for fp in slot.get('facility_ports', []):
        key = (fp['name'], fp.get('site', ''), fp.get('device_name', ''), fp.get('local_name', ''))
        all_fps[key] = fp
if all_fps:
    print('┌──────────────────────────────────────────────────────────────────────────────────────────────────┐')
    print('│              Facility Port VLANs  (per Port, per Day)                                            │')
    print('├──────────────────────────────────────────────────────────────────────────────────────────────────┤')
    for (fp_name, fp_site, fp_dev, fp_port) in sorted(all_fps.keys()):
        label = f'{fp_name} ({fp_site})'
        port_label = fp_port if len(fp_port) <= 21 else fp_port[:19] + '..'
        print(f'  {label}  port={port_label}  range={all_fps[(fp_name, fp_site, fp_dev, fp_port)].get(\"vlan_range\", \"\")}')
        for i, slot in enumerate(slots):
            fp_data = next((f for f in slot.get('facility_ports', [])
                           if f['name'] == fp_name and f.get('site', '') == fp_site
                           and f.get('device_name', '') == fp_dev and f.get('local_name', '') == fp_port), None)
            if fp_data:
                alloc_list = fp_data.get('vlans_allocated', [])
                avail_range = fp_data.get('vlans_available', '')
                alloc_count = len(alloc_list)
                total = fp_data.get('total_vlans', 0)
                avail_display = avail_range if len(avail_range) <= 60 else avail_range[:57] + '...'
                print(f'    {date_hdrs[i]}  allocated={alloc_count}/{total}  available={avail_display}')
            else:
                print(f'    {date_hdrs[i]}  ─')
    print()

print('└─────────────────────────────────────────────────────────────────────────────────────┘')
" 2>/dev/null
echo ""

# ─────────────────────────────────────────────────────────
echo "--- Step 9: Validation - bad requests ---"

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
echo "--- Step 10: Orchestrator proxy ---"
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
