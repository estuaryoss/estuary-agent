#!/usr/bin/env python3
import platform
import shlex
import time
import unittest
import zipfile

import requests
import yaml
from flask import json
from parameterized import parameterized

from tests.rest.utils import Utils
from tests.rest_win.api_code_constants import ApiCodeConstants
from tests.rest_win.error_codes import ErrorCodes


class FlaskServerTestCase(unittest.TestCase):
    server = "http://127.0.0.1:8080"

    expected_version = "4.0.6"

    def setUp(self):
        requests.delete(self.server + "/test")

    def tearDown(self):
        requests.delete(self.server + "/test")

    def test_env_endpoint(self):
        response = requests.get(self.server + "/env")

        body = json.loads(response.text)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(body.get('message')), 7)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    def test_ping_endpoint(self):
        response = requests.get(self.server + "/ping")

        body = json.loads(response.text)
        headers = response.headers

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), "pong")
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))
        self.assertEqual(len(headers.get('X-Request-ID')), 16)

    def test_getenv_endpoint_p(self):
        env_var = "VARS_DIR"
        response = requests.get(self.server + "/env/" + env_var)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertIsNotNone(body.get('message'))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    def test_getenv_endpoint_n(self):
        env_var = "alabalaportocala"
        response = requests.get(self.server + "/env/" + env_var)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.GET_ENV_VAR_FAILURE) % env_var.upper())
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.GET_ENV_VAR_FAILURE)
        self.assertIsNotNone(body.get('time'))

    def test_about_endpoint_xid_sent_is_the_same(self):
        xid = "anaaremere"
        headers = {'X-Request-ID': xid}
        response = requests.get(self.server + "/about", headers=headers)
        service_name = "estuary-testrunner"
        body = response.json()
        headers = response.headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), service_name)
        self.assertEqual(body.get('name'), service_name)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))
        self.assertEqual(headers.get('X-Request-ID'), xid)

    def test_about_endpoint_unauthorized(self):
        headers = {'Token': "invalidtoken"}
        response = requests.get(self.server + "/about", headers=headers)
        service_name = "estuary-testrunner"
        body = response.json()
        headers = response.headers
        self.assertEqual(response.status_code, 401)
        self.assertEqual(body.get('description'), "Invalid Token")
        self.assertEqual(body.get('name'), service_name)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.UNAUTHORIZED))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.UNAUTHORIZED)
        self.assertIsNotNone(body.get('time'))
        self.assertEqual(len(headers.get('X-Request-ID')), 16)

    @unittest.skipIf(platform.system() == "Windows", "Skip on Win")
    def test_swagger_endpoint(self):
        response = requests.get(self.server + "/api/docs")

        body = response.text
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body.find("html") >= 0)

    @unittest.skipIf(platform.system() == "Windows", "Skip on Win")
    def test_swagger_endpoint_swagger_still_accesible(self):
        headers = {'Token': 'whateverinvalid'}
        response = requests.get(self.server + "/api/docs", headers=headers)

        body = response.text
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body.find("html") >= 0)

    # @unittest.skipIf(os.environ.get('TEMPLATES_DIR') == ("inputs/templates"), "Skip on VM")
    def test_swagger_yml_endpoint(self):
        response = requests.get(self.server + "/swagger/swagger.yml")

        self.assertEqual(response.status_code, 200)

    def test_swagger_yml_swagger_still_accesible(self):
        headers = {'Token': 'whateverinvalid'}
        response = requests.get(self.server + "/swagger/swagger.yml", headers=headers)

        self.assertEqual(response.status_code, 200)

    @parameterized.expand([
        ("json.j2", "json.json"),
        ("yml.j2", "yml.yml")
    ])
    def test_rend_endpoint(self, template, variables):
        response = requests.get(self.server + "/render/" + template + "/" + variables)

        body = yaml.safe_load(response.text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(body), 3)

    @parameterized.expand([
        ("json.j2", "doesnotexists.json"),
        ("yml.j2", "doesnotexists.yml")
    ])
    def test_rend_endpoint(self, template, variables):
        expected = "Exception([Errno 2] No such file or directory:"

        response = requests.get(self.server + "/render/" + template + "/" + variables)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertIn(expected, body.get("description"))

    @parameterized.expand([
        ("doesnotexists.j2", "json.json"),
        ("doesnotexists.j2", "yml.yml")
    ])
    def test_rend_endpoint(self, template, variables):
        expected = f"Exception"

        response = requests.get(self.server + "/render/" + template + "/" + variables)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertIn(expected, body.get("description"))

    @parameterized.expand([
        ("standalone.yml", "variables.yml")
    ])
    @unittest.skipIf(platform.system() == "Windows", "Skip on Win")
    def test_rendwithenv_endpoint(self, template, variables):
        payload = {'DATABASE': 'mysql56', 'IMAGE': 'latest'}
        headers = {'Content-type': 'application/json'}

        response = requests.post(self.server + f"/render/{template}/{variables}", data=json.dumps(payload),
                                 headers=headers)

        body = yaml.safe_load(response.text)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(body.get("services")), 2)
        self.assertEqual(int(body.get("version")), 3)

    def test_getfile_p(self):
        headers = {
            'Content-type': 'application/json',
            'File-Path': 'requirements.txt'
        }

        response = requests.get(self.server + f"/file", headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.text), 0)

    def test_getfile_n(self):
        headers = {
            'Content-type': 'application/json',
            'File-Path': 'requirements.txttxttxt'
        }

        response = requests.get(self.server + f"/file", headers=headers)
        body = response.json()
        headers = response.headers
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.GET_FILE_FAILURE))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.GET_FILE_FAILURE)
        self.assertIsNotNone(body.get('time'))
        self.assertEqual(len(headers.get('X-Request-ID')), 16)

    def test_getfolder_header_missing_n(self):
        header_key = 'Folder-Path'
        headers = {'Content-type': 'application/json'}

        response = requests.get(
            self.server + f"/folder", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED)
        self.assertIsNotNone(body.get('time'))

    def test_getfolder_p(self):
        utils = Utils()
        headers = {
            'Content-type': 'application/json',
            'Folder-Path': 'inputs'
        }

        response = requests.get(
            self.server + f"/folder", headers=headers)

        body = response.text
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(body) > 0)
        utils.write_to_file("./response.zip", response.content)
        self.assertTrue(zipfile.is_zipfile("response.zip"))
        with zipfile.ZipFile('response.zip', 'w') as responsezip:
            self.assertTrue(responsezip.testzip() is None)

    def test_getfolder_file_not_folder_n(self):
        container_folder = 'requirements.txt'
        headers = {
            'Content-type': 'application/json',
            'Folder-Path': container_folder
        }

        response = requests.get(
            self.server + f"/folder", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.FOLDER_ZIP_FAILURE) % container_folder)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.FOLDER_ZIP_FAILURE)
        self.assertIsNotNone(body.get('time'))

    def test_getfolder_folder_not_found_n(self):
        container_folder = '/dummy'
        headers = {
            'Content-type': 'application/json',
            'Folder-Path': container_folder
        }

        response = requests.get(
            self.server + f"/folder", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get('message'),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.FOLDER_ZIP_FAILURE) % container_folder)
        self.assertIn("Exception", body.get("description"))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.FOLDER_ZIP_FAILURE)
        self.assertIsNotNone(body.get('time'))

    def test_getfolder_folder_param_missing_n(self):
        header_key = 'Folder-Path'
        headers = {
            'Content-type': 'application/json'
        }

        response = requests.get(
            self.server + f"/folder", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % header_key)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED)
        self.assertIsNotNone(body.get('time'))

    @parameterized.expand([
        "ping -n 1 127.0.0.1 \n ping -n 2 127.0.0.1 \n ping -n 3 127.0.0.1", "mvn -h", "alabalaportocala"
    ])
    def test_teststart_p(self, payload):
        test_id = "106"
        headers = {'Content-type': 'text/plain'}

        response = requests.post(
            self.server + f"/test/{test_id}",
            data=payload, headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('description'), test_id)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    @parameterized.expand([
        "", "  "
    ])
    def test_teststart_missing_payload_n(self, payload):
        test_id = "105"
        headers = {'Content-type': 'text/plain'}

        response = requests.post(
            self.server + f"/test/{test_id}",
            data=payload, headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))
        self.assertEqual(body.get('description'),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED)
        self.assertIsNotNone(body.get('time'))

    @parameterized.expand([
        "4"
    ])
    def test_gettestinfo_p(self, payload):
        test_id = "103"
        data_payload = f" ping -n {payload} 127.0.0.1 \n invalid_command"
        commands = list(map(lambda x: x.strip(), data_payload.split("\n")))
        headers = {'Content-type': 'text/plain'}

        response = requests.post(
            self.server + f"/test/{test_id}",
            data=f"{data_payload}", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), test_id)

        time.sleep(1)
        response = requests.get(self.server + "/test")
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description').get('id'), test_id)
        self.assertEqual(body.get('description').get('started'), True)
        self.assertEqual(body.get('description').get('finished'), False)
        self.assertNotEqual(body.get('description').get('startedat'), "none")
        self.assertNotEqual(body.get('description').get('finishedat'), "none")
        self.assertEqual(round(int(body.get('description').get('duration'))), 0)
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get("status"), "in progress")
        self.assertEqual(body.get('description').get("commands").get(commands[1]).get("status"), "scheduled")

        time.sleep(int(payload) - 2)
        response = requests.get(self.server + "/test")
        body = response.json()
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get("status"), "in progress")
        self.assertNotEqual(body.get('description').get("commands").get(commands[0]).get('startedat'), "none")
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get('finishedat'),
                         None)  # its not yet written
        self.assertIsInstance(body.get('description').get("commands").get(commands[0]).get("details"),
                              dict)  # is empty because the details are filled after exec
        time.sleep(int(payload) + 2)
        response = requests.get(self.server + "/test")
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description').get('id'), test_id)
        self.assertEqual(body.get('description').get('started'), False)
        self.assertEqual(body.get('description').get('finished'), True)
        self.assertGreaterEqual(len(body.get('description').get('processes')), 2)
        self.assertNotEqual(body.get('description').get('startedat'), "none")
        self.assertNotEqual(body.get('description').get('finishedat'), "none")
        self.assertNotEqual(body.get('description').get('duration'), "none")
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get("status"), "finished")
        self.assertNotEqual(body.get('description').get("commands").get(commands[0]).get("startedat"), "none")
        self.assertNotEqual(body.get('description').get("commands").get(commands[0]).get("finishedat"), "none")
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get("details").get("err"), "")
        self.assertIsInstance(body.get('description').get("commands").get(commands[0]).get("details").get("pid"), int)
        self.assertIsInstance(body.get('description').get("commands").get(commands[0]).get("details").get("code"), int)
        self.assertIsInstance(body.get('description').get("commands").get(commands[0]).get("details").get("args"), list)
        self.assertEqual(body.get('description').get("commands").get(commands[1]).get("status"), "finished")
        self.assertNotEqual(body.get('description').get("commands").get(commands[1]).get("startedat"), "none")
        self.assertNotEqual(body.get('description').get("commands").get(commands[1]).get("finishedat"), "none")
        self.assertNotEqual(body.get('description').get("commands").get(commands[1]).get("duration"), "none")
        self.assertIn("is not recognized as an internal or external command",
                      body.get('description').get("commands").get(commands[1]).get("details").get("err"))
        self.assertIsInstance(body.get('description').get("commands").get(commands[1]).get("details").get("pid"), int)
        self.assertIsInstance(body.get('description').get("commands").get(commands[1]).get("details").get("code"), int)
        self.assertIsInstance(body.get('description').get("commands").get(commands[1]).get("details").get("args"), list)

    @parameterized.expand([
        "3"
    ])
    def test_gettestinfo_repeated_should_return_always_200_p(self, payload):
        test_id = "102"
        data_payload = f"ping -n  {payload} 127.0.0.1\n ping -n {payload} 127.0.0.1"
        repetitions = 10
        headers = {'Content-type': 'text/plain'}

        response = requests.post(
            self.server + f"/test/{test_id}",
            data=f"{data_payload}", headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), test_id)
        start = time.time()
        for i in range(1, repetitions):
            response = requests.get(self.server + "/test")
            self.assertEqual(response.status_code, 200)
        end = time.time()
        print(f"made {repetitions} gettestinfo repetitions in {end - start} s")

    def test_teststop_p(self):
        test_id = "100"
        data_payload = f"ping -n 7 127.0.0.1\n ping -n 3600 127.0.0.1\n ping -n 3601 127.0.0.1"
        commands = list(map(lambda x: x.strip(), data_payload.split("\n")))
        headers = {'Content-type': 'text/plain'}

        response = requests.delete(self.server + "/test")
        self.assertEqual(response.status_code, 200)

        response = requests.post(
            self.server + f"/test/{test_id}",
            data=f"{data_payload}", headers=headers)
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), test_id)
        time.sleep(4)
        response = requests.get(self.server + "/test")
        body = response.json()
        self.assertEqual(body.get('description').get("id"), test_id)
        self.assertEqual(body.get('description').get("started"), True)
        self.assertEqual(body.get('description').get("finished"), False)
        self.assertEqual(body.get('description').get("commands").get(commands[0]).get("status"), "in progress")
        self.assertEqual(body.get('description').get("commands").get(commands[1]).get("status"), "scheduled")
        self.assertEqual(body.get('description').get("commands").get(commands[2]).get("status"), "scheduled")
        time.sleep(2)
        response = requests.delete(self.server + "/test")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get('description'), test_id)

        response = requests.get(self.server + "/test")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # self.assertEqual(body.get('description').get("finished"), True)
        self.assertEqual(body.get('description').get("id"), f"{test_id}")
        # self.assertEqual(body.get('description').get("started"), False)

    @parameterized.expand([
        "{\"file\": \"/dummy/config.properties\", \"content\": \"ip=10.0.0.1\\nrequest_sec=100\\nthreads=10\\ntype=dual\"}"
    ])
    def test_uploadfile_header_not_provided_n(self, payload):
        headers = {'Content-type': 'application/json'}
        mandatory_header_key = 'File-Path'

        response = requests.put(
            self.server + f"/file",
            data=payload, headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED) % mandatory_header_key)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED)
        self.assertIsNotNone(body.get('time'))

    @parameterized.expand([
        ""
    ])
    def test_uploadfile_empty_body_n(self, payload):
        headers = {
            'Content-type': 'application/json',
            'File-Path': '/tmp/config.properties'
        }

        response = requests.post(
            self.server + f"/file",
            data=payload, headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED)
        self.assertIsNotNone(body.get('time'))

    @parameterized.expand([
        "{\"file\": \"/tmp/config.properties\", \"content\": \"ip=10.0.0.1\\nrequest_sec=100\\nthreads=10\\ntype=dual\"}"
    ])
    def test_uploadfile_p(self, payload):
        headers = {
            'Content-type': 'application/json',
            'File-Path': '/tmp/config.properties'
        }

        response = requests.post(
            self.server + f"/file",
            data=payload, headers=headers)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_n(self):
        command = "abracadabra"  # not working on linux

        response = requests.post(
            self.server + f"/command",
            data=command)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIn("is not recognized as an internal or external command",
                      body.get('description').get('commands').get(command).get('details').get('err'))
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('out'), "")
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_p(self):
        command = "type requirements.txt"

        response = requests.post(
            self.server + f"/command",
            data=command)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('code'), 0)
        self.assertNotEqual(body.get('description').get('commands').get(command).get('details').get('out'), "")
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('err'), "")
        self.assertGreater(body.get('description').get('commands').get(command).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(command).get('details').get('args'), list)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_java_isinstalled_p(self):
        command = "java -version"

        response = requests.post(
            self.server + f"/command",
            data=command)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('code'), 0)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('out'), "")
        self.assertNotIn("is not recognized",
                         body.get('description').get('commands').get(command).get('details').get('err'))
        self.assertGreater(body.get('description').get('commands').get(command).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(command).get('details').get('args'), list)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_grep_things_p(self):
        file = "main_flask.py"
        command = "dir /B | findstr /R {}".format(file)

        response = requests.post(
            self.server + f"/command",
            data=command)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('code'), 0)
        self.assertIn("main", body.get('description').get('commands').get(command).get('details').get('out'))
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('err'), "")
        self.assertGreater(body.get('description').get('commands').get(command).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(command).get('details').get('args'), list)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_cmds_sep_by_andand_p(self):
        command = "echo 1 && echo 2"

        response = requests.post(
            self.server + f"/command",
            data=command)

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('code'), 0)
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('out'), "1 \r\n2")
        self.assertEqual(body.get('description').get('commands').get(command).get('details').get('err'), "")
        self.assertGreater(body.get('description').get('commands').get(command).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(command).get('details').get('args'), list)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_grep_and_out_redirect_p(self):
        file = "whatever.txt"
        commands = ["dir > {}".format(file), "type {}".format(file)]

        response = requests.post(
            self.server + f"/command",
            data="\n".join(commands))

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(body.get('description').get('commands').get(commands[0]).get('details').get('code'), 0)
        self.assertEqual(body.get('description').get('commands').get(commands[0]).get('details').get('out'), "")
        self.assertEqual(body.get('description').get('commands').get(commands[0]).get('details').get('err'), "")
        self.assertGreater(body.get('description').get('commands').get(commands[0]).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(commands[0]).get('details').get('args'), list)
        self.assertEqual(body.get('description').get('commands').get(commands[1]).get('details').get('code'), 0)
        self.assertIn("main", body.get('description').get('commands').get(commands[1]).get('details').get('out'))
        self.assertEqual(body.get('description').get('commands').get(commands[1]).get('details').get('err'), "")
        self.assertGreater(body.get('description').get('commands').get(commands[1]).get('details').get('pid'), 0)
        self.assertIsInstance(body.get('description').get('commands').get(commands[1]).get('details').get('args'), list)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_sum_seq_p(self):
        a = 2
        b = 3
        commands = ["ping -n {} 127.0.0.1".format(a), "ping -n {} 127.0.0.1".format(b)]

        response = requests.post(self.server + f"/command", data="\n".join(commands))
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(round(int(body.get('description').get('duration'))), a + b - 2)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[0]).get('duration'))), a - 1)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[1]).get('duration'))), b - 1)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_sum_parallel_p(self):
        a = 2
        b = 3
        commands = ["ping -n {} 127.0.0.1".format(a), "ping -n {} 127.0.0.1".format(b)]

        response = requests.post(self.server + f"/commandparallel", data="\n".join(commands))
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(round(int(body.get('description').get('duration'))), b - 1)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[0]).get('duration'))), a - 1)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[1]).get('duration'))), b - 1)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_arg_with_spaces(self):
        raw_cmd = "java -cp whatever.jar com.java.org -cmd my_cmd -args \"a;b c d;e\""
        shlex_cmd = shlex.split(raw_cmd)

        response = requests.post(self.server + f"/command", data=raw_cmd)
        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(len(body.get('description').get('commands').get(raw_cmd).get('details').get('args')),
                         len(shlex_cmd))
        self.assertEqual(body.get('description').get('commands').get(raw_cmd).get('details').get('args')[-1],
                         shlex_cmd[-1])
        self.assertIsNotNone(body.get('time'))

    def test_executetest_sum_seq_p(self):
        test_id = "test_executetest_sum_seq_p"
        a = 2
        b = 3
        commands = ["ping -n {} 127.0.0.1".format(a), "ping -n {} 127.0.0.1".format(b)]

        response = requests.post(self.server + "/test/{}".format(test_id), data="\n".join(commands))
        self.assertEqual(response.status_code, 200)
        time.sleep(a + b + 1)

        response = requests.get(self.server + f"/test")
        body = response.json()
        self.assertEqual(response.status_code, 200)

        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertEqual(round(int(body.get('description').get('duration'))), a + b - 2)
        self.assertIsInstance(body.get('description').get('duration'), float)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[0]).get('duration'))), a - 1)
        self.assertIsInstance(body.get('description').get('commands').get(commands[0]).get('duration'), float)
        self.assertEqual(round(int(body.get('description').get('commands').get(commands[1]).get('duration'))), b - 1)
        self.assertIsInstance(body.get('description').get('commands').get(commands[1]).get('duration'), float)
        self.assertIsNotNone(body.get('time'))

    def test_executecommand_timeout_from_client_n(self):
        command = "ping -n 20 127.0.0.1"

        try:
            requests.post(
                self.server + f"/command",
                data=command, timeout=2)
        except Exception as e:
            self.assertIsInstance(e, requests.exceptions.ReadTimeout)

    def test_setenv_endpoint_emptyjson_p(self):
        payload = {}
        headers = {'Content-type': 'application/json'}

        response = requests.post(self.server + f"/env", data=json.dumps(payload),
                                 headers=headers)
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), payload)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    def test_setenv_endpoint_jsonwithvalues_p(self):
        payload = {"a": "b"}
        headers = {'Content-type': 'application/json'}

        response = requests.post(self.server + f"/env", data=json.dumps(payload),
                                 headers=headers)
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.get('description'), payload)
        self.assertEqual(body.get("message"), ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SUCCESS))
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SUCCESS)
        self.assertIsNotNone(body.get('time'))

    def test_setenv_endpoint_notjson_n(self):
        payload = "whateverinvalid"
        headers = {'Content-type': 'application/json'}

        response = requests.post(self.server + f"/env", data=payload, headers=headers)
        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertIn("Exception", body.get("description"))
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.INVALID_JSON_PAYLOAD) % payload)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.INVALID_JSON_PAYLOAD)
        self.assertIsNotNone(body.get('time'))

    def test_setenv_endpoint_namenotset_n(self):
        payload = json.dumps("whateverinvalid")
        headers = {'Content-type': 'application/json'}

        response = requests.post(self.server + f"/env", data=payload, headers=headers)
        body = response.json()
        self.assertEqual(response.status_code, 404)
        self.assertIn("Exception", body.get("description"))
        self.assertEqual(body.get("message"),
                         ErrorCodes.HTTP_CODE.get(ApiCodeConstants.SET_ENV_VAR_FAILURE) % payload)
        self.assertEqual(body.get('version'), self.expected_version)
        self.assertEqual(body.get('code'), ApiCodeConstants.SET_ENV_VAR_FAILURE)
        self.assertIsNotNone(body.get('time'))


if __name__ == '__main__':
    unittest.main()