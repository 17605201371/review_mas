import asyncio
import concurrent.futures
import copy
from typing import Any, Dict, List, Optional

try:
    from omegaconf import OmegaConf
except ModuleNotFoundError:  # pragma: no cover
    class _OmegaConfShim:
        @staticmethod
        def select(config, key, default=None):
            return default

    OmegaConf = _OmegaConfShim()

from agent_system.environments.env_package.review.reward import compute_review_reward, _extract_decision
from agent_system.environments.env_package.review.state import (
    build_review_task,
    build_state_audit,
    build_turn_log,
    infer_final_decision,
    maybe_write_turn_log,
    merge_review_state,
    parse_turn_action,
    render_final_review,
    render_user_report,
)

_DEBUG_REWARD_PRINTS = 0


class ReviewEnv:
    def __init__(self, max_turns: int, mode: str, log_dir: Optional[str] = None):
        self.max_turns = max_turns
        self.mode = mode
        self.log_dir = log_dir
        self.done = False
        self.task: Dict[str, Any] | None = None
        self.last_info: Dict[str, Any] | None = None

    def reset(self, extras: Dict[str, Any]):
        self.task = build_review_task(extras, mode=self.mode, max_turns=self.max_turns)
        self.done = False
        self.last_info = None

    def _current_obs(self) -> Dict[str, Any]:
        assert self.task is not None
        return {
            "paper_id": self.task["paper_id"],
            "paper_text": self.task["paper_text"],
            "user_goal": self.task["user_goal"],
            "data_source": self.task["data_source"],
            "max_turns": self.task["max_turns"],
            "mode": self.task["mode"],
            "review_state": self.task["review_state"],
            "turn_logs": self.task["turn_logs"],
        }

    def step(self, action: str):
        global _DEBUG_REWARD_PRINTS
        assert self.task is not None

        if self.done:
            return self._current_obs(), 0.0, True, self.last_info or {
                "data_source": self.task["data_source"],
                "won": False,
                "decision_correct": 0.0,
                "accept_reject_correct": 0.0,
            }

        parsed_action = None
        parse_error = ""
        try:
            parsed_action = parse_turn_action(action, available_agents=None)
        except ValueError as exc:
            parse_error = str(exc)

        manager_payload = (
            parsed_action["manager"]
            if parsed_action is not None
            else {
                "decision": "continue",
                "selected_agents": [],
                "focus": "",
                "rationale": parse_error,
                "dialogue_summary": "",
                "unresolved_questions": [],
                "claims": [],
                "evidence_map": [],
                "flaw_candidates": [],
                "recommendation": "undecided",
                "final_decision": "undecided",
                "final_report": "",
            }
        )
        worker_payloads = parsed_action["workers"] if parsed_action is not None else []

        state = self.task["review_state"]
        previous_phase = str(state.get("phase") or "normal_review").strip().lower() or "normal_review"
        previous_phase_turn_index = int(state.get("phase_turn_index", 0) or 0)
        turn_revision_events = []
        turn_conflict_events = []

        previous_revision_count = len(state.get("revision_log", []))
        previous_conflict_count = len(state.get("conflict_notes", []))
        state = merge_review_state(state, manager_payload)
        turn_revision_events.extend(copy.deepcopy(state.get("revision_log", [])[previous_revision_count:]))
        turn_conflict_events.extend(copy.deepcopy(state.get("conflict_notes", [])[previous_conflict_count:]))
        # Merge ordinary evidence/flaw payloads before recovery patches so a
        # same-turn patch can cite evidence produced by Evidence Agent. If more
        # than one worker emits a recovery patch, keep only the safest candidate
        # for state mutation; otherwise a later bad patch can overwrite the
        # successful patch log from an earlier verified-negative patch.
        ordinary_worker_payloads = []
        recovery_worker_payloads = []
        for worker in worker_payloads:
            payload = worker.get("payload", {}) or {}
            if payload.get("action") in {"apply_recovery_patch", "blocked"}:
                recovery_worker_payloads.append(worker)
            else:
                ordinary_worker_payloads.append(worker)

        def _recovery_worker_priority(worker: Dict[str, Any]) -> tuple[int, int, int]:
            payload = worker.get("payload", {}) or {}
            source = str(payload.get("_recovery_patch_source") or payload.get("recovery_patch_source") or "")
            action = str(payload.get("action") or "")
            evidence_ids = payload.get("supporting_evidence_ids", []) or []
            return (
                1 if action == "apply_recovery_patch" else 0,
                1 if "system_salvaged" in source else 0,
                1 if any("negative-quote-bank" in str(eid) for eid in evidence_ids) else 0,
            )

        selected_recovery_payloads = []
        if recovery_worker_payloads:
            selected_recovery_payloads = [max(recovery_worker_payloads, key=_recovery_worker_priority)]
        ordered_worker_payloads = ordinary_worker_payloads + selected_recovery_payloads
        for worker in ordered_worker_payloads:
            previous_revision_count = len(state.get("revision_log", []))
            previous_conflict_count = len(state.get("conflict_notes", []))
            state = merge_review_state(state, worker["payload"])
            turn_revision_events.extend(copy.deepcopy(state.get("revision_log", [])[previous_revision_count:]))
            turn_conflict_events.extend(copy.deepcopy(state.get("conflict_notes", [])[previous_conflict_count:]))

        turn_id = int(state.get("turn_id", 0)) + 1
        state["turn_id"] = turn_id
        state["mode"] = self.task["mode"]
        state["last_focus"] = manager_payload.get("focus", "")
        phase_after_action = str(manager_payload.get("phase") or previous_phase or "normal_review").strip().lower() or "normal_review"
        if phase_after_action not in {"normal_review", "recovery"}:
            phase_after_action = "normal_review"
        phase_turn_index = int(manager_payload.get("phase_turn_index", 0) or 0)
        if phase_turn_index <= 0:
            phase_turn_index = previous_phase_turn_index + 1 if phase_after_action == previous_phase else 1
        state["phase"] = phase_after_action
        state["phase_turn_index"] = phase_turn_index
        state["phase_enter_reason"] = str(manager_payload.get("phase_enter_reason") or "")
        state["phase_exit_reason"] = str(manager_payload.get("phase_exit_reason") or "")
        state["phase_hold_reason"] = str(manager_payload.get("phase_hold_reason") or "")
        state["sticky_target_id"] = str(manager_payload.get("sticky_target_id") or "")
        state["sticky_target_type"] = str(manager_payload.get("sticky_target_type") or "")
        state["sticky_target_active"] = bool(manager_payload.get("sticky_target_active", False))
        state["sticky_target_applied"] = bool(manager_payload.get("sticky_target_applied", False))
        state["sticky_target_reused"] = bool(manager_payload.get("sticky_target_reused", False))
        state["sticky_target_released"] = bool(manager_payload.get("sticky_target_released", False))
        state["sticky_release_reason"] = str(manager_payload.get("sticky_release_reason") or "")
        state["target_switch_blocked_by_sticky"] = bool(manager_payload.get("target_switch_blocked_by_sticky", False))
        state["sticky_target_turns_remaining"] = int(manager_payload.get("sticky_target_turns_remaining", 0) or 0)

        done = manager_payload.get("decision") == "finalize" or turn_id >= self.task["max_turns"]
        reward = 0.0
        reward_breakdown = {}
        final_report = ""
        decision_correct = 0.0
        accept_reject_correct = 0.0
        review_log_path = None

        if done:
            final_decision = infer_final_decision(state, manager_payload)
            state["final_decision"] = final_decision
            # ``final_report`` is the user-facing artifact.  Machine-readable
            # recommendation labels, binary decision health checks, and hygiene
            # counters live in ``state_audit`` so paper-facing reports cannot be
            # mistaken for an automatic accept/reject judgement.
            final_report = render_user_report(state, manager_payload)
            state["final_report"] = final_report
            state["user_report"] = final_report
            state["state_audit"] = build_state_audit(state, manager_payload)
            reward, reward_breakdown = compute_review_reward(
                prediction=final_report,
                ground_truth=self.task["ground_truth_decision"],
                reference_review=self.task["reference_review"],
                reviewer_comments=self.task["reviewer_comments"],
                reference_ratings=self.task["reference_ratings"],
                review_state=state,
            )
            predicted_decision = _extract_decision(final_report)
            decision_correct = float(predicted_decision == self.task["ground_truth_decision"])
            accept_reject_correct = float(
                predicted_decision in {"accept", "reject"} and predicted_decision == self.task["ground_truth_decision"]
            )
            if _DEBUG_REWARD_PRINTS < 8:
                _DEBUG_REWARD_PRINTS += 1
                print(
                    f"[review_reward][{self.task['data_source']}][{self.task['paper_id']}] "
                    f"reward={reward:.4f} breakdown={reward_breakdown}"
                )

        previous_action_type = self.task["turn_logs"][-1].get("action_type", "") if self.task["turn_logs"] else ""
        turn_log = build_turn_log(
            turn_id,
            manager_payload,
            worker_payloads,
            state,
            final_report=final_report,
            revision_events=turn_revision_events,
            conflict_events=turn_conflict_events,
            previous_action_type=previous_action_type,
        )
        self.task["turn_logs"].append(turn_log)
        state.pop("_transient_status_locks", None)
        self.task["review_state"] = state

        if done:
            review_log_path = maybe_write_turn_log(self.log_dir, self.task, self.task["turn_logs"])

        obs = self._current_obs()
        info = {
            "data_source": self.task["data_source"],
            "won": bool(done and reward >= 0.6),
            "reward_breakdown": reward_breakdown,
            "decision_correct": decision_correct,
            "accept_reject_correct": accept_reject_correct,
            "turn_log": turn_log,
            "turn_id": turn_id,
            "review_state": state,
            "revision_events": turn_revision_events,
            "conflict_events": turn_conflict_events,
            "review_logs": self.task["turn_logs"],
            "review_log_path": review_log_path,
            "final_report": final_report,
            "parse_error": parse_error,
        }
        self.done = done
        self.last_info = info
        return obs, reward, done, info

    def close(self):
        pass


class ReviewMultiProcessEnv:
    def __init__(
        self,
        seed: int = 0,
        env_num: int = 1,
        group_n: int = 1,
        is_train: bool = True,
        env_config=None,
        review_mode: str = "s4",
    ):
        self.env_num = env_num
        self.group_n = group_n
        self.batch_size = env_num * group_n
        self.max_turns = int(getattr(env_config, "max_steps", 1))
        self.log_dir = OmegaConf.select(env_config, "review.log_dir", default=None) if env_config is not None else None
        self.envs = [
            ReviewEnv(max_turns=self.max_turns, mode=review_mode, log_dir=self.log_dir)
            for _ in range(self.batch_size)
        ]
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(self.batch_size, 256))
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def _sync_reset(self, env, kwargs):
        env.reset(kwargs)
        task = env._current_obs()
        return task, {"data_source": task.get("data_source", "unknown")}

    def _sync_step(self, env, action: str):
        return env.step(action)

    def reset(self, kwargs: List[Dict]):
        if len(kwargs) > self.batch_size:
            raise ValueError(f"Got {len(kwargs)} kwarg dicts, but the env was initialised with total_envs={self.batch_size}")

        pad_n = self.batch_size - len(kwargs)
        dummy_kw = {
            "paper_id": "dummy-paper",
            "paper_text": "",
            "data_source": "unknown",
            "ground_truth_decision": "",
        }
        padded_kwargs = list(kwargs) + [dummy_kw] * pad_n
        valid_mask = [True] * len(kwargs) + [False] * pad_n

        tasks = [
            self._loop.run_in_executor(self._executor, self._sync_reset, env, kw)
            for env, kw in zip(self.envs, padded_kwargs)
        ]
        results = self._loop.run_until_complete(asyncio.gather(*tasks))
        obs_list, info_list = map(list, zip(*results))
        obs_list = [obs for obs, keep in zip(obs_list, valid_mask) if keep]
        info_list = [info for info, keep in zip(info_list, valid_mask) if keep]
        return obs_list, info_list

    def step(self, actions: List[str]):
        if len(actions) > self.batch_size:
            raise ValueError(f"Got {len(actions)} actions, but the env was initialized with total_envs={self.batch_size}")

        pad_n = self.batch_size - len(actions)
        padded_actions = list(actions) + [""] * pad_n
        valid_mask = [True] * len(actions) + [False] * pad_n

        tasks = [
            self._loop.run_in_executor(self._executor, self._sync_step, env, act)
            for env, act in zip(self.envs, padded_actions)
        ]
        results = self._loop.run_until_complete(asyncio.gather(*tasks))

        obs_list, reward_list, done_list, info_list = map(list, zip(*results))
        obs_list = [obs for obs, keep in zip(obs_list, valid_mask) if keep]
        reward_list = [reward for reward, keep in zip(reward_list, valid_mask) if keep]
        done_list = [done for done, keep in zip(done_list, valid_mask) if keep]
        info_list = [info for info, keep in zip(info_list, valid_mask) if keep]
        return obs_list, reward_list, done_list, info_list

    def close(self):
        self._executor.shutdown()
        self._loop.close()


def build_review_envs(seed=0, env_num=1, group_n=1, is_train=True, env_config=None, review_mode: str = "s4"):
    return ReviewMultiProcessEnv(
        seed=seed,
        env_num=env_num,
        group_n=group_n,
        is_train=is_train,
        env_config=env_config,
        review_mode=review_mode,
    )
