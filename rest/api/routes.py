import json
import os
import stat
from pathlib import Path
from secrets import token_hex

import flask
import psutil
from flask import Response
from flask import request
from fluent import sender

from about import properties
from rest.api import AppCreatorSingleton
from rest.api.command.command_in_memory import CommandInMemory
from rest.api.command.command_in_parallel import CommandInParallel
from rest.api.command.command_streamer import CommandStreamer
from rest.api.constants.api_code_constants import ApiCodeConstants
from rest.api.constants.env_constants import EnvConstants
from rest.api.constants.env_init import EnvInit
from rest.api.constants.header_constants import HeaderConstants
from rest.api.definitions import command_detached_init
from rest.api.jinja2.render import Render
from rest.api.loghelpers.message_dumper import MessageDumper
from rest.api.responsehelpers.error_codes import ErrorCodes
from rest.api.responsehelpers.http_response import HttpResponse
from rest.api.swagger import swagger_file_content
from rest.environment.env_vars_setter import EnvVarsSetter
from rest.environment.environment import EnvironmentSingleton
from rest.model.config_descriptor import ConfigDescriptor
from rest.model.config_loader import ConfigLoader
from rest.service.fluentd import Fluentd
from rest.service.restapi import RestApi
from rest.state.state_holder import StateHolder
from rest.utils.cmd_utils import CmdUtils
from rest.utils.env_startup import EnvStartupSingleton
from rest.utils.io_utils import IOUtils
from rest.utils.process_utils import ProcessUtils
from rest.utils.yaml_cmds_splitter import YamlCommandsSplitter

app = AppCreatorSingleton.get_instance().get_app()
logger = \
    sender.FluentSender(tag=properties.get('name'),
                        host=EnvStartupSingleton.get_instance().get_config_env_vars().get(
                            EnvConstants.FLUENTD_IP_PORT).split(":")[0],
                        port=int(EnvStartupSingleton.get_instance().get_config_env_vars().get(
                            EnvConstants.FLUENTD_IP_PORT).split(":")[1])) \
        if EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.FLUENTD_IP_PORT) else None
fluentd_utils = Fluentd(logger)
message_dumper = MessageDumper()
env = EnvironmentSingleton.get_instance()


@app.before_request
def before_request():
    ctx = app.app_context()
    http = HttpResponse()
    ctx.g.xid = token_hex(8)
    request_uri = request.full_path

    # add here your custom header to be logged with fluentd
    message_dumper.set_header(HeaderConstants.X_REQUEST_ID,
                              request.headers.get(HeaderConstants.X_REQUEST_ID) if request.headers.get(
                                  HeaderConstants.X_REQUEST_ID) else ctx.g.xid)
    message_dumper.set_header(HeaderConstants.REQUEST_URI, request_uri)

    response = fluentd_utils.emit(tag="api", msg=message_dumper.dump(request=request))
    app.logger.debug(response)
    if not str(request.headers.get(HeaderConstants.TOKEN)) == str(
            EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTP_AUTH_TOKEN)):
        if not ("/api/docs" in request_uri or "/swagger/swagger.yml" in request_uri):  # exclude swagger
            headers = {
                HeaderConstants.X_REQUEST_ID: message_dumper.get_header(HeaderConstants.X_REQUEST_ID)
            }
            return Response(json.dumps(http.response(code=ApiCodeConstants.UNAUTHORIZED,
                                                     message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.UNAUTHORIZED),
                                                     description="Invalid Token")), 401,
                            mimetype="application/json",
                            headers=headers)


@app.after_request
def after_request(http_response):
    # if not json, do not alter
    try:
        headers = dict(http_response.headers)
        headers[HeaderConstants.X_REQUEST_ID] = message_dumper.get_header(HeaderConstants.X_REQUEST_ID)
        http_response.headers = headers
    except:
        app.logger.debug("Message was not altered: " + message_dumper.dump(http_response))

    http_response.direct_passthrough = False
    response = fluentd_utils.emit(tag="api", msg=message_dumper.dump(http_response))
    app.logger.debug(response)

    return http_response


@app.route('/swagger/swagger.yml/')
def get_swagger():
    return Response(swagger_file_content, 200, mimetype="application/json")


@app.route('/env')
def get_vars():
    http = HttpResponse()

    return Response(json.dumps(
        http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                      description=env.get_env_and_virtual_env())),
        200, mimetype="application/json")


@app.route('/ping')
def ping():
    http = HttpResponse()

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description="pong")),
        200, mimetype="application/json")


@app.route('/about')
def about():
    http = HttpResponse()

    return Response(json.dumps(
        http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                      description=properties["name"])),
        200,
        mimetype="application/json")


@app.route('/render/<template>/<variables>', methods=['GET', 'POST'])
def get_content_with_env(template, variables):
    http = HttpResponse()
    env.set_env_var(EnvConstants.TEMPLATE, template.strip())
    env.set_env_var(EnvConstants.VARIABLES, variables.strip())

    try:
        env_vars_attempted = request.get_json(force=True)
        for key, value in env_vars_attempted.items():
            env.set_env_var(key, value)
    except:
        pass

    try:
        r = Render(env.get_env_and_virtual_env().get(EnvConstants.TEMPLATE),
                   env.get_env_and_virtual_env().get(EnvConstants.VARIABLES))
        response = Response(r.rend_template(), 200, mimetype="text/plain")
    except Exception as e:
        response = Response(json.dumps(http.response(code=ApiCodeConstants.JINJA2_RENDER_FAILURE,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.JINJA2_RENDER_FAILURE),
                                                     description="Exception({})".format(e.__str__()))), 500,
                            mimetype="application/json")

    return response


@app.route('/env', methods=['POST'])
def set_env():
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    try:
        env_vars_attempted = json.loads(input_data)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.INVALID_JSON_PAYLOAD,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.INVALID_JSON_PAYLOAD) % str(
                                                     input_data),
                                                 description="Exception({0})".format(e.__str__()))), 500,
                        mimetype="application/json")

    try:
        for key, value in env_vars_attempted.items():
            env.set_env_var(key, value)

        env_vars_added = {key: value for key, value in env_vars_attempted.items() if key in env.get_virtual_env()}
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.SET_ENV_VAR_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.SET_ENV_VAR_FAILURE) % str(
                                                     input_data),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          env_vars_added)),
        200,
        mimetype="application/json")


@app.route('/env/<name>', methods=['GET'])
def get_env(name):
    http = HttpResponse()

    return Response(json.dumps(
        http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                      env.get_env_and_virtual_env().get(name))), 200, mimetype="application/json")


@app.route('/commanddetached', methods=['GET'])
def get_cmd_detached_info():
    http = HttpResponse()
    io_utils = IOUtils()

    try:
        file = StateHolder.get_last_command()
        if not Path(file).is_file():
            io_utils.write_to_file_dict(file, command_detached_init)
        cmd_detached_response = json.loads(io_utils.read_file(file))
        cmd_detached_response["processes"] = [p.info for p in
                                              psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.GET_COMMAND_DETACHED_INFO_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.GET_COMMAND_DETACHED_INFO_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=cmd_detached_response)),
        200,
        mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['GET'])
def get_cmd_detached_info_id(command_id):
    command_id = command_id.strip()
    http = HttpResponse()
    io_utils = IOUtils()
    file = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)

    try:
        cmd_detached_response = json.loads(io_utils.read_file(file))
        cmd_detached_response["processes"] = [p.info for p in
                                              psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.GET_COMMAND_DETACHED_INFO_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.GET_COMMAND_DETACHED_INFO_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=cmd_detached_response)),
        200,
        mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['POST', 'PUT'])
def cmd_detached_start(command_id):
    command_id = command_id.strip()
    start_py_path = str(Path(".").absolute()) + "/start.py"
    command = []
    io_utils = IOUtils()
    cmd_utils = CmdUtils()
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 )), 500, mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        command_detached_init["id"] = command_id
        file_path = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)
        StateHolder.set_last_command(file_path)
        io_utils.write_to_file_dict(file_path, command_detached_init)
        os.chmod(start_py_path, stat.S_IRWXU)
        command.insert(0, ";".join(input_data_list))  # second arg is cmd list separated by ;
        command.insert(0, command_id)  # first arg is test id
        command.insert(0, start_py_path)
        # final_command.insert(0, "python")
        cmd_utils.run_cmd_detached(command)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_DETACHED_START_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_DETACHED_START_FAILURE) % command_id,
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), command_id)),
        200,
        mimetype="application/json")


@app.route('/commanddetached', methods=['DELETE'])
def command_detached_stop():
    process_utils = ProcessUtils(logger)
    http = HttpResponse()

    try:
        process_utils.kill_proc_tree()
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_DETACHED_STOP_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_DETACHED_STOP_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))),
        200,
        mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['DELETE'])
def command_detached_stop_by_id(command_id):
    command_id = command_id.strip()
    process_utils = ProcessUtils(logger)
    http = HttpResponse()
    io_utils = IOUtils()
    file = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)

    try:
        cmd_detached_response = json.loads(io_utils.read_file(file))
        process_utils.kill_proc_tree(pid=cmd_detached_response.get('pid'), include_parent=True)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_DETACHED_STOP_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_DETACHED_STOP_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))),
        200,
        mimetype="application/json")


@app.route('/commanddetachedyaml/<command_id>', methods=['POST', 'PUT'])
def command_detached_start_yaml(command_id):
    command_id = command_id.strip()
    http = HttpResponse()
    self_ip = "127.0.0.1"
    protocol = "https" if EnvStartupSingleton.get_instance().get_config_env_vars().get(
        EnvConstants.HTTPS_ENABLE) else "http"
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 )), 500, mimetype="application/json")

    try:
        config_loader = ConfigLoader.load(input_data)
        yaml_cmds_splitter = YamlCommandsSplitter(config_loader.get_config())
        cmds_list_as_string = "\n".join(yaml_cmds_splitter.get_cmds_in_order())
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.INVALID_YAML_CONFIG,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.INVALID_YAML_CONFIG),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    try:
        conn = {
            "protocol": protocol,
            "cert": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_CERT),
            "ip": self_ip,
            "port": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PORT),
            "endpoint": f"/env"
        }
        evs = EnvVarsSetter(conn=conn, config=config_loader.get_config())
        response = evs.set_env_vars(headers=request.headers)
        env_vars_set = response.json().get("description")
        if response.status_code != 200:
            raise Exception(response.json().get("description"))
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.SET_ENV_VAR_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.SET_ENV_VAR_FAILURE) % evs.get_env_vars(),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    try:
        conn = {
            "protocol": protocol,
            "cert": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_CERT),
            "ip": self_ip,
            "port": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PORT),
            "endpoint": f"/commanddetached/{command_id}"
        }
        rest_service = RestApi(conn)
        response = rest_service.post(data=cmds_list_as_string, headers=request.headers)
        if response.status_code != 200:
            raise Exception(response.json().get("description"))
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_DETACHED_START_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_DETACHED_START_FAILURE) % command_id,
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    # only env vars that were set
    config_loader.get_config()[evs.get_env_key()] = env_vars_set
    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          ConfigDescriptor.description(command_id, config_loader.get_config()))), 200,
        mimetype="application/json")


@app.route('/file', methods=['POST', 'PUT'])
def upload_file():
    io_utils = IOUtils()
    http = HttpResponse()
    header_key = 'File-Path'
    try:
        file_content = request.get_data()
        file_path = request.headers.get(f"{header_key}")
        if not file_path:
            return Response(json.dumps(http.response(code=ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                     description=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 500,
                            mimetype="application/json")
        if not file_content:
            return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                     description=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 500,
                            mimetype="application/json")
        io_utils.write_to_file_binary(file_path, file_content)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.UPLOAD_FILE_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.UPLOAD_FILE_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                                 ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))), 200,
        mimetype="application/json")


@app.route('/file', methods=['GET'])
def get_file():
    io_utils = IOUtils()
    http = HttpResponse()
    header_key = 'File-Path'

    file_path = request.headers.get(f"{header_key}")
    if not file_path:
        return Response(json.dumps(http.response(code=ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 500,
                        mimetype="application/json")

    try:
        response = io_utils.read_file_byte_array(file_path), 200
    except Exception as e:
        response = Response(json.dumps(http.response(code=ApiCodeConstants.GET_FILE_FAILURE,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.GET_FILE_FAILURE),
                                                     description="Exception({})".format(e.__str__()))), 500,
                            mimetype="application/json")
    return response


@app.route('/folder', methods=['GET'])
def get_results_folder():
    io_utils = IOUtils()
    http = HttpResponse()
    archive_name = "results"
    header_key = 'Folder-Path'

    folder_path = request.headers.get(f"{header_key}")
    if not folder_path:
        return Response(json.dumps(http.response(code=ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 500,
                        mimetype="application/json")

    try:
        io_utils.zip_file(archive_name, folder_path)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.FOLDER_ZIP_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.FOLDER_ZIP_FAILURE) % folder_path,
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    return flask.send_file(
        f"/tmp/{archive_name}.zip",
        mimetype='application/zip',
        as_attachment=True), 200


@app.route('/command', methods=['POST', 'PUT'])
def execute_command():
    env.set_env_var(EnvConstants.TEMPLATE, "start.py")
    env.set_env_var(EnvConstants.VARIABLES, "commandinfo.json")
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 500,
                        mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        command_in_memory = CommandInMemory()
        response = command_in_memory.run_commands(input_data_list)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=response)),
        200,
        mimetype="application/json")


@app.route('/commandyaml', methods=['POST', 'PUT'])
def execute_command_yaml():
    env.set_env_var(EnvConstants.TEMPLATE, "start.py")
    env.set_env_var(EnvConstants.VARIABLES, "commandinfo.json")
    http = HttpResponse()
    self_ip = "127.0.0.1"
    protocol = "https" if EnvStartupSingleton.get_instance().get_config_env_vars().get(
        EnvConstants.HTTPS_ENABLE) else "http"
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 500,
                        mimetype="application/json")

    try:
        config_loader = ConfigLoader.load(input_data)
        yaml_cmds_splitter = YamlCommandsSplitter(config_loader.get_config())
        cmds_list_as_string = "\n".join(yaml_cmds_splitter.get_cmds_in_order())
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.INVALID_YAML_CONFIG,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.INVALID_YAML_CONFIG),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")
    try:
        conn = {
            "protocol": protocol,
            "cert": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_CERT),
            "ip": self_ip,
            "port": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PORT),
            "endpoint": f"/env"
        }
        evs = EnvVarsSetter(conn=conn, config=config_loader.get_config())
        response = evs.set_env_vars(headers=request.headers)
        env_vars_set = response.json().get("description")
        if response.status_code != 200:
            raise Exception(response.json().get("description"))
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.SET_ENV_VAR_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.SET_ENV_VAR_FAILURE) % evs.get_env_vars(),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    try:
        conn = {
            "protocol": protocol,
            "cert": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.HTTPS_CERT),
            "ip": self_ip,
            "port": EnvStartupSingleton.get_instance().get_config_env_vars().get(EnvConstants.PORT),
            "endpoint": f"/command",
            "timeout": 3600
        }
        rest_service = RestApi(conn)
        response = rest_service.post(data=cmds_list_as_string, headers=request.headers)
        if response.status_code != 200:
            raise Exception(response.json().get("description"))
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    # only env vars that were set
    config_loader.get_config()[evs.get_env_key()] = env_vars_set
    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          ConfigDescriptor.description(response.json().get("description"),
                                                       config_loader.get_config()))), 200,
        mimetype="application/json")


@app.route('/commandparallel', methods=['POST', 'PUT'])
def execute_command_parallel():
    env.set_env_var(EnvConstants.TEMPLATE, "start.py")
    env.set_env_var(EnvConstants.VARIABLES, "commandinfo.json")
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 500,
                        mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        command_in_parallel = CommandInParallel()
        response = command_in_parallel.run_commands(input_data_list)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 500,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=response)),
        200,
        mimetype="application/json")
