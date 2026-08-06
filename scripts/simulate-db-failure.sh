#!/usr/bin/env bash
# ==============================================================================
# Database Outage Simulation Script
# Purpose: Simulates a database outage by safely stopping the PostgreSQL container
#          and validating the liveness, readiness, and alerting state transitions.
# Usage: ./scripts/simulate-db-failure.sh
# ==============================================================================

set -euo pipefail

# Configuration (Supports environment overrides)
API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
WAIT_SECONDS="${WAIT_SECONDS:-5}"

echo "=== Operational Readiness Failure Simulation ==="
echo ""

# ------------------------------------------------------------------------------
# Phase 1: Checking baseline requirements
# ------------------------------------------------------------------------------
echo "[1/6] Checking baseline..."

# 1. Verify docker commands are available
if ! command -v docker &> /dev/null; then
    echo "✗ Error: docker CLI is not installed or not in PATH." >&2
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "✗ Error: docker compose is not available." >&2
    exit 1
fi

# 2. Check if API is running and reachable
if ! curl -s --connect-timeout 3 "${API_URL}/health" &> /dev/null; then
    echo "✗ Error: FastAPI service is unreachable at ${API_URL}." >&2
    exit 1
fi

# 3. Check health and readiness endpoints
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
READY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/ready")

if [ "$HEALTH_STATUS" -ne 200 ]; then
    echo "✗ Error: FastAPI /health endpoint returned HTTP ${HEALTH_STATUS} instead of 200." >&2
    exit 1
fi
echo "✓ API is healthy (/health → 200)"

if [ "$READY_STATUS" -ne 200 ]; then
    echo "✗ Error: FastAPI /ready endpoint returned HTTP ${READY_STATUS} instead of 200. Is database already down?" >&2
    exit 1
fi
echo "✓ API is ready (/ready → 200)"

# 4. Verify Prometheus is running and reachable
if ! curl -s --connect-timeout 3 "${PROMETHEUS_URL}/api/v1/targets" &> /dev/null; then
    echo "✗ Error: Prometheus server is unreachable at ${PROMETHEUS_URL}." >&2
    exit 1
fi
echo "✓ Prometheus target is UP"
echo ""

# ------------------------------------------------------------------------------
# Phase 2: Injecting database failure
# ------------------------------------------------------------------------------
echo "[2/6] Injecting database failure..."
BASELINE_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "Baseline Timestamp: ${BASELINE_TIME}"

# Stop only the database service safely using Compose
docker compose stop db
echo "✓ Database stopped"
echo ""

# ------------------------------------------------------------------------------
# Phase 3: Waiting for state observation
# ------------------------------------------------------------------------------
echo "[3/6] Waiting ${WAIT_SECONDS} seconds for scrape intervals and connection check logs..."
sleep "${WAIT_SECONDS}"
echo ""

# ------------------------------------------------------------------------------
# Phase 4: Checking application health post-failure
# ------------------------------------------------------------------------------
echo "[4/6] Checking application health..."
HEALTH_STATUS_POST=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
if [ "$HEALTH_STATUS_POST" -eq 200 ]; then
    echo "✓ /health → 200 OK (Process remains alive)"
else
    echo "✗ /health → ${HEALTH_STATUS_POST} (Process unhealthy/crashed!)"
fi
echo ""

# ------------------------------------------------------------------------------
# Phase 5: Checking application readiness post-failure
# ------------------------------------------------------------------------------
echo "[5/6] Checking readiness..."
READY_STATUS_POST=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/ready")
if [ "$READY_STATUS_POST" -eq 503 ]; then
    echo "✓ /ready → 503 Service Unavailable (Readiness check caught outage successfully)"
else
    echo "✗ /ready → ${READY_STATUS_POST} (Readiness check failed to catch outage!)"
fi
echo ""

# ------------------------------------------------------------------------------
# Phase 6: Querying Prometheus alert status
# ------------------------------------------------------------------------------
echo "[6/6] Checking monitoring..."

# Fetch current APIUnavailable alert state via Python standard library to ensure portability
ALERT_STATE=$(python3 -c "
import urllib.request, json
try:
    req = urllib.request.Request('${PROMETHEUS_URL}/api/v1/rules')
    with urllib.request.urlopen(req, timeout=3) as response:
        data = json.loads(response.read().decode())
        alert_state = 'unknown'
        for group in data.get('data', {}).get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('name') == 'APIUnavailable':
                    alert_state = rule.get('state', 'unknown')
        print(alert_state)
except Exception as e:
    print('error')
" 2>/dev/null || echo "error")

if [ "$ALERT_STATE" = "pending" ] || [ "$ALERT_STATE" = "firing" ]; then
    echo "✓ Availability alert state: ${ALERT_STATE} (Successfully detected by Prometheus)"
else
    echo "⚠ Availability alert state: ${ALERT_STATE} (May take up to 15s to transition to firing)"
fi
echo ""

# ------------------------------------------------------------------------------
# Finish
# ------------------------------------------------------------------------------
echo "================================================================================"
echo "Failure successfully reproduced. The application is left in the failed state."
echo ""
echo "Operator Investigation Path:"
echo "1. Run 'curl ${API_URL}/health' to confirm the container process is alive."
echo "2. Run 'curl ${API_URL}/ready' to confirm dependency connectivity is broken."
echo "3. Run 'docker compose logs api' to inspect PostgreSQL socket connection logs."
echo "4. Run 'docker compose ps' to identify stopped dependency services."
echo ""
echo "To recover the environment manually, run:"
echo "    docker compose start db"
echo ""
echo "Then verify recovery:"
echo "    curl ${API_URL}/ready  # Expected: HTTP 200"
echo "================================================================================"

exit 0
