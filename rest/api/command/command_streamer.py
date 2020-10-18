import json

from rest.utils.io_utils import IOUtils


class CommandStreamer:

    @staticmethod
    def stream_out_and_err(file):
        command_detached_response = json.loads(IOUtils.read_file(file))

        return command_detached_response