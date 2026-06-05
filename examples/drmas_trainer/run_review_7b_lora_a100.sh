#!/bin/bash
set -euo pipefail
set -x

MODE=${1:-train}
if [ $# -gt 0 ]; then
    shift
fi

PYTHON_BIN=${PYTHON_BIN:-/root/miniconda3/envs/DrMAS/bin/python}
LOG_FILE=${LOG_FILE:-/root/DrMAS/review_training_a100.log}
MODEL_PATH=${MODEL_PATH:-/reviewF/datasets/Qwen3___5-4B}
TRAIN_DATA=${TRAIN_DATA:-/reviewF/datasets/drmas_review_1pct/train.parquet}
VAL_DATA=${VAL_DATA:-/reviewF/datasets/drmas_review_1pct/test.parquet}

: > "$LOG_FILE"
exec > >(tee "$LOG_FILE") 2>&1

if [ "$MODE" = "eval" ] || [ "$MODE" = "evaluation" ]; then
    echo "Running in evaluation mode"
    VAL_ONLY=True
    TRAIN_BATCH_SIZE=8
    VAL_BATCH_SIZE=8
    VAL_GROUP_SIZE=2
else
    echo "Running in training mode"
    VAL_ONLY=False
    TRAIN_BATCH_SIZE=8
    VAL_BATCH_SIZE=8
    VAL_GROUP_SIZE=1
fi

algorithm=grpo
group_size=4
group_by_agent_id=True

lora_rank=32
lora_alpha=64

review_mode=${REVIEW_MODE:-s4}
max_turn=${MAX_TURN:-4}
max_workers_per_turn=${MAX_WORKERS_PER_TURN:-2}
review_log_dir=${REVIEW_LOG_DIR:-outputs/review_turn_logs}

case "$review_mode" in
    s1)
        agent_ids='["Review Manager Agent"]'
        model_ids="[\"$MODEL_PATH\"]"
        actor_optim_lr='[5e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1]'
        max_turn=1
        ;;
    s2)
        agent_ids='["Review Manager Agent"]'
        model_ids="[\"$MODEL_PATH\"]"
        actor_optim_lr='[5e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1]'
        ;;
    s3)
        agent_ids='["Review Manager Agent","General Reviewer Agent 1","General Reviewer Agent 2"]'
        model_ids="[\"$MODEL_PATH\", \"$MODEL_PATH\", \"$MODEL_PATH\"]"
        actor_optim_lr='[5e-6,5e-6,5e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1,1,1]'
        ;;
    s4)
        agent_ids='["Review Manager Agent","Claim Agent","Evidence Agent","Critique Agent"]'
        model_ids="[\"$MODEL_PATH\", \"$MODEL_PATH\", \"$MODEL_PATH\", \"$MODEL_PATH\"]"
        actor_optim_lr='[5e-6,5e-6,5e-6,5e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1,1,1,1]'
        ;;
    *)
        echo "Unsupported REVIEW_MODE: $review_mode"
        exit 1
        ;;
esac

model_sharing=True
orchestra_type=review

experiment_name="drmas_review_${review_mode}_a100_qwen25_7b_lora"

export VLLM_USE_V1=0
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

"$PYTHON_BIN" -m verl.trainer.main_ppo \
    algorithm.adv_estimator=$algorithm \
    data.train_files=$TRAIN_DATA \
    data.val_files=$VAL_DATA \
    data.train_batch_size=$TRAIN_BATCH_SIZE \
    data.val_batch_size=$VAL_BATCH_SIZE \
    data.max_prompt_length=2048 \
    data.max_response_length=512 \
    data.filter_overlong_prompts=False \
    +data.apply_chat_template_kwargs.enable_thinking=False \
    data.truncation='middle' \
    data.return_raw_chat=True \
    actor_rollout_ref.model.path=null \
    actor_rollout_ref.model.lora_rank=$lora_rank \
    actor_rollout_ref.model.lora_alpha=$lora_alpha \
    actor_rollout_ref.actor.optim.lr=null \
    +agent.agent_specific_parameters.actor.optim.lr=$actor_optim_lr \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.actor.use_adaptive_ppo_mini_batch_size=True \
    actor_rollout_ref.actor.ppo_mini_update_num=1 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=null \
    +agent.agent_specific_parameters.actor.ppo_micro_batch_size_per_gpu=$actor_ppo_micro_batch_size_per_gpu \
    actor_rollout_ref.actor.use_kl_loss=False \
    actor_rollout_ref.actor.entropy_coeff=0.0 \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=True \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.55 \
    actor_rollout_ref.rollout.max_model_len=2560 \
    actor_rollout_ref.rollout.max_num_batched_tokens=2560 \
    actor_rollout_ref.rollout.enable_chunked_prefill=True \
    actor_rollout_ref.rollout.val_kwargs.do_sample=True \
    actor_rollout_ref.rollout.val_kwargs.top_p=0.95 \
    actor_rollout_ref.rollout.val_kwargs.temperature=0.2 \
    actor_rollout_ref.actor.use_invalid_action_penalty=False \
    actor_rollout_ref.actor.invalid_action_penalty_coef=0.1 \
    algorithm.group_by_agent_id=$group_by_agent_id \
    env.env_name=review \
    env.seed=0 \
    env.max_steps=$max_turn \
    env.rollout.n=$group_size \
    env.rollout.val_n=$VAL_GROUP_SIZE \
    agent.agent_ids="$agent_ids" \
    agent.model_ids="$model_ids" \
    agent.model_sharing=$model_sharing \
    agent.orchestra_type=$orchestra_type \
    +agent.orchestra.review.mode=$review_mode \
    +agent.orchestra.review.max_workers_per_turn=$max_workers_per_turn \
    +env.review.log_dir=$review_log_dir \
    trainer.critic_warmup=0 \
    trainer.logger=['console'] \
    trainer.project_name='DrMAS_review' \
    trainer.experiment_name="$experiment_name" \
    trainer.n_gpus_per_node=1 \
    trainer.nnodes=1 \
    trainer.save_freq=100 \
    trainer.test_freq=10 \
    trainer.total_epochs=1 \
    trainer.val_only=$VAL_ONLY \
    trainer.val_before_train=True \
    "$@"
