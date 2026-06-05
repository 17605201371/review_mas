#!/usr/bin/env bash
# DeepSeek V3 API smoke8 sameids 对比实验
# 对比基线: smoke8_20260604_p0fix3_sameids_qwen35_t7 (Qwen3.5-9B vLLM)
#
# 使用火山引擎 DeepSeek V3 API 替换全部 Agent 推理
# 启动前确保已安装 openai: pip install openai>=1.0.0
# 启动前必须设置：
#   export DEEPSEEK_API_KEY=...

set -euo pipefail

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "ERROR: DEEPSEEK_API_KEY is required. Export it before running this script." >&2
  exit 2
fi

RUN_TAG="smoke8_$(date +%Y%m%d)_deepseek_v3_sameids_t7"
LOG_FILE="${RUN_TAG}.log"
OUTPUT_PATH="${RUN_TAG}.jsonl"
LOG_DIR="${RUN_TAG}_logs"

echo "=== DeepSeek V3 API Run: ${RUN_TAG} ==="
echo "Dataset: smoke8_sameids_20260604.parquet"
echo "Output:  ${OUTPUT_PATH}"
echo "Logs:    ${LOG_DIR}"
echo "Log:     ${LOG_FILE}"

source /opt/conda/etc/profile.d/conda.sh
conda activate DrMAS-qwen35

python -u -m agent_system.inference.review_runner \
  --backend api \
  --api-model deepseek-v3-2-251201 \
  --api-base-url "https://ark.cn-beijing.volces.com/api/v3" \
  --api-max-workers 4 \
  --api-timeout 180 \
  --api-max-retries 3 \
  --dataset-path smoke8_sameids_20260604.parquet \
  --mode s4 \
  --max-turns 7 \
  --max-workers-per-turn 2 \
  --manager-batch-size 1 \
  --temperature 0.2 \
  --top-p 0.95 \
  --max-tokens 2048 \
  --output-path "${OUTPUT_PATH}" \
  --log-dir "${LOG_DIR}" \
  2>&1 | tee "${LOG_FILE}"

echo ""
echo "=== Run complete: ${RUN_TAG} ==="
echo "Run dashboard:"
echo "  python scripts/dashboard_run_comparison_v1.py ${OUTPUT_PATH}"
