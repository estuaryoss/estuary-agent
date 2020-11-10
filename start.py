#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

import click

from rest.api.command.command import Command
from rest.api.constants.env_init import EnvInit
from rest.api.definitions import command_detached_init
from rest.utils.io_utils import IOUtils

@click.command()
@click.option('--cid', help="The id of the command. E.g. 5")
@click.option('--args', help="The arguments of the command separated by ';;'. E.g. ls -lrt;;echo3")
def cli(cid, args):
    if cid is None:
        raise Exception(f"Error: --id argument was not set. Value: {str(cid)}")

    if args is None:
        raise Exception(f"Error: --args argument was not set. Value: {str(args)}")

    io_utils = IOUtils()
    command_logger_path = "command_info_logger.txt"

    io_utils.append_to_file(command_logger_path, f"{sys.argv[0]} --id {cid} --args {args}")
    IOUtils.create_dir(EnvInit.CMD_DETACHED_DIR)
    IOUtils.create_dir(EnvInit.CMD_DETACHED_STREAMS)

    command_id = cid
    commands_list = args.split(";;")
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


if __name__ == '__main__':
    cli()
