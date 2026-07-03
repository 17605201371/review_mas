#!/usr/bin/env bash
# P31.6 fresh full20 launcher/post-processor.
#
# This wrapper keeps the P31.6 validation sequence reproducible:
#   launch MiMo full20 -> optionally wait -> generate dashboard/cases/recovery
#   -> entry gate -> manual audit template.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/p31_6_full20_pipeline.sh --launch [--wait] [--update-latest]
  scripts/p31_6_full20_pipeline.sh --run-base RUN_BASE [--wait] [--update-latest]

Options:
  --launch              Launch a fresh P31.6 hardneg20 run with the agreed MiMo parameters.
  --run-base BASE       Existing run base without .jsonl; used for wait/postprocess.
  --label LABEL         Artifact label passed to p31_6_generate_full20_artifacts.sh.
  --wait                Wait for the run process to finish before postprocessing.
  --no-postprocess      Do not generate artifacts after launch/wait.
  --update-latest       Update .latest_hardneg20_* pointers during postprocessing.
  --min-lines N         Minimum completed jsonl rows before postprocessing. Default: 20.
  --wait-timeout SEC    Max seconds to wait. Default: 28800.
  --poll-interval SEC   Poll interval while waiting. Default: 60.
  --dry-run             Print commands without launching or generating artifacts.
  -h, --help            Show this help.

Environment defaults for --launch:
  API_MAX_WORKERS=4 API_MAX_RETRIES=8 API_TIMEOUT=600 MAX_TOKENS=1536
  DRMAS_NEG_QUOTE_HYGIENE=1
  DRMAS_TARGETED_NEGATIVE_SEARCH=1
  DRMAS_FREEFORM_REVIEWER_NEGATIVE=1
  DRMAS_REVIEW_ISSUE_BUNDLE=1
EOF
}

LAUNCH=0
RUN_BASE=""
LABEL=""
WAIT=0
POSTPROCESS=1
UPDATE_LATEST=0
MIN_LINES=20
WAIT_TIMEOUT=28800
POLL_INTERVAL=60
DRY_RUN=0

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
    --label)
      LABEL="${2:-}"
      shift 2
      ;;
    --wait)
      WAIT=1
      shift
      ;;
    --no-postprocess)
      POSTPROCESS=0
      shift
      ;;
    --update-latest)
      UPDATE_LATEST=1
      shift
      ;;
    --min-lines)
      MIN_LINES="${2:-}"
      shift 2
      ;;
    --wait-timeout)
      WAIT_TIMEOUT="${2:-}"
      shift 2
      ;;
    --poll-interval)
      POLL_INTERVAL="${2:-}"
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
for numeric in MIN_LINES WAIT_TIMEOUT POLL_INTERVAL; do
  value="${!numeric}"
  if ! [[ "${value}" =~ ^[0-9]+$ ]]; then
    echo "ERROR: ${numeric} must be a non-negative integer" >&2
    exit 2
  fi
done

line_count_for_run() {
  local base="$1"
  local jsonl="${base}.jsonl"
  if [[ -f "${jsonl}" ]]; then
    wc -l < "${jsonl}" | tr -d ' '
  else
    echo 0
  fi
}

wait_for_run() {
  local base="$1"
  local pid_file="${base}.pid"
  local jsonl="${base}.jsonl"
  local waited=0
  local pid=""

  if [[ -f "${pid_file}" ]]; then
    pid="$(tr -d '[:space:]' < "${pid_file}")"
  fi

  if [[ -z "${pid}" ]]; then
    local lines
    lines="$(line_count_for_run "${base}")"
    if [[ "${lines}" -ge "${MIN_LINES}" ]]; then
      echo "Run already complete: ${jsonl} has ${lines} rows."
      return 0
    fi
    echo "ERROR: ${pid_file} not found and ${jsonl} has only ${lines} rows." >&2
    return 3
  fi

  echo "Waiting for ${base} (pid=${pid})..."
  while kill -0 "${pid}" >/dev/null 2>&1; do
    local lines
    lines="$(line_count_for_run "${base}")"
    echo "  waited=${waited}s rows=${lines}"
    if [[ "${WAIT_TIMEOUT}" -gt 0 && "${waited}" -ge "${WAIT_TIMEOUT}" ]]; then
      echo "ERROR: wait timeout after ${waited}s for ${base}" >&2
      return 4
    fi
    sleep "${POLL_INTERVAL}"
    waited=$((waited + POLL_INTERVAL))
  done

  local final_lines
  final_lines="$(line_count_for_run "${base}")"
  echo "Run process ended: ${base}, rows=${final_lines}"
  if [[ "${final_lines}" -lt "${MIN_LINES}" ]]; then
    echo "ERROR: ${jsonl} has ${final_lines} rows, below required ${MIN_LINES}" >&2
    return 5
  fi
}

launch_run() {
  local output
  echo "Launching P31.6 fresh full20..."
  if [[ "${DRY_RUN}" == "1" ]]; then
    cat <<'EOF'
+ DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1 DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 DRMAS_REVIEW_ISSUE_BUNDLE=1 API_MAX_WORKERS=4 API_MAX_RETRIES=8 API_TIMEOUT=600 MAX_TOKENS=1536 bash run_hardneg20_guard3.sh
EOF
    return 0
  fi

  set +e
  output="$(
    DRMAS_NEG_QUOTE_HYGIENE=1 \
    DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
    DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
    DRMAS_REVIEW_ISSUE_BUNDLE=1 \
    API_MAX_WORKERS="${API_MAX_WORKERS:-4}" \
    API_MAX_RETRIES="${API_MAX_RETRIES:-8}" \
    API_TIMEOUT="${API_TIMEOUT:-600}" \
    MAX_TOKENS="${MAX_TOKENS:-1536}" \
    bash run_hardneg20_guard3.sh 2>&1
  )"
  local status=$?
  set -e
  printf '%s\n' "${output}"
  if [[ "${status}" != "0" ]]; then
    echo "ERROR: launch failed before a usable background run was created." >&2
    return "${status}"
  fi
  RUN_BASE="$(printf '%s\n' "${output}" | sed -n 's/^=== hardneg20 guard3: \(.*\) ===$/\1/p' | tail -1)"
  if [[ -z "${RUN_BASE}" ]]; then
    echo "ERROR: could not parse run base from launcher output." >&2
    return 6
  fi
  echo "Parsed run base: ${RUN_BASE}"
}

postprocess_run() {
  local base="$1"
  local args=("--run-base" "${base}" "--min-lines" "${MIN_LINES}")
  if [[ -n "${LABEL}" ]]; then
    args+=("--label" "${LABEL}")
  fi
  if [[ "${UPDATE_LATEST}" == "1" ]]; then
    args+=("--update-latest")
  fi
  if [[ "${DRY_RUN}" == "1" ]]; then
    args+=("--dry-run")
  fi
  echo "Postprocessing ${base}..."
  scripts/p31_6_generate_full20_artifacts.sh "${args[@]}"
}

if [[ "${LAUNCH}" == "1" ]]; then
  launch_run
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "Dry-run launch has no run base to wait/postprocess."
    exit 0
  fi
fi

if [[ "${WAIT}" == "1" ]]; then
  wait_for_run "${RUN_BASE}"
fi

if [[ "${POSTPROCESS}" == "1" ]]; then
  postprocess_run "${RUN_BASE}"
else
  echo "Postprocess skipped for ${RUN_BASE}."
fi
