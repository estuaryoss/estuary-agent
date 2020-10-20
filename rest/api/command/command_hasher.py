import base64
import json

from rest.api.constants.env_init import EnvInit


class CommandHasher:
    @staticmethod
    def get_cmd_for_file_encode_list(command, suffix):
        return EnvInit.CMD_DETACHED_STREAMS + "/" + \
               base64.b64encode(command[0].encode("UTF-8")).decode("UTF-8") + suffix

    @staticmethod
    def get_cmd_for_file_encode_str(command, suffix):
        return EnvInit.CMD_DETACHED_STREAMS + "/" + \
               base64.b64encode(command.encode("UTF-8")).decode("UTF-8") + suffix

    @staticmethod
    def get_cmd_for_file_decode(command):
        return ""
