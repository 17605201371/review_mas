from __future__ import annotations

from typing import Any, Dict

from transformers import PreTrainedTokenizer

from agent_system.agent.agents.review.base_review_agent import BaseReviewAgent
from agent_system.agent.registry import AgentRegistry
from agent_system.environments.env_package.review.state import normalize_review_update_payload
from agent_system.review_prompts import CRITIQUE_PROMPT


@AgentRegistry.register("Critique Agent")
class CritiqueAgent(BaseReviewAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("Critique Agent", CRITIQUE_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)

    def normalize_payload(self, payload: Dict[str, Any], env_obs: Dict[str, Any], item_idx: int) -> Dict[str, Any]:
        return normalize_review_update_payload(payload)
