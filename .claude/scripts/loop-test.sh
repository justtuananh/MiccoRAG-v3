#!/usr/bin/env bash
# ==============================================================================
# loop-test.sh — TDD loop: test → fix → test until ≥ 95% pass
# Usage: .claude/scripts/loop-test.sh <backend|frontend> [description]
# ==============================================================================
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COVERAGE_THRESHOLD=95
MAX_LOOPS=10
LOG_PREFIX="[$(date '+%H:%M:%S')]"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}${LOG_PREFIX} INFO:${NC}  $*"; }
log_pass()  { echo -e "${GREEN}${LOG_PREFIX} PASS:${NC}  $*"; }
log_fail()  { echo -e "${RED}${LOG_PREFIX} FAIL:${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}${LOG_PREFIX} WARN:${NC}  $*"; }
log_step()  { echo -e "${CYAN}${LOG_PREFIX} STEP:${NC}  $*"; }

# ─────────────────────────────────────────────────────────────────────────────
# Detect what changed from git
# ─────────────────────────────────────────────────────────────────────────────
detect_scope() {
  local changed_file="${1:-}"
  if [[ -z "$changed_file" ]]; then
    git diff --name-only HEAD 2>/dev/null | head -20 || return 1
  else
    echo "$changed_file"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Backend: run pytest with coverage
# ─────────────────────────────────────────────────────────────────────────────
run_backend_tests() {
  local test_target="${1:-}"
  local loop=0
  local coverage=0

  while [[ $loop -lt $MAX_LOOPS ]]; do
    ((loop++))
    log_step "Backend test loop $loop/$MAX_LOOPS"

    cd "$PROJECT_ROOT/micco-backend/backend"

    # Determine what to test
    if [[ -n "$test_target" && -f "$test_target" ]]; then
      log_info "Running pytest on: $test_target"
      output=$(pytest "$test_target" -v --tb=short 2>&1)
      exit_code=$?
    elif [[ -n "$test_target" && -d "$test_target" ]]; then
      log_info "Running pytest on dir: $test_target"
      output=$(pytest "$test_target" -v --tb=short 2>&1)
      exit_code=$?
    else
      log_info "Running all backend unit tests"
      output=$(pytest tests/ -v --tb=short --cov=app --cov-report=term 2>&1)
      exit_code=$?
    fi

    echo "$output" | tail -30

    if [[ $exit_code -eq 0 ]]; then
      # Extract coverage
      coverage=$(echo "$output" | grep -oP 'TOTAL\s+\d+\s+\d+\s+\K\d+' | tail -1 || echo "0")
      if [[ -z "$coverage" || "$coverage" == "0" ]]; then
        coverage=$(echo "$output" | grep -oP 'coverage:\s*\K\d+' | tail -1 || echo "0")
      fi

      log_pass "All tests passed!"
      if [[ -n "$coverage" && "$coverage" != "0" ]]; then
        log_info "Coverage: ${coverage}%"
      fi
      echo "$output" | grep -E "passed|failed|error" | tail -5
      return 0
    else
      log_fail "Tests failed. Fix issues and re-run..."
      echo "$output" | grep -E "FAILED|ERROR|AssertionError|Traceback" | head -20
    fi

    # Prompt for fix cycle (this runs inside Claude Code hook context)
    # In hook context we auto-loop, but if this is called manually, pause
    if [[ -t 0 && -z "$CLAUDE_TOOL_INPUT_FILE_PATH" ]]; then
      read -p "Press ENTER to retry, Ctrl+C to stop: " </dev/null
    else
      # In hook mode: check if we've hit the coverage threshold
      if [[ "$coverage" -ge "$COVERAGE_THRESHOLD" ]]; then
        log_pass "Coverage ${coverage}% >= threshold ${COVERAGE_THRESHOLD}%. Stopping."
        return 0
      fi
    fi
  done

  log_warn "Max loops ($MAX_LOOPS) reached. Tests may still have issues."
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Frontend: run playwright e2e tests
# ─────────────────────────────────────────────────────────────────────────────
run_frontend_tests() {
  local test_url="${1:-http://localhost:5174}"
  local loop=0

  while [[ $loop -lt $MAX_LOOPS ]]; do
    ((loop++))
    log_step "Frontend Playwright loop $loop/$MAX_LOOPS"

    # Check if frontend dev server is running
    if ! curl -sf "$test_url" > /dev/null 2>&1; then
      log_warn "Frontend not running at $test_url. Starting vite dev server..."
      cd "$PROJECT_ROOT/micco-frontend"
      # Try to start in background if not running
      if ! pgrep -f "vite" > /dev/null; then
        log_info "Starting Vite dev server on port 5174..."
        npm run dev > /tmp/vite-dev.log 2>&1 &
        sleep 8
      fi
      if ! curl -sf "$test_url" > /dev/null 2>&1; then
        log_fail "Cannot start frontend dev server. Check manually."
        return 1
      fi
    fi

    cd "$PROJECT_ROOT/.claude/skills/playwright-e2e"

    # Run playwright test
    log_info "Running Playwright E2E tests against $test_url"
    output=$(node run.js "$test_url" 2>&1)
    exit_code=$?

    echo "$output"

    if [[ $exit_code -eq 0 ]]; then
      log_pass "All Playwright E2E tests passed!"
      return 0
    else
      log_fail "Playwright tests failed. Fix and re-run..."
    fi
  done

  log_warn "Max loops ($MAX_LOOPS) reached."
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Auto-detect scope from changed files
# ─────────────────────────────────────────────────────────────────────────────
detect_and_run() {
  local changed_files
  changed_files=$(git diff --name-only HEAD 2>/dev/null || echo "")

  if [[ -z "$changed_files" ]]; then
    log_warn "No changed files detected. Run with: loop-test.sh backend|frontend"
    exit 1
  fi

  local has_backend=false
  local has_frontend=false

  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ "$file" == micco-backend/* || "$file" == micco-server/* ]]; then
      has_backend=true
    fi
    if [[ "$file" == micco-frontend/* ]]; then
      has_frontend=true
    fi
  done <<< "$changed_files"

  if $has_backend && ! $has_frontend; then
    log_info "Detected: Backend changes → running backend tests"
    run_backend_tests
  elif $has_frontend && ! $has_backend; then
    log_info "Detected: Frontend changes → running Playwright E2E"
    run_frontend_tests
  else
    log_info "Detected: Both backend + frontend → running both"
    run_backend_tests || true
    run_frontend_tests || true
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
SCOPE="${1:-detect}"
shift || true

case "$SCOPE" in
  backend)
    run_backend_tests "$@"
    ;;
  frontend)
    run_frontend_tests "$@"
    ;;
  detect)
    detect_and_run
    ;;
  *)
    echo "Usage: loop-test.sh <backend|frontend|detect> [target]"
    exit 1
    ;;
esac