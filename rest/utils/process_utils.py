import os

import psutil

from rest.api.loghelpers.message_dumper import MessageDumper
from rest.service.fluentd import Fluentd


class ProcessUtils:
    def __init__(self, logger):
        self.logger = logger
        self.fluentd_utils = Fluentd(logger)
        self.message_dumper = MessageDumper()

    def on_terminate(self, proc):
        self.fluentd_utils.emit(tag="api", msg=self.message_dumper.dump_message(
            {"proc": str(proc), "returncode": proc.returncode}))

    @staticmethod
    def get_procs_by_name(name):
        """ Return a list of processes matching 'name' """
        process_list = []
        for p in psutil.process_iter():
            name_, pid_ = "", 0
            try:
                name_ = p.name()
                pid_ = p.pid
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except psutil.NoSuchProcess:
                continue
            if name == name_:
                process_list.append(pid_)
        return process_list
