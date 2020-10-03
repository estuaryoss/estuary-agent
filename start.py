#!/usr/bin/env python3
import json
import sys

from rest.api.command.command import Command
from rest.api.constants.env_init import EnvInit
from rest.utils.io_utils import IOUtils

if __name__ == '__main__':
    io_utils = IOUtils()
    command_logger_path = "command_info_logger.txt"
    file_path = EnvInit.COMMAND_DETACHED_FILENAME

    io_utils.append_to_file(command_logger_path, " ".join(sys.argv[:-1]) + f" \"{sys.argv[-1]}\"")

    min_args = 3
    if len(sys.argv) < min_args:
        raise Exception(
            "Error: Expecting at least {} args. Got {}, args={}".format(min_args, len(sys.argv), sys.argv))

    test_id = sys.argv[1]
    commands_list = sys.argv[2].split(";")

    test_runner = Command()
    dictionary = test_runner.run_commands(file_path, test_id, commands_list)
    dictionary = io_utils.read_dict_from_file(file_path)

    print(json.dumps(dictionary) + "\n")
