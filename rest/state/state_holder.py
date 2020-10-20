from rest.api.constants.env_init import EnvInit


class StateHolder:
    __command = EnvInit.COMMAND_DETACHED_FILENAME.format("_")

    @staticmethod
    def get_last_command():
        return StateHolder.__command

    @staticmethod
    def set_last_command(id):
        StateHolder.__command = EnvInit.COMMAND_DETACHED_FILENAME.format(id)
