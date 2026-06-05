from __future__ import annotations

from typing import Any, Dict

from transformers import PreTrainedTokenizer

from agent_system.agent.agents.review.manager_agent import MANAGER_PROMPT
from agent_system.agent.agents.review.base_review_agent import BaseReviewAgent
from agent_system.agent.registry import AgentRegistry
from agent_system.environments.env_package.review.state import normalize_manager_payload


@AgentRegistry.register("Meta Reviewer Agent")
class MetaReviewerAgent(BaseReviewAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("Meta Reviewer Agent", MANAGER_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)

    def normalize_payload(self, payload: Dict[str, Any], env_obs: Dict[str, Any], item_idx: int) -> Dict[str, Any]:
        available_workers = env_obs.get("available_workers", [[]])[item_idx]
        return normalize_manager_payload(payload, available_workers)


__all__ = ["MetaReviewerAgent"]
