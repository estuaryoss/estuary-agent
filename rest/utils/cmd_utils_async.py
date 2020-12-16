import asyncio

from rest.environment.environment import EnvironmentSingleton


class CmdUtilsAsync:
    @staticmethod
    async def run_cmd_async(command):
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=EnvironmentSingleton.get_instance().get_env_and_virtual_env())

        return await CmdUtilsAsync.__get_subprocess_data(proc)

    @staticmethod
    async def __get_subprocess_data(proc):
        out, err = await proc.communicate()

        return {
            "code": proc.returncode,
            "out": out.decode("UTF-8", "replace"),
            "err": err.decode("UTF-8", "replace"),
            "pid": proc.pid,
            "args": "NA"
        }
