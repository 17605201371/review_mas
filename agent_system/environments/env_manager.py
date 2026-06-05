import copy
from typing import List, Tuple, Dict, Union, Any
from collections import defaultdict
import torch
import numpy as np
from functools import partial
import os
from omegaconf import OmegaConf
from agent_system.environments.prompts import *
from agent_system.environments.base import EnvironmentManagerBase, to_numpy
from agent_system.environments.env_package.review.state import infer_review_mode, render_review_observation
from agent_system.memory import SimpleMemory, SearchMemory

import time

class SearchEnvironmentManager(EnvironmentManagerBase):
    """
    EnvironmentManager for SearchEnv.
    """
    def __init__(self, envs, projection_f, config):
        self.memory = SearchMemory()
        super().__init__(envs, projection_f, config)

    def reset(self, kwargs) -> Tuple[Dict[str, Any], List[Dict]]:
        obs, infos = self.envs.reset(kwargs=kwargs)
        self.tasks = obs

        self.memory.reset(batch_size=len(obs))

        observations = {
            "text": self.build_text_obs(obs, init=True),
            "image": None,
            "anchor": obs.copy()
        }
        
        return observations, infos

    def step(self, text_actions: List[str]):
        if not self.config.agent.multi_agent:
            actions, valids = self.projection_f(text_actions)
        else:
            actions = text_actions

        time1 = time.time()
        next_obs, rewards, dones, infos = self.envs.step(actions)
        time2 = time.time()
        print(f"SearchEnv step time: {time2 - time1:.4f} seconds")

        self.memory.store({
            "search": actions,
            "information": next_obs,
        })

        next_observations = {
            "text": self.build_text_obs(next_obs),
            "image": None,
            "anchor": next_obs.copy()
        }
        
        if not self.config.agent.multi_agent:
            for i, info in enumerate(infos):
                info["is_action_valid"] = to_numpy(valids[i])

        rewards = to_numpy(rewards)
        dones = to_numpy(dones)

        return next_observations, rewards, dones, infos

    def build_text_obs(
        self,
        text_obs: List[str],
        init: bool = False
    ) -> List[str]:
        postprocess_text_obs: List[str] = []

        if not init and self.config.env.history_length > 0:
            memory_ctx, _ = self.memory.fetch(
                self.config.env.history_length,
                obs_key="information",
                action_key="search"
            )

        for i in range(len(text_obs)):
            if init or self.config.env.history_length <= 0:
                if self.config.agent.multi_agent:
                    obs_i = SEARCH_MULTIAGENT_TEMPLATE_NO_HIS.format(
                        task_description=self.tasks[i]
                    )
                else:
                    obs_i = SEARCH_TEMPLATE_NO_HIS.format(
                        task_description=self.tasks[i]
                    )
            else:
                if self.config.agent.multi_agent:
                    obs_i = SEARCH_MULTIAGENT_TEMPLATE.format(
                        task_description=self.tasks[i],
                        memory_context="{memory}" if self.config.agent.use_agent_memory else memory_ctx[i],
                        step_count=len(self.memory[i]),
                    )
                else:
                    obs_i = SEARCH_TEMPLATE.format(
                        task_description=self.tasks[i],
                        memory_context=memory_ctx[i],
                        step_count=len(self.memory[i]),
                    )
            postprocess_text_obs.append(obs_i)

        return postprocess_text_obs

    def _process_batch(self, batch_idx, total_batch_list, total_infos, success):
        # Find the last entry with active masks
        for i in reversed(range(len(total_batch_list[batch_idx]))):
            batch_item = total_batch_list[batch_idx][i]
            if batch_item['active_masks']:
                info = total_infos[batch_idx][i]
                won_value = float(info['won'])
                success['success_rate'].append(won_value)
                
                # Process game file if it exists
                data_source = info.get("data_source")
                success[f"{data_source}_success_rate"].append(won_value)
                return  # Exit after finding the first active mask
            


class MathEnvironmentManager(EnvironmentManagerBase):
    """
    EnvironmentManager for MathEnv.
    """
    def __init__(self, envs, projection_f, config):
        super().__init__(envs, projection_f, config)

    def reset(self, kwargs) -> Tuple[Dict[str, Any], List[Dict]]:
        obs, infos = self.envs.reset(kwargs=kwargs)
        self.tasks = obs

        observations = {
            "text": self.build_text_obs(obs),
            "image": None,
            "anchor": obs.copy()
        }
        
        return observations, infos

    def step(self, text_actions: List[str]):
        if not self.config.agent.multi_agent:
            actions, valids = self.projection_f(text_actions)
        else:
            actions = text_actions

        time1 = time.time()
        next_obs, rewards, dones, infos = self.envs.step(actions)
        time2 = time.time()
        print(f"MathEnv step time: {time2 - time1:.4f} seconds")

        next_observations = {
            "text": None,
            "image": None,
            "anchor": None
        }
        
        if not self.config.agent.multi_agent:
            for i, info in enumerate(infos):
                info["is_action_valid"] = to_numpy(valids[i])

        rewards = to_numpy(rewards)
        dones = to_numpy(dones)

        return next_observations, rewards, dones, infos

    def build_text_obs(
        self,
        text_obs: List[str],
    ) -> List[str]:
        postprocess_text_obs: List[str] = []

        for i in range(len(text_obs)):
            if self.config.agent.multi_agent:
                obs_i = MATH_MULTIAGENT_TEMPLATE.format(
                    task_description=self.tasks[i]
                )
            else:
                obs_i = MATH_TEMPLATE.format(
                    task_description=self.tasks[i]
                )
            postprocess_text_obs.append(obs_i)

        return postprocess_text_obs

    def _process_batch(self, batch_idx, total_batch_list, total_infos, success):
        # Find the last entry with active masks
        for i in reversed(range(len(total_batch_list[batch_idx]))):
            batch_item = total_batch_list[batch_idx][i]
            if batch_item['active_masks']:
                info = total_infos[batch_idx][i]
                won_value = float(info['won'])
                success['success_rate'].append(won_value)
                
                # Process game file if it exists
                data_source = info.get("data_source")
                success[f"{data_source}_success_rate"].append(won_value)
                return  # Exit after finding the first active mask

class ReviewEnvironmentManager(EnvironmentManagerBase):
    """
    EnvironmentManager for ReviewEnv.
    """
    def __init__(self, envs, projection_f, config):
        super().__init__(envs, projection_f, config)

    def reset(self, kwargs) -> Tuple[Dict[str, Any], List[Dict]]:
        obs, infos = self.envs.reset(kwargs=kwargs)
        self.tasks = obs

        observations = {
            "text": self.build_text_obs(obs),
            "image": None,
            "anchor": copy.deepcopy(obs),
            "review_state": [copy.deepcopy(item["review_state"]) for item in obs],
            "review_task": copy.deepcopy(obs),
            "turn_logs": [copy.deepcopy(item.get("turn_logs", [])) for item in obs],
        }
        
        return observations, infos

    def step(self, text_actions: List[str]):
        if not self.config.agent.multi_agent:
            actions, valids = self.projection_f(text_actions)
        else:
            actions = text_actions

        time1 = time.time()
        next_obs, rewards, dones, infos = self.envs.step(actions)
        time2 = time.time()
        print(f"ReviewEnv step time: {time2 - time1:.4f} seconds")

        self.tasks = next_obs
        next_observations = {
            "text": self.build_text_obs(next_obs),
            "image": None,
            "anchor": copy.deepcopy(next_obs),
            "review_state": [copy.deepcopy(item["review_state"]) for item in next_obs],
            "review_task": copy.deepcopy(next_obs),
            "turn_logs": [copy.deepcopy(item.get("turn_logs", [])) for item in next_obs],
        }
        
        if not self.config.agent.multi_agent:
            for i, info in enumerate(infos):
                info["is_action_valid"] = to_numpy(valids[i])

        rewards = to_numpy(rewards)
        dones = to_numpy(dones)

        return next_observations, rewards, dones, infos

    def build_text_obs(
        self,
        text_obs: List[str],
    ) -> List[str]:
        return [render_review_observation(item) for item in text_obs]

    def _process_batch(self, batch_idx, total_batch_list, total_infos, success):
        # Find the last entry with active masks
        for i in reversed(range(len(total_batch_list[batch_idx]))):
            batch_item = total_batch_list[batch_idx][i]
            if batch_item['active_masks']:
                info = total_infos[batch_idx][i]
                won_value = float(info['won'])
                success['success_rate'].append(won_value)

                data_source = info.get("data_source")
                success[f"{data_source}_success_rate"].append(won_value)

                decision_correct = float(info.get("decision_correct", 0.0))
                accept_reject_correct = float(info.get("accept_reject_correct", 0.0))
                success['decision_correct'].append(decision_correct)
                success['accept_reject_correct'].append(accept_reject_correct)
                success[f"{data_source}_decision_correct"].append(decision_correct)
                success[f"{data_source}_accept_reject_correct"].append(accept_reject_correct)
                return  # Exit after finding the first active mask

def make_envs(config):
    """
    Create enviroments 
    """ 
    # check if config.env.rollout.n is an integer
    if not isinstance(config.env.rollout.n, int):
        raise ValueError("config.env.rollout.n should be an integer")
    group_n = config.env.rollout.n if config.env.rollout.n > 0 else 1
    # Get validation rollout n for pass@k and avg@k computation
    val_group_n = getattr(config.env.rollout, 'val_n', 1)

    if "math" in config.env.env_name.lower():
        from agent_system.environments.env_package.math import build_math_envs, math_projection
        _envs = build_math_envs(seed=config.env.seed, env_num=config.data.train_batch_size, group_n=group_n, is_train=True)
        _val_envs = build_math_envs(seed=config.env.seed + 1000, env_num=config.data.val_batch_size, group_n=val_group_n, is_train=False)
        
        projection_f = partial(math_projection)
        envs = MathEnvironmentManager(_envs, projection_f, config)
        val_envs = MathEnvironmentManager(_val_envs, projection_f, config)
        return envs, val_envs
    elif "search" in config.env.env_name.lower():
        from agent_system.environments.env_package.search import build_search_envs, search_projection
        _envs = build_search_envs(seed=config.env.seed, env_num=config.data.train_batch_size, group_n=group_n, is_train=True, env_config=config.env)
        _val_envs = build_search_envs(seed=config.env.seed + 1000, env_num=config.data.val_batch_size, group_n=val_group_n, is_train=False, env_config=config.env)

        projection_f = partial(search_projection)
        envs = SearchEnvironmentManager(_envs, projection_f, config)
        val_envs = SearchEnvironmentManager(_val_envs, projection_f, config)
        return envs, val_envs
    elif "review" in config.env.env_name.lower():
        from agent_system.environments.env_package.review import build_review_envs, review_projection
        review_mode = infer_review_mode(
            OmegaConf.select(config, "agent.orchestra.review.mode", default=None),
            config.agent.agent_ids,
            config.env.max_steps,
        )
        _envs = build_review_envs(
            seed=config.env.seed,
            env_num=config.data.train_batch_size,
            group_n=group_n,
            is_train=True,
            env_config=config.env,
            review_mode=review_mode,
        )
        _val_envs = build_review_envs(
            seed=config.env.seed + 1000,
            env_num=config.data.val_batch_size,
            group_n=val_group_n,
            is_train=False,
            env_config=config.env,
            review_mode=review_mode,
        )

        projection_f = partial(review_projection)
        envs = ReviewEnvironmentManager(_envs, projection_f, config)
        val_envs = ReviewEnvironmentManager(_val_envs, projection_f, config)
        return envs, val_envs
    else:
        print("Environment not supported")
        exit(1)
