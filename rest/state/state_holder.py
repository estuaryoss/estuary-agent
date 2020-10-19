from rest.api.constants.env_init import EnvInit


class StateHolder:
    __state = {"last_command": EnvInit.COMMAND_DETACHED_FILENAME.format("_")}

    @staticmethod
    def get_last_command():
        return StateHolder.__state.get("last_command")

    @staticmethod
    def set_last_command(attr_value):
        StateHolder.__state["last_command"] = attr_value
