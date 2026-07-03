#!/usr/bin/env bash
# Generate P31.6 dashboard/case/recovery artifacts from a completed hardneg20 run.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/p31_6_generate_full20_artifacts.sh --input RUN.jsonl [--label LABEL] [--update-latest]
  scripts/p31_6_generate_full20_artifacts.sh --run-base RUN_BASE [--label LABEL] [--update-latest]

Options:
  --input PATH        Completed run jsonl.
  --run-base BASE    Run base without .jsonl; BASE.jsonl is used.
  --label LABEL      Artifact prefix. Default: P31_6_FRESH_<timestamp or stem>.
  --min-lines N      Minimum jsonl rows required. Default: 20.
  --update-latest    Update .latest_hardneg20_* pointers after successful generation.
  --manual-audit-validation-json PATH
                     Include a validated manual audit report in the entry gate.
  --require-manual-audit
                     Fail the entry gate when manual audit validation is missing.
  --skip-entry-gate  Do not generate the P31.6 entry-gate report.
  --skip-manual-template
                     Do not generate a fillable manual audit template.
  --skip-status-report
                     Do not generate a P31.6 readiness status report.
  --fail-entry-gate  Exit non-zero if the P31.6 machine entry gate fails.
  --dry-run          Print resolved paths/commands without generating artifacts.
  -h, --help         Show this help.
EOF
}

INPUT=""
RUN_BASE=""
LABEL=""
MIN_LINES=20
UPDATE_LATEST=0
MANUAL_AUDIT_VALIDATION_JSON=""
REQUIRE_MANUAL_AUDIT=0
SKIP_ENTRY_GATE=0
SKIP_MANUAL_TEMPLATE=0
SKIP_STATUS_REPORT=0
FAIL_ENTRY_GATE=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT="${2:-}"
      shift 2
      ;;
    --run-base)
      RUN_BASE="${2:-}"
      shift 2
      ;;
    --label)
      LABEL="${2:-}"
      shift 2
      ;;
    --min-lines)
      MIN_LINES="${2:-}"
      shift 2
      ;;
    --update-latest)
      UPDATE_LATEST=1
      shift
      ;;
    --manual-audit-validation-json)
      MANUAL_AUDIT_VALIDATION_JSON="${2:-}"
      shift 2
      ;;
    --require-manual-audit)
      REQUIRE_MANUAL_AUDIT=1
      shift
      ;;
    --skip-entry-gate)
      SKIP_ENTRY_GATE=1
      shift
      ;;
    --skip-manual-template)
      SKIP_MANUAL_TEMPLATE=1
      shift
      ;;
    --skip-status-report)
      SKIP_STATUS_REPORT=1
      shift
      ;;
    --fail-entry-gate)
      FAIL_ENTRY_GATE=1
      shift
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

if [[ -z "${INPUT}" && -z "${RUN_BASE}" ]]; then
  echo "ERROR: provide --input or --run-base" >&2
  usage >&2
  exit 2
fi

if [[ -n "${INPUT}" && -n "${RUN_BASE}" ]]; then
  echo "ERROR: use only one of --input or --run-base" >&2
  exit 2
fi

if [[ -n "${RUN_BASE}" ]]; then
  INPUT="${RUN_BASE}.jsonl"
else
  RUN_BASE="${INPUT%.jsonl}"
fi

if [[ ! -f "${INPUT}" ]]; then
  echo "ERROR: input jsonl not found: ${INPUT}" >&2
  exit 2
fi

if ! [[ "${MIN_LINES}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: --min-lines must be a non-negative integer" >&2
  exit 2
fi

LINE_COUNT="$(wc -l < "${INPUT}" | tr -d ' ')"
if [[ "${LINE_COUNT}" -lt "${MIN_LINES}" ]]; then
  echo "ERROR: ${INPUT} has ${LINE_COUNT} rows, below required ${MIN_LINES}" >&2
  echo "       Do not generate authoritative P31.6 full20 artifacts from partial/empty runs." >&2
  exit 3
fi

if [[ -z "${LABEL}" ]]; then
  stem="$(basename "${RUN_BASE}")"
  if [[ "${stem}" =~ ([0-9]{8}_[0-9]{6}) ]]; then
    LABEL="P31_6_FRESH_${BASH_REMATCH[1]}"
  else
    safe_stem="$(echo "${stem}" | tr '[:lower:]' '[:upper:]' | sed -E 's/[^A-Z0-9]+/_/g; s/^_+|_+$//g')"
    LABEL="P31_6_FRESH_${safe_stem}"
  fi
fi

PYTHON_BIN="${PYTHON_BIN:-/opt/miniconda3/envs/DrMAS/bin/python}"
PYTHONPATH_VALUE="${PYTHONPATH_VALUE:-/opt/miniconda3/envs/agent/lib/python3.12/site-packages:.}"

DASH_MD="${LABEL}_HARDNEG20_DASHBOARD.md"
DASH_JSON="${LABEL}_HARDNEG20_DASHBOARD.json"
DASH_AUDIT="${LABEL}_HARDNEG20_DASHBOARD.audit.json"
ISSUE_MD="${LABEL}_REVIEW_ISSUE_CASE_TABLE.md"
ISSUE_JSON="${LABEL}_REVIEW_ISSUE_CASE_TABLE.json"
RECOVERY_MD="${LABEL}_RECOVERY_CASE_TABLE.md"
RECOVERY_JSON="${LABEL}_RECOVERY_CASE_TABLE.json"
GATE_MD="${LABEL}_ENTRY_GATE_AUDIT.md"
GATE_JSON="${LABEL}_ENTRY_GATE_AUDIT.json"
MANUAL_TEMPLATE_MD="${LABEL}_MANUAL_AUDIT_TEMPLATE.md"
MANUAL_TEMPLATE_JSON="${LABEL}_MANUAL_AUDIT_TEMPLATE.json"
STATUS_MD="${LABEL}_READINESS_STATUS.md"
STATUS_JSON="${LABEL}_READINESS_STATUS.json"

echo "P31.6 artifact generation"
echo "  input:       ${INPUT}"
echo "  rows:        ${LINE_COUNT}"
echo "  label:       ${LABEL}"
echo "  update_latest: ${UPDATE_LATEST}"
if [[ -n "${MANUAL_AUDIT_VALIDATION_JSON}" ]]; then
  echo "  manual_audit_validation: ${MANUAL_AUDIT_VALIDATION_JSON}"
fi
if [[ "${SKIP_ENTRY_GATE}" == "1" ]]; then
  echo "  entry_gate:  skip"
else
  echo "  entry_gate:  generate"
fi
if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_MANUAL_TEMPLATE}" == "0" ]]; then
  echo "  manual_template: generate"
else
  echo "  manual_template: skip"
fi
if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_STATUS_REPORT}" == "0" ]]; then
  echo "  status_report: generate"
else
  echo "  status_report: skip"
fi

run_cmd() {
  echo "+ $*"
  if [[ "${DRY_RUN}" == "0" ]]; then
    "$@"
  fi
}

run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/dashboard_run_comparison_v1.py \
  --candidate "${INPUT}" \
  --label-candidate "${LABEL}" \
  --output-md "${DASH_MD}" \
  --output-json "${DASH_JSON}" \
  --output-audit-json "${DASH_AUDIT}" \
  --mode auto \
  --fail-on-violation

run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/audit_review_issue_case_table_v1.py \
  --input "${INPUT}" \
  --output-json "${ISSUE_JSON}" \
  --output-md "${ISSUE_MD}"

run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/audit_recovery_case_table_v1.py \
  --input "${INPUT}" \
  --output-json "${RECOVERY_JSON}" \
  --output-md "${RECOVERY_MD}"

ENTRY_GATE_STATUS=0
if [[ "${SKIP_ENTRY_GATE}" == "0" ]]; then
  GATE_EXTRA_ARGS=()
  if [[ -n "${MANUAL_AUDIT_VALIDATION_JSON}" ]]; then
    GATE_EXTRA_ARGS+=(--manual-audit-validation-json "${MANUAL_AUDIT_VALIDATION_JSON}")
  fi
  if [[ "${REQUIRE_MANUAL_AUDIT}" == "1" ]]; then
    GATE_EXTRA_ARGS+=(--require-manual-audit)
  fi
  if [[ "${DRY_RUN}" == "1" ]]; then
    if [[ "${#GATE_EXTRA_ARGS[@]}" -gt 0 ]]; then
      run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_entry_gate_audit.py \
        --dashboard-json "${DASH_JSON}" \
        --case-json "${ISSUE_JSON}" \
        --recovery-json "${RECOVERY_JSON}" \
        --output-json "${GATE_JSON}" \
        --output-md "${GATE_MD}" \
        "${GATE_EXTRA_ARGS[@]}"
    else
      run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_entry_gate_audit.py \
        --dashboard-json "${DASH_JSON}" \
        --case-json "${ISSUE_JSON}" \
        --recovery-json "${RECOVERY_JSON}" \
        --output-json "${GATE_JSON}" \
        --output-md "${GATE_MD}"
    fi
  else
    if [[ "${#GATE_EXTRA_ARGS[@]}" -gt 0 ]]; then
      echo "+ env PYTHONPATH=${PYTHONPATH_VALUE} ${PYTHON_BIN} scripts/p31_6_entry_gate_audit.py --dashboard-json ${DASH_JSON} --case-json ${ISSUE_JSON} --recovery-json ${RECOVERY_JSON} --output-json ${GATE_JSON} --output-md ${GATE_MD} ${GATE_EXTRA_ARGS[*]}"
    else
      echo "+ env PYTHONPATH=${PYTHONPATH_VALUE} ${PYTHON_BIN} scripts/p31_6_entry_gate_audit.py --dashboard-json ${DASH_JSON} --case-json ${ISSUE_JSON} --recovery-json ${RECOVERY_JSON} --output-json ${GATE_JSON} --output-md ${GATE_MD}"
    fi
    set +e
    if [[ "${#GATE_EXTRA_ARGS[@]}" -gt 0 ]]; then
      env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_entry_gate_audit.py \
        --dashboard-json "${DASH_JSON}" \
        --case-json "${ISSUE_JSON}" \
        --recovery-json "${RECOVERY_JSON}" \
        --output-json "${GATE_JSON}" \
        --output-md "${GATE_MD}" \
        "${GATE_EXTRA_ARGS[@]}"
    else
      env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_entry_gate_audit.py \
        --dashboard-json "${DASH_JSON}" \
        --case-json "${ISSUE_JSON}" \
        --recovery-json "${RECOVERY_JSON}" \
        --output-json "${GATE_JSON}" \
        --output-md "${GATE_MD}"
    fi
    ENTRY_GATE_STATUS=$?
    set -e
    if [[ "${ENTRY_GATE_STATUS}" != "0" ]]; then
      echo "P31.6 entry gate did not pass (exit=${ENTRY_GATE_STATUS})."
      echo "Artifacts were still generated; pass --fail-entry-gate to make this fatal."
      if [[ "${FAIL_ENTRY_GATE}" == "1" ]]; then
        exit "${ENTRY_GATE_STATUS}"
      fi
    fi
  fi
fi

if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_MANUAL_TEMPLATE}" == "0" ]]; then
  run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_manual_audit.py template \
    --entry-gate-json "${GATE_JSON}" \
    --case-json "${ISSUE_JSON}" \
    --output-json "${MANUAL_TEMPLATE_JSON}" \
    --output-md "${MANUAL_TEMPLATE_MD}"
fi

if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_STATUS_REPORT}" == "0" ]]; then
  STATUS_EXTRA_ARGS=()
  if [[ -n "${MANUAL_AUDIT_VALIDATION_JSON}" ]]; then
    STATUS_EXTRA_ARGS+=(--manual-validation-json "${MANUAL_AUDIT_VALIDATION_JSON}")
  fi
  if [[ "${#STATUS_EXTRA_ARGS[@]}" -gt 0 ]]; then
    run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_status_report.py \
      --run-base "${RUN_BASE}" \
      --entry-gate-json "${GATE_JSON}" \
      --output-json "${STATUS_JSON}" \
      --output-md "${STATUS_MD}" \
      "${STATUS_EXTRA_ARGS[@]}"
  else
    run_cmd env PYTHONPATH="${PYTHONPATH_VALUE}" "${PYTHON_BIN}" scripts/p31_6_status_report.py \
      --run-base "${RUN_BASE}" \
      --entry-gate-json "${GATE_JSON}" \
      --output-json "${STATUS_JSON}" \
      --output-md "${STATUS_MD}"
  fi
fi

if [[ "${DRY_RUN}" == "0" && "${UPDATE_LATEST}" == "1" ]]; then
  echo "${RUN_BASE}" > .latest_hardneg20_run
  echo "${DASH_MD}" > .latest_hardneg20_dashboard
  echo "${ISSUE_MD}" > .latest_hardneg20_review_issue_cases
  echo "${RECOVERY_MD}" > .latest_hardneg20_recovery_case
  if [[ -f "${RUN_BASE}.log" ]]; then
    echo "${RUN_BASE}.log" > .latest_hardneg20_log
  fi
fi

echo "Generated artifact targets:"
echo "  ${DASH_MD}"
echo "  ${DASH_JSON}"
echo "  ${DASH_AUDIT}"
echo "  ${ISSUE_MD}"
echo "  ${ISSUE_JSON}"
echo "  ${RECOVERY_MD}"
echo "  ${RECOVERY_JSON}"
if [[ "${SKIP_ENTRY_GATE}" == "0" ]]; then
  echo "  ${GATE_MD}"
  echo "  ${GATE_JSON}"
fi
if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_MANUAL_TEMPLATE}" == "0" ]]; then
  echo "  ${MANUAL_TEMPLATE_MD}"
  echo "  ${MANUAL_TEMPLATE_JSON}"
fi
if [[ "${SKIP_ENTRY_GATE}" == "0" && "${SKIP_STATUS_REPORT}" == "0" ]]; then
  echo "  ${STATUS_MD}"
  echo "  ${STATUS_JSON}"
fi
