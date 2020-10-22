import base64

from rest.api.constants.env_init import EnvInit


class CommandHasher:
    @staticmethod
    def get_cmd_for_file_encode_list(command, cmd_id, suffix):
        return EnvInit.CMD_DETACHED_STREAMS + "/" + \
               base64.b64encode(command[0].encode("UTF-8")).decode("UTF-8") + "_" + cmd_id + suffix

    @staticmethod
    def get_cmd_for_file_encode_str(command, cmd_id, suffix):
        return EnvInit.CMD_DETACHED_STREAMS + "/" + \
               base64.b64encode(command.encode("UTF-8")).decode("UTF-8") + "_" + cmd_id + suffix

    @staticmethod
    def get_cmd_for_file_decode(command):
        return ""
