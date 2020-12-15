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

from about import properties, about_system
from rest.api import AppCreatorSingleton
from rest.api.command.command_hasher import CommandHasher
from rest.api.command.command_in_memory import CommandInMemory
from rest.api.command.command_in_parallel import CommandInParallel
from rest.api.constants.api_code_constants import ApiCode
from rest.api.constants.env_constants import EnvConstants
from rest.api.constants.env_init import EnvInit
from rest.api.constants.header_constants import HeaderConstants
from rest.api.definitions import command_detached_init
from rest.api.exception.api_exception import ApiException
from rest.api.jinja2.render import Render
from rest.api.loghelpers.message_dumper import MessageDumper
from rest.api.responsehelpers.error_codes import ErrorMessage
from rest.api.responsehelpers.http_response import HttpResponse
from rest.api.swagger import swagger_file_content
from rest.environment.environment import EnvironmentSingleton
from rest.model.config_descriptor import ConfigDescriptor
from rest.model.config_loader import ConfigLoader
from rest.service.fluentd import Fluentd
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


@app.errorhandler(ApiException)
def handle_api_error(e):
    return Response(json.dumps(HttpResponse().response(
        code=e.code, message=e.message, description="Exception({})".format(e.exception.__str__()))), 500,
        mimetype="application/json")


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
            return Response(json.dumps(http.response(code=ApiCode.UNAUTHORIZED.value,
                                                     message=ErrorMessage.HTTP_CODE.get(ApiCode.UNAUTHORIZED.value),
                                                     description="Invalid Token")), 401,
                            mimetype="application/json", headers=headers)


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
    return Response(
        json.dumps(HttpResponse().response(code=ApiCode.SUCCESS.value,
                                           message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                           description=env.get_env_and_virtual_env())), 200,
        mimetype="application/json")


@app.route('/ping')
def ping():
    return Response(
        json.dumps(HttpResponse().response(code=ApiCode.SUCCESS.value,
                                           message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                           description="pong")), 200, mimetype="application/json")


@app.route('/about')
def about():
    return Response(json.dumps(
        HttpResponse().response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                description=about_system)), 200, mimetype="application/json")


@app.route('/render/<template>/<variables>', methods=['GET', 'POST'])
def get_content_with_env(template, variables):
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
        raise ApiException(ApiCode.JINJA2_RENDER_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.JINJA2_RENDER_FAILURE.value), e)

    return response


@app.route('/env', methods=['POST'])
def set_env():
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    try:
        env_vars_attempted = json.loads(input_data)
    except Exception as e:
        raise ApiException(ApiCode.INVALID_JSON_PAYLOAD.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.INVALID_JSON_PAYLOAD.value) % str(input_data), e)
    try:
        for key, value in env_vars_attempted.items():
            env.set_env_var(key, value)

        env_vars_added = {key: value for key, value in env_vars_attempted.items() if key in env.get_virtual_env()}
    except Exception as e:
        raise ApiException(ApiCode.SET_ENV_VAR_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.SET_ENV_VAR_FAILURE.value) % str(input_data), e)
    return Response(
        json.dumps(
            http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value), env_vars_added)),
        200, mimetype="application/json")


@app.route('/env/<name>', methods=['GET'])
def get_env(name):
    http = HttpResponse()

    return Response(json.dumps(
        http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
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
        cmd_id = cmd_detached_response.get('id')
        command_keys = cmd_detached_response.get('commands').keys()
        for key in command_keys:
            try:  # because files might not be created yet
                cmd_detached_response["commands"][key]["details"]["out"] = \
                    IOUtils.read_file(CommandHasher.get_cmd_for_file_encode_str(key, cmd_id, ".out"))
                cmd_detached_response["commands"][key]["details"]["err"] = \
                    IOUtils.read_file(CommandHasher.get_cmd_for_file_encode_str(key, cmd_id, ".err"))
            except Exception as e:
                app.logger.debug("Exception({})".format(e.__str__()))
        cmd_detached_response["processes"] = \
            [p.info for p in psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        raise ApiException(ApiCode.GET_COMMAND_DETACHED_INFO_FAILURE,
                           ErrorMessage.HTTP_CODE.get(ApiCode.GET_COMMAND_DETACHED_INFO_FAILURE), e)
    return Response(
        json.dumps(
            http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                          description=cmd_detached_response)), 200, mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['GET'])
def get_cmd_detached_info_id(command_id):
    cmd_id = command_id.strip()
    http = HttpResponse()
    io_utils = IOUtils()
    file = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)

    try:
        cmd_detached_response = json.loads(io_utils.read_file(file))
        command_keys = cmd_detached_response.get('commands').keys()
        for key in command_keys:
            try:  # because files might not be created yet
                cmd_detached_response["commands"][key]["details"]["out"] = \
                    IOUtils.read_file(CommandHasher.get_cmd_for_file_encode_str(key, cmd_id, ".out"))
                cmd_detached_response["commands"][key]["details"]["err"] = \
                    IOUtils.read_file(CommandHasher.get_cmd_for_file_encode_str(key, cmd_id, ".err"))
            except Exception as e:
                app.logger.debug("Exception({})".format(e.__str__()))
        cmd_detached_response["processes"] = [p.info for p in
                                              psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        raise ApiException(ApiCode.GET_COMMAND_DETACHED_INFO_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.GET_COMMAND_DETACHED_INFO_FAILURE.value), e)

    return Response(
        json.dumps(http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                 description=cmd_detached_response)), 200, mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['POST'])
def cmd_detached_start(command_id, internal_data=None):
    command_id = command_id.strip()
    io_utils = IOUtils()
    cmd_utils = CmdUtils()
    http = HttpResponse()
    start_py_path = str(Path(".").absolute()) + os.path.sep + "start.py"
    input_data = internal_data if internal_data else request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))
    try:
        command_detached_stop_by_id(command_id=command_id)
    except Exception as e:
        app.logger.debug(f"Could not stop command id: {command_id}. Exception: {e.__str__()}")

    try:
        input_data_list = input_data.split("\n")
        command_detached_init["id"] = command_id
        io_utils.write_to_file_dict(StateHolder.get_last_command(), command_detached_init)
        os.chmod(start_py_path, stat.S_IRWXU)
        command = [start_py_path, f"--cid={command_id}", f"--args={';;'.join(input_data_list)}"]
        cmd_utils.run_cmd_detached(command)
        StateHolder.set_last_command(command_id)
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_DETACHED_START_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_DETACHED_START_FAILURE.value) % command_id, e)

    return Response(
        json.dumps(http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value), command_id)),
        202, mimetype="application/json")


@app.route('/commanddetached', methods=['DELETE'])
def command_detached_stop():
    process_utils = ProcessUtils(logger)
    http = HttpResponse()

    try:
        process_utils.kill_proc_tree()
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_DETACHED_STOP_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_DETACHED_STOP_FAILURE.value), e)

    return Response(json.dumps(
        http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                      description=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value))), 200, mimetype="application/json")


@app.route('/commanddetached/<command_id>', methods=['DELETE'])
def command_detached_stop_by_id(command_id):
    command_id = command_id.strip()
    process_utils = ProcessUtils(logger)
    http = HttpResponse()
    io_utils = IOUtils()
    file = EnvInit.COMMAND_DETACHED_FILENAME.format(command_id)

    try:
        cmd_detached_response = json.loads(io_utils.read_file(file))
        process_utils.kill_proc_tree(pid=cmd_detached_response.get('pid'))
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_DETACHED_STOP_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_DETACHED_STOP_FAILURE.value), e)

    return Response(
        json.dumps(
            http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                          description=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value))), 200,
        mimetype="application/json")


@app.route('/commanddetachedyaml/<command_id>', methods=['POST', 'PUT'])
def command_detached_start_yaml(command_id):
    command_id = command_id.strip()
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))

    try:
        config_loader = ConfigLoader.load(input_data)
        yaml_cmds_splitter = YamlCommandsSplitter(config_loader.get_config())
        cmds_list_as_string = "\n".join(yaml_cmds_splitter.get_cmds_in_order())
    except Exception as e:
        raise ApiException(ApiCode.INVALID_YAML_CONFIG.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.INVALID_YAML_CONFIG.value), e)
    try:
        env_vars_set = EnvironmentSingleton.get_instance().set_env_vars(config_loader.get_config().get('env'))
    except Exception as e:
        raise ApiException(ApiCode.SET_ENV_VAR_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.SET_ENV_VAR_FAILURE.value) %
                           json.dumps(config_loader.get_config().get('env')), e)

    try:
        cmd_detached_start(command_id, cmds_list_as_string)
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_DETACHED_START_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_DETACHED_START_FAILURE.value) % command_id, e)

    # only env vars that were set
    config_loader.get_config()['env'] = env_vars_set
    return Response(
        json.dumps(
            http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                          ConfigDescriptor.description(command_id, config_loader.get_config()))), 200,
        mimetype="application/json")


@app.route('/file', methods=['POST', 'PUT'])
def upload_file():
    io_utils = IOUtils()
    http = HttpResponse()
    header_key = 'File-Path'
    file_content = request.get_data()
    file_path = request.headers.get(f"{header_key}")
    if file_path is None:
        raise ApiException(ApiCode.HTTP_HEADER_NOT_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key)
    if not file_content:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))
    try:
        io_utils.write_to_file_binary(file_path, file_content)
    except Exception as e:
        raise ApiException(ApiCode.UPLOAD_FILE_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.UPLOAD_FILE_FAILURE.value), e)

    return Response(
        json.dumps(http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                 ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value))), 200, mimetype="application/json")


@app.route('/file', methods=['GET'])
def get_file():
    io_utils = IOUtils()
    header_key = 'File-Path'

    file_path = request.headers.get(f"{header_key}")
    if not file_path:
        raise ApiException(ApiCode.HTTP_HEADER_NOT_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key)

    try:
        response = io_utils.read_file_byte_array(file_path), 200
    except Exception as e:
        raise ApiException(ApiCode.GET_FILE_FAILURE.value, ErrorMessage.HTTP_CODE.get(ApiCode.GET_FILE_FAILURE.value),
                           e)

    return response


@app.route('/folder', methods=['GET'])
def get_results_folder():
    io_utils = IOUtils()
    http = HttpResponse()
    archive_name = "results"
    header_key = 'Folder-Path'

    folder_path = request.headers.get(f"{header_key}")
    if not folder_path:
        raise ApiException(ApiCode.HTTP_HEADER_NOT_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key,
                           ErrorMessage.HTTP_CODE.get(ApiCode.HTTP_HEADER_NOT_PROVIDED.value) % header_key)

    try:
        io_utils.zip_file(archive_name, folder_path)
    except Exception as e:
        raise ApiException(ApiCode.FOLDER_ZIP_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.FOLDER_ZIP_FAILURE.value) % folder_path, e)

    return flask.send_file(f"/tmp/{archive_name}.zip", mimetype='application/zip', as_attachment=True), 200


@app.route('/command', methods=['POST', 'PUT'])
def execute_command(internal_data=None):
    http = HttpResponse()
    input_data = internal_data if internal_data else request.get_data(as_text=True).strip()

    if not input_data:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))
    try:
        input_data_list = [x.strip() for x in input_data.split("\n")]
        command_in_memory = CommandInMemory()
        response = command_in_memory.run_commands(input_data_list)
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_EXEC_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_EXEC_FAILURE.value), e)

    return Response(
        json.dumps(
            http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                          description=response)), 200, mimetype="application/json")


@app.route('/commandyaml', methods=['POST', 'PUT'])
def execute_command_yaml():
    env.set_env_var(EnvConstants.TEMPLATE, "start.py")
    env.set_env_var(EnvConstants.VARIABLES, "commandinfo.json")
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))

    try:
        config_loader = ConfigLoader.load(input_data)
        yaml_cmds_splitter = YamlCommandsSplitter(config_loader.get_config())
        cmds_list_as_string = "\n".join(yaml_cmds_splitter.get_cmds_in_order())
    except Exception as e:
        raise ApiException(ApiCode.INVALID_YAML_CONFIG.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.INVALID_YAML_CONFIG.value), e)
    try:
        env_vars_set = EnvironmentSingleton.get_instance().set_env_vars(config_loader.get_config().get('env'))
    except Exception as e:
        raise ApiException(ApiCode.SET_ENV_VAR_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(
                               ApiCode.SET_ENV_VAR_FAILURE.value) % config_loader.get_config().get('env'), e)

    try:
        body = json.loads(execute_command(internal_data=cmds_list_as_string).get_data())
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_EXEC_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_EXEC_FAILURE.value), e)

    # only env vars that were set
    config_loader.get_config()['env'] = env_vars_set
    return Response(
        json.dumps(http.response(ApiCode.SUCCESS.value, ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                 ConfigDescriptor.description(body.get('description'),
                                                              config_loader.get_config()))), 200,
        mimetype="application/json")


@app.route('/commandparallel', methods=['POST', 'PUT'])
def execute_command_parallel():
    env.set_env_var(EnvConstants.TEMPLATE, "start.py")
    env.set_env_var(EnvConstants.VARIABLES, "commandinfo.json")
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        raise ApiException(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value),
                           ErrorMessage.HTTP_CODE.get(ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value))
    try:
        input_data_list = [x.strip() for x in input_data.split("\n")]
        command_in_parallel = CommandInParallel()
        response = command_in_parallel.run_commands(input_data_list)
    except Exception as e:
        raise ApiException(ApiCode.COMMAND_EXEC_FAILURE.value,
                           ErrorMessage.HTTP_CODE.get(ApiCode.COMMAND_EXEC_FAILURE.value), e)

    return Response(
        json.dumps(http.response(code=ApiCode.SUCCESS.value, message=ErrorMessage.HTTP_CODE.get(ApiCode.SUCCESS.value),
                                 description=response)), 200, mimetype="application/json")
