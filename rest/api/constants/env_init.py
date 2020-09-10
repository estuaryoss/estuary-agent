from rest.api.constants.env_constants import EnvConstants
from rest.environment.environment import Environment


class EnvInit:
    # env constants
    WORKSPACE = "tmp"
    env = Environment.get_instance()
    if env.get_env_and_virtual_env().get(EnvConstants.WORKSPACE):
        WORKSPACE = env.get_env_and_virtual_env().get(EnvConstants.WORKSPACE)
    # take paths from env if they exists
    TEMPLATES_DIR = env.get_env_and_virtual_env().get(
        EnvConstants.TEMPLATES_DIR) if env.get_env_and_virtual_env().get(
        EnvConstants.TEMPLATES_DIR) else WORKSPACE + "/templates"
    VARS_DIR = env.get_env_and_virtual_env().get(
        EnvConstants.VARS_DIR) if env.get_env_and_virtual_env().get(
        EnvConstants.VARS_DIR) else WORKSPACE + "/variables"

    if not env.get_env_and_virtual_env().get(EnvConstants.VARS_DIR):
        env.set_env_var(EnvConstants.VARS_DIR, VARS_DIR)
        print(
            f"{EnvConstants.VARS_DIR} env var not set, defaulting to : " + env.get_env_and_virtual_env().get(
                EnvConstants.VARS_DIR))

    if not env.get_env_and_virtual_env().get(EnvConstants.TEMPLATES_DIR):
        env.set_env_var(EnvConstants.TEMPLATES_DIR, TEMPLATES_DIR)
        print(
            f"{EnvConstants.TEMPLATES_DIR} env var not set, defaulting to : " + env.get_env_and_virtual_env().get(
                EnvConstants.TEMPLATES_DIR))

    COMMAND_DETACHED_FILENAME = "command_detached_info.json"
