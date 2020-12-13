import datetime
import os
import platform

from rest.api.constants.env_constants import EnvConstants
from rest.api.definitions import command_detached_init
from rest.utils.cmd_utils import CmdUtils
from rest.utils.env_startup import EnvStartupSingleton


class CommandInMemory:
    """
    This class executes commands, stores & gets the details from the memory
    It uses a dict as data describing the command details
    """

    def __init__(self):
        self.command_dict = command_detached_init
        self.__cmd_utils = CmdUtils()

    def run_commands(self, commands):
        start_time = datetime.datetime.now()
        commands = [item.strip() for item in commands]

        self.command_dict['pid'] = os.getpid()
        self.command_dict["started"] = True
        self.command_dict["startedat"] = str(datetime.datetime.now())

        self.__run_commands(commands)

        self.command_dict['finished'] = True
        self.command_dict['started'] = False
        end_time = datetime.datetime.now()
        self.command_dict['finishedat'] = str(end_time)
        self.command_dict['duration'] = (end_time - start_time).total_seconds()

        return self.command_dict

    def __run_commands(self, commands):
        if EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PRESERVE_SHELL):
            self.__run_cmds_each_in_same_shell(commands)
        else:
            self.__run_cmds_each_in_different_shell(commands)

    def __run_cmds_each_in_different_shell(self, commands):
        input_data_dict = dict.fromkeys(commands, {"status": "scheduled", "details": {}})
        self.command_dict["commands"] = input_data_dict

        details = {}
        status_finished = "finished"
        status_in_progress = "in progress"

        for command in commands:
            start_time = datetime.datetime.now()
            self.command_dict['commands'][command] = {"status": "scheduled", "details": {}}
            self.command_dict['commands']['last'] = {"status": "scheduled", "details": {}}
            self.command_dict['commands'][command]['status'] = status_in_progress
            self.command_dict['commands'][command]['startedat'] = str(start_time)

            if platform.system() == "Windows":
                details[command] = self.__cmd_utils.run_cmd_shell_true(command)
            else:
                details[command] = self.__cmd_utils.run_cmd_shell_true([command])

            self.command_dict['commands'][command]['status'] = status_finished
            end_time = datetime.datetime.now()
            self.command_dict['commands'][command]['finishedat'] = str(end_time)
            self.command_dict['commands'][command]['duration'] = (end_time - start_time).total_seconds()
            self.command_dict['commands'][command]['details'] = details[command]
            self.command_dict['commands']['last'] = self.command_dict['commands'][command]

    def __run_cmds_each_in_same_shell(self, commands):
        details = {}
        status_finished = "finished"
        status_in_progress = "in progress"
        start_time = datetime.datetime.now()
        self.command_dict['commands']['last'] = {"status": "scheduled", "details": {}}
        self.command_dict['commands']['last'] = {"status": "scheduled", "details": {}}
        self.command_dict['commands']['last']['status'] = status_in_progress
        self.command_dict['commands']['last']['startedat'] = str(start_time)

        if platform.system() == "Windows":
            details['last'] = self.__cmd_utils.run_cmd_shell_true("&".join(commands))
        else:
            details['last'] = self.__cmd_utils.run_cmd_shell_true(";".join(commands))

        self.command_dict['commands']['last']['status'] = status_finished
        end_time = datetime.datetime.now()
        self.command_dict['commands']['last']['finishedat'] = str(end_time)
        self.command_dict['commands']['last']['duration'] = (end_time - start_time).total_seconds()
        self.command_dict['commands']['last']['details'] = details['last']
        self.command_dict['commands']['last'] = self.command_dict['commands']['last']
