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
from rest.utils.testrunner_parallel import TestRunnerParallel

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
    request_uri = request.full_path

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
        headers['X-Request-ID'] = message_dumper.get_header("X-Request-ID")
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
                      description=dict(os.environ))),
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
    except Exception as e:
        response = Response(json.dumps(http.response(code=ApiCodeConstants.JINJA2_RENDER_FAILURE,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.JINJA2_RENDER_FAILURE),
                                                     description="Exception({})".format(e.__str__()))), 404,
                            mimetype="application/json")

    return response


@app.route('/test', methods=['GET'])
def get_test_info():
    http = HttpResponse()
    io_utils = IOUtils()
    file = "testinfo.json"

    try:
        file_path = Path(file)
        if not file_path.is_file():
            io_utils.write_to_file_dict(file, test_info_init)
        test_env_vars = json.loads(io_utils.read_file(file))
        test_env_vars["processes"] = [p.info for p in psutil.process_iter(attrs=['pid', 'name', 'username', 'status'])]

    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.GET_TEST_INFO_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.GET_TEST_INFO_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")
    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=test_env_vars)),
        200,
        mimetype="application/json")


@app.route('/env', methods=['POST'])
def set_env():
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    try:
        input_json = json.loads(input_data)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.INVALID_JSON_PAYLOAD,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.INVALID_JSON_PAYLOAD) % str(
                                                     input_data),
                                                 description="Exception({0})".format(e.__str__()))), 404,
                        mimetype="application/json")

    try:
        for key, value in input_json.items():
            if key not in unmodifiable_env_vars:
                os.environ[key] = value
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.SET_ENV_VAR_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.SET_ENV_VAR_FAILURE) % str(
                                                     input_data),
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")
    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), input_json)),
        200,
        mimetype="application/json")


@app.route('/env/<name>', methods=['GET'])
def get_env(name):
    name = name.upper().strip()
    http = HttpResponse()
    try:
        response = Response(json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          os.environ[name])), 200,
            mimetype="application/json")
    except Exception as e:
        response = Response(json.dumps(http.response(code=ApiCodeConstants.GET_ENV_VAR_FAILURE,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.GET_ENV_VAR_FAILURE) % name,
                                                     description="Exception({})".format(e.__str__()))), 404,
                            mimetype="application/json")
    return response


@app.route('/test/<test_id>', methods=['POST', 'PUT'])
def test_start(test_id):
    test_id = test_id.strip()
    variables = "testinfo.json"
    start_py_path = str(Path(".").absolute()) + "/start.py"
    os.environ['TEMPLATE'] = "start.py"
    os.environ['VARIABLES'] = variables
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
                                                 )), 404, mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        test_info_init["id"] = test_id
        io_utils.write_to_file_dict(EnvConstants.TEST_INFO_PATH, test_info_init)
        os.chmod(start_py_path, stat.S_IRWXU)
        command.insert(0, ";".join(input_data_list))  # second arg is cmd list separated by ;
        command.insert(0, test_id)  # first arg is test id
        command.insert(0, start_py_path)
        # final_command.insert(0, "python")
        cmd_utils.run_cmd_detached(command)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.TEST_START_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.TEST_START_FAILURE) % test_id,
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(ApiCodeConstants.SUCCESS, ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS), test_id)),
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
            return Response(json.dumps(http.response(code=ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key,
                                                     description=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 404,
                            mimetype="application/json")
        if not file_content:
            return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                     description=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 404,
                            mimetype="application/json")
        io_utils.write_to_file_binary(file_path, file_content)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.UPLOAD_TEST_CONFIG_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.UPLOAD_TEST_CONFIG_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 404,
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
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 404,
                        mimetype="application/json")

    try:
        response = io_utils.read_file_byte_array(file_path), 200
    except Exception as e:
        response = Response(json.dumps(http.response(code=ApiCodeConstants.GET_FILE_FAILURE,
                                                     message=ErrorCodes.HTTP_CODE.get(
                                                         ApiCodeConstants.GET_FILE_FAILURE),
                                                     description="Exception({})".format(e.__str__()))), 404,
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
                                                     ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)), 404,
                        mimetype="application/json")

    try:
        io_utils.zip_file(archive_name, folder_path)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.FOLDER_ZIP_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.FOLDER_ZIP_FAILURE) % folder_path,
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")
    return flask.send_file(
        f"/tmp/{archive_name}.zip",
        mimetype='application/zip',
        as_attachment=True), 200


@app.route('/test', methods=['DELETE'])
def test_stop():
    io_utils = IOUtils()
    process_utils = ProcessUtils(logger)
    http = HttpResponse()
    test_id = json.loads(io_utils.read_file("testinfo.json"))["id"]

    try:
        response = get_test_info()
        pid = json.loads(response.get_data()).get('description').get('pid')
        if not isinstance(pid, str):
            if psutil.pid_exists(int(pid)):
                parent = psutil.Process()

                children = parent.children()
                for p in children:
                    p.terminate()
                _, alive = psutil.wait_procs(children, timeout=3, callback=process_utils.on_terminate)
                for p in alive:
                    p.kill()
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.TEST_STOP_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.TEST_STOP_FAILURE) % test_id,
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=test_id)),
        200,
        mimetype="application/json")


@app.route('/command', methods=['POST', 'PUT'])
def execute_command():
    variables = "commandinfo.json"
    os.environ['TEMPLATE'] = "start.py"
    os.environ['VARIABLES'] = variables
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 404,
                        mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        test_runner = TestRunnerInMemory()
        response = test_runner.run_commands(input_data_list)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=response)),
        200,
        mimetype="application/json")


@app.route('/commandparallel', methods=['POST', 'PUT'])
def execute_command_parallel():
    variables = "commandinfo.json"
    os.environ['TEMPLATE'] = "start.py"
    os.environ['VARIABLES'] = variables
    http = HttpResponse()
    input_data = request.data.decode("UTF-8", "replace").strip()

    if not input_data:
        return Response(json.dumps(http.response(code=ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED),
                                                 description=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))), 404,
                        mimetype="application/json")
    try:
        input_data_list = input_data.split("\n")
        input_data_list = list(map(lambda x: x.strip(), input_data_list))
        test_runner = TestRunnerParallel()
        response = test_runner.run_commands(input_data_list)
    except Exception as e:
        return Response(json.dumps(http.response(code=ApiCodeConstants.COMMAND_EXEC_FAILURE,
                                                 message=ErrorCodes.HTTP_CODE.get(
                                                     ApiCodeConstants.COMMAND_EXEC_FAILURE),
                                                 description="Exception({})".format(e.__str__()))), 404,
                        mimetype="application/json")

    return Response(
        json.dumps(
            http.response(code=ApiCodeConstants.SUCCESS, message=ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS),
                          description=response)),
        200,
        mimetype="application/json")
