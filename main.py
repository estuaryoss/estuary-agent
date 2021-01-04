#!/usr/bin/env python3
import multiprocessing
import sys
from pathlib import Path

from rest.api.constants.env_constants import EnvConstants
from rest.api.constants.env_init import EnvInit
from rest.api.loghelpers.message_dumper import MessageDumper
from rest.api.routes import fluentd_utils, app
from rest.environment.environment import EnvironmentSingleton
from rest.service.eureka import Eureka
from rest.utils.env_startup import EnvStartupSingleton
from rest.utils.io_utils import IOUtils

if __name__ == "__main__":
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None

    message_dumper = MessageDumper()
    io_utils = IOUtils()
    host = '0.0.0.0'
    port = EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PORT)
    fluentd_tag = "startup"

    if EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.EUREKA_SERVER):
        Eureka(EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.EUREKA_SERVER)).register_app(
            EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.APP_IP_PORT))

    io_utils.create_dir(Path(EnvInit.TEMPLATES_DIR))
    io_utils.create_dir(Path(EnvInit.VARS_DIR))
    io_utils.create_dir(Path(EnvInit.CMD_DETACHED_DIR))
    io_utils.create_dir(Path(EnvInit.CMD_DETACHED_STREAMS))

    environ_dump = message_dumper.dump_message(EnvironmentSingleton.get_instance().get_env_and_virtual_env())
    ip_port_dump = message_dumper.dump_message({"host": host, "port": port})

    app.logger.debug({"msg": environ_dump})
    app.logger.debug({"msg": ip_port_dump})
    app.logger.debug({"msg": EnvStartupSingleton.get_instance().get_config_env_vars()})

    fluentd_utils.emit(tag=fluentd_tag, msg=environ_dump)
    is_https = EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_ENABLE)
    https_cert_path = EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_CERT)
    https_prv_key_path = EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_KEY)
    ssl_context = (https_cert_path, https_prv_key_path) if is_https else None
    app.run(host=host, port=port, ssl_context=ssl_context)
