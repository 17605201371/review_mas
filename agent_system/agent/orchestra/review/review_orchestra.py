from __future__ import annotations

import copy
import importlib
from typing import Any, Dict, List, Tuple

import numpy as np
from omegaconf import OmegaConf
from transformers import PreTrainedTokenizer
from verl import DataProto

from agent_system import review_manager_policy as review_policy
from agent_system.agent.orchestra.base import BaseOrchestra, update_team_context
from agent_system.environments.env_package.review.state import (
    build_turn_action,
    infer_review_mode,
)


class ReviewMultiAgentOrchestra(BaseOrchestra):
    MANAGER_CANDIDATES = ("Review Manager Agent", "Meta Reviewer Agent")

    def __init__(
        self,
        agent_ids: List[str],
        model_ids: List[str],
        agents_to_wg_mapping: Dict[str, str],
        tokenizers: Dict[str, PreTrainedTokenizer] = None,
        processors: Dict[str, Any] = None,
        config: Any = None,
    ):
        importlib.import_module("agent_system.agent.agents.review")
        super().__init__(
            agent_ids=agent_ids,
            model_ids=model_ids,
            agents_to_wg_mapping=agents_to_wg_mapping,
            tokenizers=tokenizers,
            processors=processors,
            config=config,
        )
        if not self.agents:
            raise ValueError("ReviewMultiAgentOrchestra requires at least one agent.")

        self.manager_agent_id = self._resolve_manager_agent_id(agent_ids)
        self.worker_agent_ids = [agent_id for agent_id in agent_ids if agent_id != self.manager_agent_id]
        explicit_mode = OmegaConf.select(config, "agent.orchestra.review.mode", default=None)
        self.mode = infer_review_mode(explicit_mode, agent_ids, int(getattr(config.env, "max_steps", 1)))
        self.max_workers_per_turn = int(
            OmegaConf.select(config, "agent.orchestra.review.max_workers_per_turn", default=max(1, len(self.worker_agent_ids)))
        )

    def _resolve_manager_agent_id(self, agent_ids: List[str]) -> str:
        for candidate in self.MANAGER_CANDIDATES:
            if candidate in agent_ids:
                return candidate
        if len(agent_ids) == 1:
            return agent_ids[0]
        raise ValueError("Review orchestra requires a manager agent. Use 'Review Manager Agent' or 'Meta Reviewer Agent'.")

    def _augment_obs(
        self,
        env_obs: Dict[str, Any],
        extra_sections: List[str],
        extra_fields: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        obs = copy.deepcopy(env_obs)
        obs["text"] = [
            f"{base_text}\n\n{extra_section}".strip()
            if extra_section else base_text
            for base_text, extra_section in zip(obs["text"], extra_sections)
        ]
        if extra_fields:
            for key, value in extra_fields.items():
                obs[key] = value
        return obs

    def _default_manager_payload(self, step: int) -> Dict[str, Any]:
        payload = review_policy.default_manager_payload()
        if not self.worker_agent_ids and step >= int(getattr(self.config.env, "max_steps", 1)):
            payload["decision"] = "finalize"
        return payload

    def run(
        self,
        gen_batch: DataProto,
        env_obs: Dict[str, Any],
        actor_rollout_wgs,
        active_masks: np.ndarray,
        step: int,
    ) -> Tuple[List[str], Dict[str, DataProto]]:
        self.reset_buffer()
        text_actions, team_context, env_obs = self.initialize_context(env_obs)
        batch_size = len(gen_batch)
        active_mask = active_masks.astype(bool)

        available_workers = [list(self.worker_agent_ids) for _ in range(batch_size)]
        review_states = env_obs.get("review_state") or [{} for _ in range(batch_size)]
        turn_logs_per_item = env_obs.get("turn_logs") or [[] for _ in range(batch_size)]
        allowed_actions = sorted(review_policy.mode_allowed_actions(self.mode))
        manager_sections = [
            (
                "# Manager Routing Context\n"
                f"Available worker agents: {', '.join(self.worker_agent_ids) if self.worker_agent_ids else 'none'}\n"
                f"Review mode: {self.mode}\n"
                f"Risk readiness: {(review_states[i] or {}).get('risk_profile', {}).get('readiness', 'not_ready')}\n"
                f"Active focus: {(review_states[i] or {}).get('active_focus', '')}\n"
                f"Open unresolved questions: {len([q for q in (review_states[i] or {}).get('unresolved_questions', []) if (not isinstance(q, dict)) or q.get('status', 'open') == 'open'])}\n"
                f"Evidence gaps: {len((review_states[i] or {}).get('evidence_gaps', []))}\n"
                f"Allowed action types: {', '.join(allowed_actions)}\n"
                "Choose the next review objective before routing workers or finalizing."
            )
            if active_mask[i] else ""
            for i in range(batch_size)
        ]
        manager_obs = self._augment_obs(
            env_obs,
            manager_sections,
            extra_fields={"available_workers": available_workers},
        )

        manager_rollout_wg = actor_rollout_wgs[self.agents_to_wg_mapping[self.manager_agent_id]]
        manager_batch, manager_texts = self.agents[self.manager_agent_id].call(
            gen_batch=gen_batch,
            env_obs=manager_obs,
            team_context=team_context,
            actor_rollout_wg=manager_rollout_wg,
            agent_active_mask=active_mask,
            step=step,
        )
        self.save_to_buffer(self.manager_agent_id, manager_batch)
        team_context = update_team_context(self.manager_agent_id, team_context, manager_texts, active_mask)

        manager_payloads = list(manager_batch.non_tensor_batch["json_payload"])
        for i in range(batch_size):
            if not active_mask[i]:
                continue
            if manager_payloads[i] is None:
                manager_payloads[i] = self._default_manager_payload(step)
            manager_payloads[i] = review_policy.apply_manager_policy_fallback(
                manager_payload=manager_payloads[i],
                state=review_states[i] or {},
                mode=self.mode,
                worker_ids=self.worker_agent_ids,
                worker_limit=self.max_workers_per_turn,
                recent_turn_logs=turn_logs_per_item[i] or [],
            )

        selected_per_item: List[List[str]] = []
        for i in range(batch_size):
            if not active_mask[i]:
                selected_per_item.append([])
                continue
            manager_payload = manager_payloads[i]
            selected_agents = manager_payload.get("selected_agents", [])[: self.max_workers_per_turn]
            manager_payload["selected_agents"] = selected_agents
            selected_per_item.append(selected_agents)

        worker_payloads_per_item: List[List[Dict[str, Any]]] = [[] for _ in range(batch_size)]
        for worker_agent_id in self.worker_agent_ids:
            worker_mask = np.array(
                [
                    active_mask[i] and worker_agent_id in selected_per_item[i]
                    for i in range(batch_size)
                ],
                dtype=bool,
            )
            if not worker_mask.any():
                continue

            worker_sections = []
            for i in range(batch_size):
                if not worker_mask[i]:
                    worker_sections.append("")
                    continue
                manager_payload = manager_payloads[i]
                worker_sections.append(
                    "# Manager Focus\n"
                    f"Action Type: {manager_payload.get('action_type', 'extract_claims')}\n"
                    f"Effective Action Type: {manager_payload.get('effective_action_type', manager_payload.get('action_type', 'extract_claims'))}\n"
                    f"Focus: {manager_payload.get('focus', '')}\n"
                    f"Rationale: {manager_payload.get('rationale', '')}\n"
                    f"Target Claim IDs: {manager_payload.get('target_claim_ids', [])}\n"
                    f"Target Flaw IDs: {manager_payload.get('target_flaw_ids', [])}\n"
                    f"Target Evidence IDs: {manager_payload.get('target_evidence_ids', [])}\n"
                    f"Target Hypotheses: {manager_payload.get('target_hypotheses', [])}\n"
                    f"Policy Source: {manager_payload.get('policy_source', 'manager_model')}\n"
                    f"Executed agent: {worker_agent_id}"
                )

            worker_obs = self._augment_obs(env_obs, worker_sections)
            worker_rollout_wg = actor_rollout_wgs[self.agents_to_wg_mapping[worker_agent_id]]
            worker_batch, worker_texts = self.agents[worker_agent_id].call(
                gen_batch=gen_batch,
                env_obs=worker_obs,
                team_context=team_context,
                actor_rollout_wg=worker_rollout_wg,
                agent_active_mask=worker_mask,
                step=step,
            )
            self.save_to_buffer(worker_agent_id, worker_batch)
            team_context = update_team_context(worker_agent_id, team_context, worker_texts, worker_mask)

            worker_payloads = list(worker_batch.non_tensor_batch["json_payload"])
            for i in range(batch_size):
                if worker_mask[i] and worker_payloads[i] is not None:
                    worker_payloads_per_item[i].append(
                        {
                            "agent_id": worker_agent_id,
                            "payload": worker_payloads[i],
                        }
                    )

        for i in range(batch_size):
            if not active_mask[i]:
                text_actions[i] = ""
                continue
            manager_payload, selected_workers = review_policy.apply_finalize_policy(
                manager_payload=manager_payloads[i],
                state=review_states[i] or {},
                mode=self.mode,
                step=step,
                turn_cap=int(getattr(self.config.env, "max_steps", 1)),
                worker_ids=self.worker_agent_ids,
                worker_limit=self.max_workers_per_turn,
                selected_workers=selected_per_item[i],
                worker_payloads=worker_payloads_per_item[i],
                recent_turn_logs=turn_logs_per_item[i] or [],
            )
            manager_payload.setdefault("policy_source", "manager_model")
            manager_payload.setdefault("policy_notes", [])
            manager_payload["selected_agents"] = list(selected_workers)
            manager_payload["effective_action_type"] = review_policy.infer_effective_action_type(
                manager_payload,
                worker_payloads_per_item[i],
            )
            manager_payloads[i] = manager_payload
            text_actions[i] = build_turn_action(
                manager_payload=manager_payloads[i],
                worker_payloads=worker_payloads_per_item[i],
                mode=self.mode,
                turn_id=step,
            )

        return text_actions, self.multiagent_batch_buffer
