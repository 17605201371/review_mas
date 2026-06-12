#!/usr/bin/env bash
# hardneg20 guard3 验证跑批 (P0)
# 代码版本: 3342192 (negqty recoverycap guard3)
# 目的: 在 hardneg20 上确认 smoke8 guard3 的 recovery/contested 改善是否成立，
#       并检查 negative quantity 是否仍然偏低 (smoke8 上比上一轮下降)。
# 与上一轮 hardneg20 (hygienefilter3, 20260612_162757) 同口径对比: mt7 / b4w2 / mimo-v2.5。
# 当前默认复现 20260612_215608: api4 / retries5 / timeout600 / aggressive。
#
# 启动前必须设置 MiMo API key:
#   export MIMO_API_KEY=...
# 在 Mac 上的仓库根目录运行:
#   bash run_hardneg20_guard3.sh

set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source ./.env
  set +a
fi

if [[ -z "${MIMO_API_KEY:-}" ]]; then
  echo "ERROR: MIMO_API_KEY is required. Export it before running." >&2
  exit 2
fi

# P26 7.3: negative-discovery persistence mode.
#   default     -> 当前 baseline 行为 (smoke8 口径不变)
#   aggressive  -> 放开 hard-negative 持续发现 (grounded 5 / actionable 3 / flaw 3 / attempts 5 / min_remaining 1)
# 用法:
#   bash run_hardneg20_guard3.sh                              # baseline
#   DRMAS_NEG_DISCOVERY_MODE=aggressive bash run_hardneg20_guard3.sh   # 7.3 改动
NEG_MODE="${DRMAS_NEG_DISCOVERY_MODE:-default}"
export DRMAS_NEG_DISCOVERY_MODE="${NEG_MODE}"
if [[ "${NEG_MODE}" == "aggressive" || "${NEG_MODE}" == "hardneg" || "${NEG_MODE}" == "enrich" ]]; then
  MODE_SUFFIX="_negaggr"
else
  MODE_SUFFIX=""
fi

API_MAX_WORKERS="${API_MAX_WORKERS:-4}"
API_MAX_RETRIES="${API_MAX_RETRIES:-5}"
API_TIMEOUT="${API_TIMEOUT:-600}"

RUN_TAG="mimo_v25_negqty_recoverycap_guard3${MODE_SUFFIX}_hardneg20_mt7_b4w2_api${API_MAX_WORKERS}_r${API_MAX_RETRIES}t${API_TIMEOUT}_$(date +%Y%m%d_%H%M%S)"
OUTPUT_PATH="${RUN_TAG}.jsonl"
LOG_FILE="${RUN_TAG}.log"
LOG_DIR="${RUN_TAG}_logs"
META_FILE="${RUN_TAG}.meta"
PID_FILE="${RUN_TAG}.pid"
DATASET="hard_negative_20_20260611.parquet"

if [[ ! -f "${DATASET}" ]]; then
  echo "ERROR: dataset ${DATASET} not found in $(pwd)" >&2
  exit 2
fi

echo "=== hardneg20 guard3: ${RUN_TAG} ==="
echo "Dataset: ${DATASET} (20 papers)"
echo "Output:  ${OUTPUT_PATH}"
echo "Log:     ${LOG_FILE}"

PYTHON_BIN="${PYTHON_BIN:-/opt/miniconda3/envs/DrMAS/bin/python}"
PYTHONPATH_VALUE="${PYTHONPATH_VALUE:-/opt/miniconda3/envs/agent/lib/python3.12/site-packages:.}"

cat > "${META_FILE}" <<EOF
run_base=${RUN_TAG}
start_time=$(date '+%Y-%m-%d %H:%M:%S %Z')
params=max_turns=7 manager_batch_size=4 api_max_workers=${API_MAX_WORKERS} api_max_retries=${API_MAX_RETRIES} api_timeout=${API_TIMEOUT} dataset=${DATASET} mode=s4 model=mimo-v2.5 max_tokens=768 temperature=1.0 top_p=0.95 model_adapter_mode=small_model code_commit=3342192 neg_discovery_mode=${NEG_MODE}
launch_mode=background
EOF

NO_PROXY="*" HTTPS_PROXY="" HTTP_PROXY="" PYTHONPATH="${PYTHONPATH_VALUE}" nohup "${PYTHON_BIN}" -u agent_system/inference/review_runner.py \
  --backend api \
  --api-provider mimo \
  --api-model mimo-v2.5 \
  --api-max-workers "${API_MAX_WORKERS}" \
  --api-max-retries "${API_MAX_RETRIES}" \
  --api-timeout "${API_TIMEOUT}" \
  --model-adapter-mode small_model \
  --dataset-path "${DATASET}" \
  --mode s4 \
  --max-turns 7 \
  --max-workers-per-turn 2 \
  --manager-batch-size 4 \
  --temperature 1.0 \
  --top-p 0.95 \
  --max-tokens 768 \
  --output-path "${OUTPUT_PATH}" \
  --log-dir "${LOG_DIR}" \
  > "${LOG_FILE}" 2>&1 &

RUN_PID=$!
echo "${RUN_PID}" > "${PID_FILE}"
echo "pid=${RUN_PID}" >> "${META_FILE}"
echo "已后台启动, PID=${RUN_PID}"
echo "实时查看: tail -f ${LOG_FILE}"
echo "完成后更新 latest 指针:"
echo "  echo ${RUN_TAG} > .latest_hardneg20_run && echo ${LOG_FILE} > .latest_hardneg20_log"
