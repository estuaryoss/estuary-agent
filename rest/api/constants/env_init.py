import os

from rest.api.constants.env_constants import EnvConstants


class EnvInit:
    # env constants
    WORKSPACE = "tmp"
    if os.environ.get(EnvConstants.WORKSPACE):
        WORKSPACE = os.environ.get(EnvConstants.WORKSPACE)
    # take paths from env if they exists
    TEMPLATES_DIR = os.environ.get(EnvConstants.TEMPLATES_DIR) if os.environ.get(
        EnvConstants.TEMPLATES_DIR) else WORKSPACE + "/templates"
    VARS_DIR = os.environ.get(EnvConstants.VARS_DIR) if os.environ.get(
        EnvConstants.VARS_DIR) else WORKSPACE + "/variables"

    if not os.environ.get(EnvConstants.VARS_DIR):
        os.environ[EnvConstants.VARS_DIR] = VARS_DIR
        print(f"{EnvConstants.VARS_DIR} env var not set, defaulting to : " + os.environ.get(EnvConstants.VARS_DIR))

    if not os.environ.get(EnvConstants.TEMPLATES_DIR):
        os.environ[EnvConstants.TEMPLATES_DIR] = TEMPLATES_DIR
        print(f"{EnvConstants.TEMPLATES_DIR} env var not set, defaulting to : " + os.environ.get(EnvConstants.TEMPLATES_DIR))

    COMMAND_DETACHED_FILENAME = "command_detached_info.json"
