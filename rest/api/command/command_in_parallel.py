import datetime
import platform
from multiprocessing import Process, Manager

from rest.api.definitions import command_detached_init
from rest.utils.cmd_utils import CmdUtils
from rest.utils.io_utils import IOUtils


class CommandInParallel:
    """
    This class does not implement (and it does not make sense) executing commands in the same shell
    Every command is in different shell
    """

    def __init__(self):
        self.command_dict = command_detached_init
        self.__cmd_utils = CmdUtils()
        self.__io_utils = IOUtils()

    def run_command(self, manager_dict, dictionary, command):
        status_finished = "finished"
        status_in_progress = "in progress"
        dictionary['commands'][command] = {}
        dictionary['commands'][command]['status'] = status_in_progress
        start = datetime.datetime.now()
        dictionary['commands'][command]['startedat'] = str(start)

        if platform.system() == "Windows":
            details = self.__cmd_utils.run_cmd_shell_true(command)
        else:
            details = self.__cmd_utils.run_cmd_shell_true([command])

        dictionary['commands'][command]['status'] = status_finished
        end = datetime.datetime.now()
        dictionary['commands'][command]['finishedat'] = str(end)
        dictionary['commands'][command]['duration'] = (end - start).total_seconds()
        dictionary['commands'][command]['details'] = details

        manager_dict[command] = {}
        manager_dict[command] = dictionary['commands'][command]
        manager_dict['last'] = dictionary['commands'][command]
        manager_dict['last'] = manager_dict.pop('last')

    def run_commands(self, commands):
        with Manager() as manager:
            try:
                manager_dict = manager.dict()
                start_time = datetime.datetime.now()

                processes = [Process(target=self.run_command, args=(manager_dict, self.command_dict, command,)) for
                             command in commands]

                # start processes
                for p in processes:
                    p.start()

                # join them after they started
                for p in processes:
                    p.join()

                self.command_dict['commands'] = dict(manager_dict)

                self.command_dict['finished'] = "true"
                self.command_dict['started'] = "false"
                end_time = datetime.datetime.now()
                self.command_dict['finishedat'] = str(end_time)
                self.command_dict['duration'] = (end_time - start_time).total_seconds()

            except Exception as e:
                raise e

        return self.command_dict
