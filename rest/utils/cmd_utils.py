import base64
import subprocess

from rest.environment.environment import EnvironmentSingleton
from rest.utils.io_utils import IOUtils


class CmdUtils:
    __env = EnvironmentSingleton.get_instance()

    @staticmethod
    def run_cmd_detached(command):
        p = subprocess.Popen(command, env=CmdUtils.__env.get_env_and_virtual_env())
        print("Opened pid {} for command {}".format(p.pid, command))

    @staticmethod
    def run_cmd_shell_true(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=CmdUtils.__env.get_env_and_virtual_env(), shell=True)
        return CmdUtils.__get_subprocess_data(p)

    @staticmethod
    def run_cmd_shell_true_to_file(command):
        file_path_out = base64.b64encode(command) + "_out.cmd"
        file_path_err = base64.b64encode(command) + "_err.cmd"
        IOUtils.delete_files([file_path_out, file_path_err])
        with open(file_path_out, 'r+') as fh_out, open(file_path_err, 'r+') as fh_err:
            p = subprocess.Popen(command, stdout=fh_out, stderr=fh_err,
                                 env=CmdUtils.__env.get_env_and_virtual_env(), shell=True)

        return CmdUtils.__get_subprocess_data_file(p, fh_out=fh_out, fh_err=fh_err)

    @staticmethod
    def run_cmd_shell_false(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=CmdUtils.__env.get_env_and_virtual_env())
        return CmdUtils.__get_subprocess_data(p)

    @staticmethod
    def __get_subprocess_data(p):
        out, err = p.communicate()

        return {
            "out": out.decode("UTF-8", "replace"),
            "err": err.decode("UTF-8", "replace"),
            "code": p.returncode,
            "pid": p.pid,
            "args": p.args
        }

    @staticmethod
    def __get_subprocess_data_file(p, fh_out, fh_err):
        p.communicate()

        return {
            "out": fh_out.read(),
            "err": fh_err.read(),
            "code": p.returncode,
            "pid": p.pid,
            "args": p.args
        }
