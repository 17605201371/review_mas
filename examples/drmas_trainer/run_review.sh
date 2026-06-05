#!/bin/bash
set -x

MODE=${1:-train}
if [ "$MODE" == "eval" ] || [ "$MODE" == "evaluation" ]; then
    echo "Running in evaluation mode"
    VAL_ONLY=True
    TRAIN_DATA="/reviewF/datasets/drmas_review/train.parquet"
    VAL_DATA="/reviewF/datasets/drmas_review/test.parquet" 
    train_data_size=32
    val_data_size=64
    val_group_size=4
else
    echo "Running in training mode"
    VAL_ONLY=False
    TRAIN_DATA="/reviewF/datasets/drmas_review/train.parquet"
    VAL_DATA="/reviewF/datasets/drmas_review/test.parquet" 
    train_data_size=32
    val_data_size=64
    val_group_size=1
fi

###################### Algorithm Configurations #################
algorithm=grpo
group_size=8
group_by_agent_id=True # enable Dr. MAS

##################### Agent Configurations #####################
# Use the newly downloaded 1.5B model on /reviewF mount
model_path="/reviewF/datasets/Qwen3___5-4B"
review_mode=${REVIEW_MODE:-s4}
max_turn=${MAX_TURN:-4}
max_workers_per_turn=${MAX_WORKERS_PER_TURN:-2}
review_log_dir=${REVIEW_LOG_DIR:-outputs/review_turn_logs}

case "$review_mode" in
    s1)
        agent_ids='["Review Manager Agent"]'
        model_ids="[\"$model_path\"]"
        actor_optim_lr='[1e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1]'
        max_turn=1
        ;;
    s2)
        agent_ids='["Review Manager Agent"]'
        model_ids="[\"$model_path\"]"
        actor_optim_lr='[1e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1]'
        ;;
    s3)
        agent_ids='["Review Manager Agent","General Reviewer Agent 1","General Reviewer Agent 2"]'
        model_ids="[\"$model_path\", \"$model_path\", \"$model_path\"]"
        actor_optim_lr='[1e-6,1e-6,1e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1,1,1]'
        ;;
    s4)
        agent_ids='["Review Manager Agent","Claim Agent","Evidence Agent","Critique Agent"]'
        model_ids="[\"$model_path\", \"$model_path\", \"$model_path\", \"$model_path\"]"
        actor_optim_lr='[1e-6,1e-6,1e-6,1e-6]'
        actor_ppo_micro_batch_size_per_gpu='[1,1,1,1]'
        ;;
    *)
        echo "Unsupported REVIEW_MODE: $review_mode"
        exit 1
        ;;
esac

model_sharing=True

orchestra_type=review

experiment_name="drmas_review_${review_mode}_share${model_sharing}"

# Shift the positional arguments so that MODE is not passed to the python script
shift 1

# Performance and Memory Tuning
# export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export VLLM_USE_V1=0

python3 -m verl.trainer.main_ppo \
    algorithm.adv_estimator=$algorithm \
    data.train_files=$TRAIN_DATA \
    data.val_files=$VAL_DATA \
    data.train_batch_size=$train_data_size \
    data.val_batch_size=$val_data_size \
    data.max_prompt_length=2048 \
    data.max_response_length=1024 \
    data.filter_overlong_prompts=False \
    +data.apply_chat_template_kwargs.enable_thinking=False \
    data.truncation='middle' \
    data.return_raw_chat=True \
    actor_rollout_ref.model.path=null \
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
    actor_rollout_ref.rollout.max_num_batched_tokens=10240 \
    actor_rollout_ref.rollout.enable_chunked_prefill=True \
    actor_rollout_ref.rollout.val_kwargs.do_sample=True \
    actor_rollout_ref.rollout.val_kwargs.top_p=0.95 \
    actor_rollout_ref.rollout.val_kwargs.temperature=0.2 \
    actor_rollout_ref.actor.use_invalid_action_penalty=True \
    actor_rollout_ref.actor.invalid_action_penalty_coef=0.1 \
    algorithm.group_by_agent_id=$group_by_agent_id \
    env.env_name=review \
    env.seed=0 \
    env.max_steps=$max_turn \
    env.rollout.n=$group_size \
    env.rollout.val_n=$val_group_size \
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
