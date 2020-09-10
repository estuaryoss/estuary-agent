import os


class Environment:
    __VIRTUAL_ENV_MAX_SIZE = 50
    __instance = None
    __env = os.environ.copy()
    __virtual_env = {}

    @staticmethod
    def get_instance():
        if Environment.__instance is None:
            Environment()
        return Environment.__instance

    def __init__(self):
        """

        The constructor. This class keeps system env vars plus the virtual env vars set by the user.
        These env vars are then passed to the subprocess call.
        """

        if Environment.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Environment.__instance = self

    @staticmethod
    def set_env_var(key, value):
        if key not in Environment.__instance.__env and len(
                Environment.__instance.__virtual_env) <= Environment.__VIRTUAL_ENV_MAX_SIZE:
            Environment.__instance.__virtual_env[key] = value

    @staticmethod
    def get_env():
        return Environment.__env

    @staticmethod
    def get_virtual_env():
        return Environment.__virtual_env

    @staticmethod
    def get_env_and_virtual_env():
        return {**Environment.__env, **Environment.__virtual_env}
