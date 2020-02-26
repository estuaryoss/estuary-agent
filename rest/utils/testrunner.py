import datetime
import os
import platform
import shlex

from rest.api.definitions import test_info_init
from rest.utils.cmd_utils import CmdUtils
from rest.utils.io_utils import IOUtils


class TestRunner:

    def __init__(self):
        self.__cmd_utils = CmdUtils()
        self.__io_utils = IOUtils()

    def run_commands(self, json_file, test_id, commands):
        start_total = datetime.datetime.now()

        status_finished = "finished"
        status_in_progress = "in progress"
        command_dict = test_info_init

        command_dict['id'] = test_id
        command_dict['pid'] = os.getpid()
        input_data_dict = dict.fromkeys(commands, {"status": "scheduled", "details": {}})
        command_dict["started"] = "true"
        command_dict["commands"] = input_data_dict
        command_dict["startedat"] = str(datetime.datetime.now())

        details = {}
        for command in commands:
            start = datetime.datetime.now()
            command_dict['commands'][command.strip()] = {"status": "scheduled", "details": {}}
            command_dict['commands'][command.strip()]['status'] = status_in_progress
            command_dict['commands'][command.strip()]['startedat'] = str(start)
            self.__io_utils.write_to_file_dict(json_file, command_dict)
            try:
                if platform.system() == "Windows":
                    details[command.strip()] = self.__cmd_utils.run_cmd_shell_true(shlex.split(command.strip()))
                else:
                    details[command.strip()] = self.__cmd_utils.run_cmd_shell_true([command.strip()])
            except Exception as e:
                details[command.strip()] = "Exception({0})".format(e.__str__())
            command_dict['commands'][command.strip()]['status'] = status_finished
            end = datetime.datetime.now()
            command_dict['commands'][command.strip()]['finishedat'] = str(end)
            command_dict['commands'][command.strip()]['duration'] = round((end - start).total_seconds())
            command_dict['commands'][command.strip()]['details'] = details[command.strip()]
            self.__io_utils.write_to_file_dict(json_file, command_dict)

        command_dict['finished'] = "true"
        command_dict['started'] = "false"
        end_total = datetime.datetime.now()
        command_dict['finishedat'] = str(end_total)
        command_dict['duration'] = round((end_total - start_total).total_seconds())
        self.__io_utils.write_to_file_dict(json_file, command_dict)

        return command_dict
