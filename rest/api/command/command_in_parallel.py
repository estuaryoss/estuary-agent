import asyncio
import datetime
import platform

from rest.api.definitions import command_detached_init
from rest.utils.cmd_utils_async import CmdUtilsAsync
from rest.utils.io_utils import IOUtils


class CommandInParallel:

    def __init__(self):
        self.command_dict = command_detached_init
        self.__cmd_utils = CmdUtilsAsync()
        self.__io_utils = IOUtils()

    async def run_command(self, command):
        status_finished = "finished"
        status_in_progress = "in progress"
        self.command_dict['commands'][command] = {}
        self.command_dict['commands'][command]['status'] = status_in_progress
        start_time = datetime.datetime.now()
        self.command_dict['commands'][command]['startedat'] = str(start_time)

        self.command_dict['commands'][command]['details'] = await self.__cmd_utils.run_cmd_async(command)

        end_time = datetime.datetime.now()
        self.command_dict['commands'][command]['status'] = status_finished
        self.command_dict['commands'][command]['finishedat'] = str(end_time)
        self.command_dict['commands'][command]['duration'] = (end_time - start_time).total_seconds()

        return command

    def run_commands(self, commands):
        commands = [item.strip() for item in commands]
        self.command_dict['commands'] = dict.fromkeys(commands, {"status": "scheduled", "details": {}})

        start_time = datetime.datetime.now()

        if platform.system() == "Windows":
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        else:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(self.main_asyncio(commands))
        loop.close()

        end_time = datetime.datetime.now()

        self.command_dict['finished'] = "true"
        self.command_dict['started'] = "false"
        self.command_dict['finishedat'] = str(end_time)
        self.command_dict['duration'] = (end_time - start_time).total_seconds()

        return self.command_dict

    async def main_asyncio(self, commands):
        future_commands = [self.run_command(command) for command in commands]
        for finished_command in asyncio.as_completed(future_commands):
            print(await finished_command)
