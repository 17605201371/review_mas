try:
    from agent_system.environments.env_manager import EnvironmentManagerBase, make_envs
except ModuleNotFoundError:  # pragma: no cover
    EnvironmentManagerBase = None
    make_envs = None
