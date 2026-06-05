from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np
from transformers import PreTrainedTokenizer
from verl import DataProto

from agent_system.agent.agents.base import BaseAgent
from agent_system.agent.utils import json_projection
from agent_system.multi_turn_rollout.utils import preprocess_batch


class BaseReviewJsonAgent(BaseAgent):
    json_start_tag = "<json>"
    json_end_tag = "</json>"
    check_think_tag = True

    def normalize_payload(self, payload: Dict[str, Any], env_obs: Dict[str, Any], item_idx: int) -> Dict[str, Any]:
        raise NotImplementedError

    def call(
        self,
        gen_batch: DataProto,
        env_obs: Dict[str, Any],
        team_context: List[str],
        actor_rollout_wg,
        agent_active_mask,
        step: int,
    ) -> Tuple[DataProto, List[str]]:
        obs = self.build_prompt(env_obs, team_context, step)
        batch = preprocess_batch(
            gen_batch=gen_batch,
            obs=obs,
            config=self.config,
            tokenizer=self.tokenizer,
            processor=self.processor,
        )

        batch, text_responses = self._generate_with_llm(batch, actor_rollout_wg, agent_active_mask, gen_batch.meta_info)
        json_texts, payloads, valids = json_projection(
            text_responses,
            start_tag=self.json_start_tag,
            end_tag=self.json_end_tag,
            check_think_tag=self.check_think_tag,
        )

        normalized_texts: List[str] = []
        normalized_payloads: List[Any] = []
        for idx, payload in enumerate(payloads):
            if not valids[idx] or not agent_active_mask[idx]:
                normalized_texts.append("")
                normalized_payloads.append(None)
                continue
            try:
                normalized_payload = self.normalize_payload(payload, env_obs, idx)
                normalized_texts.append(json.dumps(normalized_payload, ensure_ascii=False, sort_keys=True))
                normalized_payloads.append(normalized_payload)
            except Exception:
                valids[idx] = False
                normalized_texts.append("")
                normalized_payloads.append(None)

        batch.non_tensor_batch["is_action_valid"] = valids
        batch.non_tensor_batch["json_payload"] = np.array(normalized_payloads, dtype=object)
        batch.non_tensor_batch["json_text"] = np.array(normalized_texts, dtype=object)
        batch.non_tensor_batch["raw_text_response"] = np.array([str(resp).strip() for resp in text_responses], dtype=object)
        batch.non_tensor_batch["env_step"] = np.array([step] * len(text_responses), dtype=object)
        return batch, normalized_texts


class BaseReviewAgent(BaseReviewJsonAgent):
    def __init__(self, name: str, prompt: str, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__(name=name, prompt=prompt, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)
