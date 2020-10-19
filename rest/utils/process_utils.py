import os
import signal

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
    def find_procs_by_name(name):
        """ Return a list of processes matching 'name' """
        ls = []
        for p in psutil.process_iter(["name", "exe", "cmdline"]):
            if name == p.info['name'] or \
                    p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                    p.info['cmdline'] and p.info['cmdline'][0] == name:
                ls.append(p)
        return ls

    def kill_proc_tree(self, sig=signal.SIGTERM, include_parent=False, timeout=5):

        """Kill a process tree (including grandchildren) with signal
        "sig" and return a (gone, still_alive) tuple.
        "on_terminate", if specified, is a callback function which is
        called as soon as a child terminates.
        """

        parent = psutil.Process(os.getpid())
        children = parent.children(recursive=True)
        if include_parent:
            children.append(parent)
        for p in children:
            p.send_signal(sig)
        gone, alive = psutil.wait_procs(children, timeout=timeout, callback=self.on_terminate)

        return (gone, alive)
