import datetime
import os
import platform
import shlex

from rest.api.definitions import test_info_init
from rest.utils.cmd_utils import CmdUtils
from rest.utils.io_utils import IOUtils


class TestRunner:

    def __init__(self):
        self.command_dict = test_info_init
        self.__cmd_utils = CmdUtils()
        self.__io_utils = IOUtils()

    def run_commands(self, json_file, test_id, commands):
        start_time = datetime.datetime.now()
        commands = list(map(lambda item: item.strip(), commands))

        self.command_dict['id'] = str(test_id)
        self.command_dict['pid'] = os.getpid()
        input_data_dict = dict.fromkeys(commands, {"status": "scheduled", "details": {}})
        self.command_dict["started"] = True
        self.command_dict["commands"] = input_data_dict
        self.command_dict["startedat"] = str(datetime.datetime.now())

        self.__run_commands(commands, json_file=json_file)

        self.command_dict['finished'] = True
        self.command_dict['started'] = False
        end_time = datetime.datetime.now()
        self.command_dict['finishedat'] = str(end_time)
        self.command_dict['duration'] = (end_time - start_time).total_seconds()
        self.__io_utils.write_to_file_dict(json_file, self.command_dict)

        return self.command_dict

    def __run_commands(self, commands, json_file):
        details = {}
        status_finished = "finished"
        status_in_progress = "in progress"
        for command in commands:
            start = datetime.datetime.now()
            self.command_dict['commands'][command] = {"status": "scheduled", "details": {}}
            self.command_dict['commands'][command]['status'] = status_in_progress
            self.command_dict['commands'][command]['startedat'] = str(start)
            self.__io_utils.write_to_file_dict(json_file, self.command_dict)
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
            self.command_dict['commands'][command]['duration'] = (end - start).total_seconds()
            self.command_dict['commands'][command]['details'] = details[command]
            self.__io_utils.write_to_file_dict(json_file, self.command_dict)
