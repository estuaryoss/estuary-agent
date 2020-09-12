from rest.api import AppCreatorSingleton
from rest.api.constants.env_constants import EnvConstants
from rest.environment.environment import EnvironmentSingleton


class EnvInit:
    WORKSPACE = "tmp"
    env = EnvironmentSingleton.get_instance()
    app = AppCreatorSingleton.get_instance().get_app()

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
        app.logger.debug({"msg":
                              f"{EnvConstants.VARS_DIR} env var not set, defaulting to : " + env.get_env_and_virtual_env().get(
                                  EnvConstants.VARS_DIR)})

    if not env.get_env_and_virtual_env().get(EnvConstants.TEMPLATES_DIR):
        env.set_env_var(EnvConstants.TEMPLATES_DIR, TEMPLATES_DIR)
        app.logger.debug({"msg":
                              f"{EnvConstants.TEMPLATES_DIR} env var not set, defaulting to : " + env.get_env_and_virtual_env().get(
                                  EnvConstants.TEMPLATES_DIR)})

    COMMAND_DETACHED_FILENAME = "command_detached_info.json"
