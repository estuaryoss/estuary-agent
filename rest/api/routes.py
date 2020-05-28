import json
import os
import re
import stat
import sys
import traceback
from pathlib import Path
from secrets import token_hex

import flask
import psutil
from flask import Response
from flask import request
from fluent import sender

from about import properties
from entities.render import Render
from rest.api import create_app
from rest.api.apiresponsehelpers.error_codes import ErrorCodes
from rest.api.apiresponsehelpers.http_response import HttpResponse
from rest.api.constants.api_code_constants import ApiCodeConstants
from rest.api.constants.env_constants import EnvConstants
from rest.api.definitions import test_info_init, unmodifiable_env_vars
from rest.api.logginghelpers.message_dumper import MessageDumper
from rest.api.swagger import swagger_file_content
from rest.utils.cmd_utils import CmdUtils
from rest.utils.env_startup import EnvStartup
from rest.utils.fluentd_utils import FluentdUtils
from rest.utils.io_utils import IOUtils
from rest.utils.process_utils import ProcessUtils
from rest.utils.testrunner_in_memory import TestRunnerInMemory

app = create_app()
logger = \
    sender.FluentSender(tag=properties.get('name'),
                        host=EnvStartup.get_instance().get("fluentd_ip_port").split(":")[0],
                        port=int(EnvStartup.get_instance().get("fluentd_ip_port").split(":")[1])) \
        if EnvStartup.get_instance().get("fluentd_ip_port") else None
fluentd_utils = FluentdUtils(logger)
message_dumper = MessageDumper()


@app.before_request
def before_request():
    ctx = app.app_context()
    http = HttpResponse()
    ctx.g.xid = token_hex(8)
    request_uri = request.environ.get("REQUEST_URI")

    # add here your custom header to be logged with fluentd
    message_dumper.set_header("X-Request-ID",
                              request.headers.get('X-Request-ID') if request.headers.get('X-Request-ID') else ctx.g.xid)
    message_dumper.set_header("Request-Uri", request_uri)

    response = fluentd_utils.emit(tag="api", msg=message_dumper.dump(request=request))
    app.logger.debug(response)
    if not str(request.headers.get("Token")) == str(EnvStartup.get_instance().get("http_auth_token")):
        if not ("/api/docs" in request_uri or "/swagger/swagger.yml" in request_uri):  # exclude swagger
            headers = {
                'X-Request-ID': message_dumper.get_header("X-Request-ID")
            }
            return Response(json.dumps(http.failure(ApiCodeConstants.UNAUTHORIZED,
                                                    ErrorCodes.HTTP_CODE.get(ApiCodeConstants.UNAUTHORIZED),
                                                    "Invalid Token",
                                                    str(traceback.format_exc()))), 401, mimetype="application/json",
                            headers=headers)


@app.after_request
def after_request(http_response):
    # if not json, do not alter
    try:
        headers = dict(http_response.headers)
        headers['X-Request-ID'] = message_dumper.get_header("X-Request-ID")
        http_response.headers = headers
    except:
        app.logger.debug("Message was not altered: " + message_dumper.dump(http_response))

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
        http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), dict(os.environ))),
        200, mimetype="application/json")


@app.route('/ping')
def ping():
    http = HttpResponse()

    return Response(
        json.dumps(http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), "pong")),
        200, mimetype="application/json")


@app.route('/about')
def about():
    http = HttpResponse()

    return Response(json.dumps(
        http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), properties["name"])),
        200,
        mimetype="application/json")


@app.route('/render/<template>/<variables>', methods=['GET', 'POST'])
def get_content_with_env(template, variables):
    try:
        input_json = request.get_json(force=True)
        for key, value in input_json.items():
            if key not in unmodifiable_env_vars:
                os.environ[key] = value
    except:
        pass

    os.environ['TEMPLATE'] = template.strip()
    os.environ['VARIABLES'] = variables.strip()

    http = HttpResponse()
    try:
        r = Render(os.environ['TEMPLATE'], os.environ['VARIABLES'])
        response = Response(r.rend_template(), 200, mimetype="text/plain")
        # response = http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), result), 200
    except Exception as e:
        result = "Exception({})".format(e.__str__())
        response = Response(json.dumps(http.failure(ApiCodeConstants.JINJA2_RENDER_FAILURE,
                                                    ErrorCodes.HTTP_CODE.get(ApiCodeConstants.JINJA2_RENDER_FAILURE),
                                                    result,
                                                    str(traceback.format_exc()))), 404, mimetype="application/json")

    return response


@app.route('/test', methods=['GET'])
def get_test_info():
    http = HttpResponse()
    io_utils = IOUtils()
    variables = "testinfo.json"
    file = EnvConstants.VARIABLES_PATH + "/" + variables

    try:
        file_path = Path(file)
        if not file_path.is_file():
            io_utils.write_to_file_dict(file, test_info_init)
        test_env_vars = json.loads(io_utils.read_file(file))
        test_env_vars["processes"] = [p.info for p in psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        exception = "Exception({})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.GET_CONTAINER_TEST_INFO_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.GET_CONTAINER_TEST_INFO_FAILURE),
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")
    return Response(
        json.dumps(
            http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), test_env_vars)),
        200,
        mimetype="application/json")


@app.route('/env', methods=['POST'])
def set_env():
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    try:
        input_json = json.loads(input_data)
    except Exception as e:
        exception = "Exception({0})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.INVALID_JSON_PAYLOAD,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.INVALID_JSON_PAYLOAD) % str(
                                                    input_data),
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    try:
        for key, value in input_json.items():
            if key not in unmodifiable_env_vars:
                os.environ[key] = value
    except Exception as e:
        exception = "Exception({})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.SET_ENV_VAR_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SET_ENV_VAR_FAILURE) % str(
                                                    input_data),
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")
    return Response(
        json.dumps(
            http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), input_json)),
        200,
        mimetype="application/json")


@app.route('/env/<name>', methods=['GET'])
def get_env(name):
    name = name.upper().strip()
    http = HttpResponse()
    try:
        response = Response(json.dumps(
            http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                         os.environ[name])), 200,
            mimetype="application/json")
    except Exception as e:
        result = "Exception({})".format(e.__str__())
        response = Response(json.dumps(http.failure(ApiCodeConstants.GET_CONTAINER_ENV_VAR_FAILURE,
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.GET_CONTAINER_ENV_VAR_FAILURE) % name,
                                                    result,
                                                    str(traceback.format_exc()))), 404, mimetype="application/json")
    return response


@app.route('/test/<test_id>', methods=['POST', 'PUT'])
def test_start(test_id):
    test_id = test_id.strip()
    variables = "testinfo.json"
    start_py_path = str(Path(".").absolute()) + "/start.py"
    os.environ['TEMPLATE'] = "start.py"
    os.environ['VARIABLES'] = variables
    io_utils = IOUtils()
    cmd_utils = CmdUtils()
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.failure(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                str(traceback.format_exc()))), 404, mimetype="application/json")
    try:
        input_data_list = io_utils.get_filtered_list_regex(input_data.split("\n"),
                                                           re.compile(r'(\s+|[^a-z]|^)rm\s+.*$'))
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        test_info_init["id"] = test_id
        io_utils.write_to_file_dict(EnvConstants.TEST_INFO_PATH, test_info_init)
        os.chmod(start_py_path, stat.S_IRWXU)
        input_data_list.insert(0, test_id)
        input_data_list.insert(0, start_py_path)
        # input_data_list.insert(0, "python")
        cmd_utils.run_cmd_detached(input_data_list)
    except Exception as e:
        result = "Exception({})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.TEST_START_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.TEST_START_FAILURE) % test_id,
                                                result,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    return Response(
        json.dumps(http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), test_id)),
        200,
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
            return Response(json.dumps(http.failure(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                    str(traceback.format_exc()))), 404, mimetype="application/json")
        if not file_content:
            return Response(json.dumps(http.failure(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                    str(traceback.format_exc()))), 404, mimetype="application/json")
        io_utils.write_to_file_binary(file_path, file_content)
    except Exception as e:
        exception = "Exception({})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.UPLOAD_TEST_CONFIG_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.UPLOAD_TEST_CONFIG_FAILURE),
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    return Response(
        json.dumps(http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))), 200,
        mimetype="application/json")


@app.route('/file', methods=['GET'])
def get_file():
    io_utils = IOUtils()
    http = HttpResponse()
    header_key = 'File-Path'

    file_path = request.headers.get(f"{header_key}")
    if not file_path:
        return Response(json.dumps(http.failure(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    try:
        response = io_utils.read_file_byte_array(file_path), 200
    except Exception as e:
        exception = "Exception({})".format(e.__str__())
        response = Response(json.dumps(http.failure(ApiCodeConstants.GET_FILE_FAILURE,
                                                    ErrorCodes.HTTP_CODE.get(
                                                        ApiCodeConstants.GET_FILE_FAILURE),
                                                    exception,
                                                    str(traceback.format_exc()))), 404, mimetype="application/json")
    return response


@app.route('/folder', methods=['GET'])
def get_results_folder():
    io_utils = IOUtils()
    http = HttpResponse()
    archive_name = "results"
    header_key = 'Folder-Path'

    folder_path = request.headers.get(f"{header_key}")
    if not folder_path:
        return Response(json.dumps(http.failure(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    try:
        io_utils.zip_file(archive_name, folder_path)
    except Exception as e:
        result = "Exception({})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.FOLDER_ZIP_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.FOLDER_ZIP_FAILURE) % folder_path,
                                                result,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")
    return flask.send_file(
        f"/tmp/{archive_name}.zip",
        mimetype='application/zip',
        as_attachment=True), 200


@app.route('/test', methods=['DELETE'])
def test_stop():
    io_utils = IOUtils()
    process_utils = ProcessUtils(logger)
    http = HttpResponse()
    variables = "testinfo.json"
    test_id = json.loads(io_utils.read_file(os.environ.get('VARS_DIR') + f"/{variables}"))["id"]

    try:
        response = get_test_info()
        pid = json.loads(response.get_data()).get('message').get('pid')
        if not isinstance(pid, str):
            if psutil.pid_exists(int(pid)):
                parent = psutil.Process()

                children = parent.children()
                for p in children:
                    p.terminate()
                _, alive = psutil.wait_procs(children, timeout=3, callback=process_utils.on_terminate)
                for p in alive:
                    p.kill()
    except:
        exception = "Exception({0})".format(sys.exc_info()[0])
        return Response(json.dumps(http.failure(ApiCodeConstants.TEST_STOP_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.TEST_STOP_FAILURE) % test_id,
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    return Response(
        json.dumps(http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), test_id)),
        200,
        mimetype="application/json")


@app.route('/command', methods=['POST', 'PUT'])
def execute_command():
    variables = "commandinfo.json"
    os.environ['TEMPLATE'] = "start.py"
    os.environ['VARIABLES'] = variables
    io_utils = IOUtils()
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.failure(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                str(traceback.format_exc()))), 404, mimetype="application/json")
    try:
        input_data_list = io_utils.get_filtered_list_regex(input_data.split("\n"),
                                                           re.compile(r'(\s+|[^a-z]|^)rm\s+.*$'))
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        test_runner = TestRunnerInMemory()
        response = test_runner.run_commands(input_data_list)
    except Exception as e:
        exception = "Exception({0})".format(e.__str__())
        return Response(json.dumps(http.failure(ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                ErrorCodes.HTTP_CODE.get(
                                                    ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                exception,
                                                str(traceback.format_exc()))), 404, mimetype="application/json")

    return Response(
        json.dumps(
            http.success(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), response)),
        200,
        mimetype="application/json")
