import datetime
import json
import os
import platform
import shlex
from multiprocessing import Process, Manager

from rest.utils.cmd_utils import CmdUtils
from rest.utils.io_utils import IOUtils


class TestRunnerParallel:

    def __init__(self):
        self.__cmd_utils = CmdUtils()
        self.__io_utils = IOUtils()

    def run_command(self, manager_dict, dictionary, command):
        print("Input json is: " + json.dumps(dictionary) + "\n")
        status_finished = "finished"
        status_in_progress = "in progress"
        dictionary['commands'][command.strip()]['status'] = status_in_progress
        start = datetime.datetime.now()
        dictionary['commands'][command.strip()]['startedat'] = str(start)
        if platform.system() == "Windows":
            details = self.__cmd_utils.run_cmd_shell_true(shlex.split(command.strip()))
        else:
            details = self.__cmd_utils.run_cmd_shell_true([command.strip()])
        dictionary['commands'][command.strip()]['status'] = status_finished
        end = datetime.datetime.now()
        dictionary['commands'][command.strip()]['finishedat'] = str(end)
        dictionary['commands'][command.strip()]['duration'] = round((end - start).total_seconds())
        dictionary['commands'][command.strip()]['details'] = details

        manager_dict[command.strip()] = {}
        manager_dict[command.strip()] = dictionary['commands'][command.strip()]

    def run_commands(self, json_file, commands):
        with Manager() as manager:
            try:
                manager_dict = manager.dict()
                command_dict = self.__io_utils.read_dict_from_file(json_file)
                command_dict['start_pid'] = os.getpid()
                start_total = datetime.datetime.now()

                procs = [Process(target=self.run_command, args=(manager_dict, command_dict, command.strip(),)) for
                         command in commands]

                # start processes
                for p in procs:
                    p.start()
                    p.join()

                command_dict['commands'] = dict(manager_dict)

                self.__io_utils.write_to_file_dict(json_file, command_dict)
                command_dict['finished'] = "true"
                command_dict['started'] = "false"
                end_total = datetime.datetime.now()
                command_dict['finishedat'] = str(end_total)
                command_dict['duration'] = round((end_total - start_total).total_seconds())
                self.__io_utils.write_to_file_dict(json_file, command_dict)

            except Exception as e:
                raise e
