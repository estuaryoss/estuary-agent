from rest.api.logginghelpers.message_dumper import MessageDumper
from rest.utils.fluentd_utils import FluentdUtils


class ProcessUtils:
    def __init__(self, logger):
        self.logger = logger
        self.fluentd_utils = FluentdUtils(logger)
        self.message_dumper = MessageDumper()

    def on_terminate(self, proc):
        self.fluentd_utils.emit(tag="api", msg=self.message_dumper.dump_message(
            {"proc": str(proc), "returncode": proc.returncode}))
