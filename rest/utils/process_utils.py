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
