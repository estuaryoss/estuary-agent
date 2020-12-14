import datetime
import os
import platform

from rest.api.definitions import command_detached_init
from rest.utils.cmd_utils import CmdUtils
from rest.utils.io_utils import IOUtils


class Command:

    def __init__(self):
        self.command_dict = command_detached_init
        self.__cmd_utils = CmdUtils()
        self.__io_utils = IOUtils()

    def run_commands(self, json_file, cmd_id, commands):
        start_time = datetime.datetime.now()

        self.command_dict['id'] = str(cmd_id)
        self.command_dict['pid'] = os.getpid()
        commands = [item.strip() for item in commands]
        input_data_dict = dict.fromkeys(commands, {"status": "scheduled", "details": {}})
        self.command_dict["commands"] = input_data_dict
        self.command_dict["started"] = True
        self.command_dict["startedat"] = str(datetime.datetime.now())
        self.__io_utils.write_to_file_dict(json_file, self.command_dict)

        self.__run_commands(json_file=json_file, cmd_id=cmd_id, commands=commands)

        self.command_dict['started'] = False
        self.command_dict['finished'] = True
        end_time = datetime.datetime.now()
        self.command_dict['finishedat'] = str(end_time)
        self.command_dict['duration'] = (end_time - start_time).total_seconds()
        self.__io_utils.write_to_file_dict(json_file, self.command_dict)

        return self.command_dict

    def __run_commands(self, json_file, cmd_id, commands):
        for command in commands:
            self.__run_command(json_file, cmd_id, command)

    def __run_command(self, json_file, cmd_id, command):
        details = {}
        status_finished = "finished"
        status_in_progress = "in progress"
        start_time = datetime.datetime.now()
        self.command_dict['commands'][command] = {"status": "scheduled", "details": {}}
        self.command_dict['commands'][command]['status'] = status_in_progress
        self.command_dict['commands'][command]['startedat'] = str(start_time)
        self.__io_utils.write_to_file_dict(json_file, self.command_dict)

        if platform.system() == "Windows":
            details[command] = self.__cmd_utils.run_cmd_shell_true_to_file_str(str_cmd=command, cmd_id=cmd_id)
        else:
            details[command] = self.__cmd_utils.run_cmd_shell_true_to_file_list(list_cmd=[command], cmd_id=cmd_id)

        self.command_dict['commands'][command]['status'] = status_finished
        end_time = datetime.datetime.now()
        self.command_dict['commands'][command]['finishedat'] = str(end_time)
        self.command_dict['commands'][command]['duration'] = (end_time - start_time).total_seconds()
        self.command_dict['commands'][command]['details'] = details[command]
        self.__io_utils.write_to_file_dict(json_file, self.command_dict)

    def get_command_dict(self):
        return self.command_dict
