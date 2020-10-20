#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

from rest.api.command.command import Command
from rest.api.constants.env_init import EnvInit
from rest.api.definitions import command_detached_init
from rest.utils.io_utils import IOUtils

if __name__ == '__main__':
    io_utils = IOUtils()
    command_logger_path = "command_info_logger.txt"

    io_utils.append_to_file(command_logger_path, " ".join(sys.argv[:-1]) + f" \"{sys.argv[-1]}\"")

    min_args = 3
    if len(sys.argv) < min_args:
        raise Exception(
            "Error: Expecting at least {} args. Got {}, args={}".format(min_args, len(sys.argv), sys.argv))

    IOUtils.create_dir(EnvInit.CMD_DETACHED_DIR)
    IOUtils.create_dir(EnvInit.CMD_DETACHED_STREAMS)

    command_id = sys.argv[1]
    commands_list = sys.argv[2].split(";")
    file_path = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)

    try:
        command_detached_init["pid"] = os.getpid()
        io_utils.write_to_file_dict(Path(file_path), command_detached_init)
    except Exception as e:
        raise e

    command_runner = Command()
    dictionary = command_runner.run_commands(file_path, command_id, commands_list)
    dictionary = io_utils.read_dict_from_file(file_path)

    print(json.dumps(dictionary) + "\n")
