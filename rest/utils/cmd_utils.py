import subprocess

from rest.environment.environment import EnvironmentSingleton


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
    def run_cmd_shell_false(command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env=CmdUtils.__env.get_env_and_virtual_env())
        return CmdUtils.__get_subprocess_data(p)

    @staticmethod
    def __get_subprocess_data(p):
        lines_to_slice = 10000
        [out, err] = p.communicate()

        return {
            "out": "\n".join(out.decode("UTF-8", "replace").split("\n")[-lines_to_slice:]),
            "err": "\n".join(err.decode("UTF-8", "replace").split("\n")[-lines_to_slice:]),
            "code": p.returncode,
            "pid": p.pid,
            "args": p.args
        }
