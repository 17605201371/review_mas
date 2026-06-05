from __future__ import annotations

from typing import Any, Dict

from transformers import PreTrainedTokenizer

from agent_system.agent.agents.review.base_review_agent import BaseReviewAgent
from agent_system.agent.registry import AgentRegistry
from agent_system.environments.env_package.review.state import normalize_review_update_payload
from agent_system.review_prompts import GENERAL_REVIEWER_PROMPT


class _BaseGeneralReviewerAgent(BaseReviewAgent):
    def normalize_payload(self, payload: Dict[str, Any], env_obs: Dict[str, Any], item_idx: int) -> Dict[str, Any]:
        return normalize_review_update_payload(payload)


@AgentRegistry.register("Reviewer Agent")
class ReviewerAgent(_BaseGeneralReviewerAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("Reviewer Agent", GENERAL_REVIEWER_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)


@AgentRegistry.register("General Reviewer Agent 1")
class GeneralReviewerAgent1(_BaseGeneralReviewerAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("General Reviewer Agent 1", GENERAL_REVIEWER_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)


@AgentRegistry.register("General Reviewer Agent 2")
class GeneralReviewerAgent2(_BaseGeneralReviewerAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("General Reviewer Agent 2", GENERAL_REVIEWER_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)


@AgentRegistry.register("General Reviewer Agent 3")
class GeneralReviewerAgent3(_BaseGeneralReviewerAgent):
    def __init__(self, wg_id: str, tokenizer: PreTrainedTokenizer, processor, config: Any):
        super().__init__("General Reviewer Agent 3", GENERAL_REVIEWER_PROMPT, wg_id=wg_id, tokenizer=tokenizer, processor=processor, config=config)
