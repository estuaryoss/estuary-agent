import datetime
import os
import platform
import shlex

from rest.api.definitions import test_info_init
from rest.utils.cmd_utils import CmdUtils


class TestRunnerInMemory:

    def __init__(self):
        self.command_dict = test_info_init
        self.__cmd_utils = CmdUtils()

    def run_commands(self, commands):
        start_total = datetime.datetime.now()
        commands = list(map(lambda item: item.strip(), commands))

        self.command_dict['pid'] = os.getpid()
        input_data_dict = dict.fromkeys(commands, {"status": "scheduled", "details": {}})
        self.command_dict["started"] = "true"
        self.command_dict["commands"] = input_data_dict
        self.command_dict["startedat"] = str(datetime.datetime.now())

        self.__run_commands(commands)

        self.command_dict['finished'] = "true"
        self.command_dict['started'] = "false"
        end_total = datetime.datetime.now()
        self.command_dict['finishedat'] = str(end_total)
        self.command_dict['duration'] = round((end_total - start_total).total_seconds())

        return self.command_dict

    def __run_commands(self,commands):
        details = {}
        status_finished = "finished"
        status_in_progress = "in progress"

        for command in commands:
            start = datetime.datetime.now()
            self.command_dict['commands'][command] = {"status": "scheduled", "details": {}}
            self.command_dict['commands'][command]['status'] = status_in_progress
            self.command_dict['commands'][command]['startedat'] = str(start)
            try:
                if platform.system() == "Windows":
                    details[command] = self.__cmd_utils.run_cmd_shell_true(shlex.split(command))
                else:
                    details[command] = self.__cmd_utils.run_cmd_shell_true([command])
            except Exception as e:
                details[command] = "Exception({0})".format(e.__str__())
            self.command_dict['commands'][command]['status'] = status_finished
            end = datetime.datetime.now()
            self.command_dict['commands'][command]['finishedat'] = str(end)
            self.command_dict['commands'][command]['duration'] = round((end - start).total_seconds())
            self.command_dict['commands'][command]['details'] = details[command]