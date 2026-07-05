#!/usr/bin/env bash
# P32 clean hardneg20 reproducibility wrapper.
#
# This wrapper deliberately reuses the P31.6 artifact pipeline.  P32 adds only
# stricter run hygiene: stable labels, 20-row minimum, JSON response format on,
# and MAX_TOKENS=2048.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/p32_clean_full20_pipeline.sh --launch --run-id R1 [--update-latest]
  scripts/p32_clean_full20_pipeline.sh --run-base RUN_BASE --run-id R1 [--label LABEL]

Options:
  --launch              Launch a fresh hardneg20 run and wait for completion.
  --run-base BASE       Existing run base without .jsonl; used for postprocess.
  --run-id ID           P32 clean run id, for example R1, R2, or R3.
  --label LABEL         Artifact label. Default: P32_CLEAN_<RUN_ID>_<timestamp>.
  --update-latest       Update .latest_hardneg20_* pointers during postprocess.
  --wait-timeout SEC    Max seconds to wait. Default: 28800.
  --poll-interval SEC   Poll interval while waiting. Default: 60.
  --stability-run SPEC  Add LABEL=RUN_BASE to a post-run stability report.
                         Repeat for multiple completed/manual-audited runs.
  --stability-prefix P  Output P.json/P.md from p32_stability_report.py.
                         Default: P32_STABILITY_<timestamp>.
  --min-stability-runs N
                         Required clean runs for stability PASS. Default: 3.
  --dry-run             Print and dry-run commands without API calls.
  -h, --help            Show this help.

P32 enforced runtime defaults:
  DRMAS_JSON_RESPONSE_FORMAT=on
  API_MAX_WORKERS=4 API_MAX_RETRIES=8 API_TIMEOUT=600 MAX_TOKENS=2048

If API instability requires fewer workers, set API_MAX_WORKERS=2.  Do not
lower MAX_TOKENS below 2048 for P32.
EOF
}

LAUNCH=0
RUN_BASE=""
RUN_ID=""
LABEL=""
UPDATE_LATEST=0
WAIT_TIMEOUT=28800
POLL_INTERVAL=60
DRY_RUN=0
MIN_LINES=20
MIN_STABILITY_RUNS=3
STABILITY_PREFIX=""
STABILITY_RUNS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --launch)
      LAUNCH=1
      shift
      ;;
    --run-base)
      RUN_BASE="${2:-}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:-}"
      shift 2
      ;;
    --label)
      LABEL="${2:-}"
      shift 2
      ;;
    --update-latest)
      UPDATE_LATEST=1
      shift
      ;;
    --wait-timeout)
      WAIT_TIMEOUT="${2:-}"
      shift 2
      ;;
    --poll-interval)
      POLL_INTERVAL="${2:-}"
      shift 2
      ;;
    --stability-run)
      STABILITY_RUNS+=("${2:-}")
      shift 2
      ;;
    --stability-prefix)
      STABILITY_PREFIX="${2:-}"
      shift 2
      ;;
    --min-stability-runs)
      MIN_STABILITY_RUNS="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${LAUNCH}" == "0" && -z "${RUN_BASE}" ]]; then
  echo "ERROR: provide --launch or --run-base" >&2
  usage >&2
  exit 2
fi
if [[ "${LAUNCH}" == "1" && -n "${RUN_BASE}" ]]; then
  echo "ERROR: use only one of --launch or --run-base" >&2
  exit 2
fi
if [[ -z "${RUN_ID}" ]]; then
  echo "ERROR: --run-id is required, for example --run-id R1" >&2
  exit 2
fi
for numeric in WAIT_TIMEOUT POLL_INTERVAL MIN_STABILITY_RUNS; do
  value="${!numeric}"
  if ! [[ "${value}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: ${numeric} must be a non-negative integer" >&2
    exit 2
  fi
done

MAX_TOKENS_VALUE="${MAX_TOKENS:-2048}"
if [[ "${MAX_TOKENS_VALUE}" != "2048" ]]; then
  echo "ERROR: P32 requires MAX_TOKENS=2048; got ${MAX_TOKENS_VALUE}" >&2
  exit 2
fi

JSON_FORMAT_VALUE="${DRMAS_JSON_RESPONSE_FORMAT:-on}"
if [[ "${JSON_FORMAT_VALUE}" != "on" ]]; then
  echo "ERROR: P32 requires DRMAS_JSON_RESPONSE_FORMAT=on; got ${JSON_FORMAT_VALUE}" >&2
  exit 2
fi

API_MAX_WORKERS_VALUE="${API_MAX_WORKERS:-4}"
API_MAX_RETRIES_VALUE="${API_MAX_RETRIES:-8}"
API_TIMEOUT_VALUE="${API_TIMEOUT:-600}"

if [[ -z "${LABEL}" ]]; then
  safe_run_id="$(echo "${RUN_ID}" | tr '[:lower:]' '[:upper:]' | sed -E 's/[^A-Z0-9]+/_/g; s/^_+|_+$//g')"
  LABEL="P32_CLEAN_${safe_run_id}_$(date +%Y%m%d_%H%M%S)"
fi

P31_ARGS=()
if [[ "${LAUNCH}" == "1" ]]; then
  P31_ARGS+=(--launch --wait)
else
  P31_ARGS+=(--run-base "${RUN_BASE}")
fi
P31_ARGS+=(--label "${LABEL}" --min-lines "${MIN_LINES}" --wait-timeout "${WAIT_TIMEOUT}" --poll-interval "${POLL_INTERVAL}")
if [[ "${UPDATE_LATEST}" == "1" ]]; then
  P31_ARGS+=(--update-latest)
fi
if [[ "${DRY_RUN}" == "1" ]]; then
  P31_ARGS+=(--dry-run)
fi

echo "P32 clean full20 pipeline"
echo "  run_id: ${RUN_ID}"
echo "  label: ${LABEL}"
echo "  max_tokens: ${MAX_TOKENS_VALUE}"
echo "  json_response_format: ${JSON_FORMAT_VALUE}"
echo "  api_max_workers: ${API_MAX_WORKERS_VALUE}"
echo "  min_lines: ${MIN_LINES}"

P31_CMD=(
  env
  DRMAS_JSON_RESPONSE_FORMAT="${JSON_FORMAT_VALUE}"
  API_MAX_WORKERS="${API_MAX_WORKERS_VALUE}"
  API_MAX_RETRIES="${API_MAX_RETRIES_VALUE}"
  API_TIMEOUT="${API_TIMEOUT_VALUE}"
  MAX_TOKENS="${MAX_TOKENS_VALUE}"
  scripts/p31_6_full20_pipeline.sh
  "${P31_ARGS[@]}"
)

printf '+'
printf ' %q' "${P31_CMD[@]}"
printf '\n'
"${P31_CMD[@]}"

if [[ "${#STABILITY_RUNS[@]}" -gt 0 ]]; then
  if [[ -z "${STABILITY_PREFIX}" ]]; then
    STABILITY_PREFIX="P32_STABILITY_$(date +%Y%m%d_%H%M%S)"
  fi
  REPORT_CMD=(scripts/p32_stability_report.py --min-runs "${MIN_STABILITY_RUNS}" --output-json "${STABILITY_PREFIX}.json" --output-md "${STABILITY_PREFIX}.md")
  for spec in "${STABILITY_RUNS[@]}"; do
    REPORT_CMD+=(--run "${spec}")
  done
  printf '+'
  printf ' %q' "${REPORT_CMD[@]}"
  printf '\n'
  if [[ "${DRY_RUN}" == "0" ]]; then
    "${REPORT_CMD[@]}"
  fi
fi
