from rest.api.constants.env_constants import EnvConstants
from rest.environment.environment import Environment


class EnvStartup:
    __instance = None
    __env = Environment.get_instance()

    @staticmethod
    def get_instance():
        if EnvStartup.__instance is None:
            EnvStartup()
        return EnvStartup.__instance

    def __init__(self):
        if EnvStartup.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            EnvStartup.__instance = {
                EnvConstants.APP_IP_PORT: EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.APP_IP_PORT).strip().lower() if EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.APP_IP_PORT) else None,
                EnvConstants.PORT: int(EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.PORT).strip()) if EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.PORT) is not None else 8080,
                EnvConstants.EUREKA_SERVER: EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.EUREKA_SERVER).strip() if EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.EUREKA_SERVER) else None,
                EnvConstants.FLUENTD_IP_PORT: EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.FLUENTD_IP_PORT).strip() if EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.FLUENTD_IP_PORT) else None,
                EnvConstants.HTTP_AUTH_TOKEN: EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.HTTP_AUTH_TOKEN).strip() if EnvStartup.__env.get_env_and_virtual_env().get(
                    EnvConstants.HTTP_AUTH_TOKEN) else "None"
            }
