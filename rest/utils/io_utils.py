import errno
import json
import os
import shutil
from pathlib import Path


class IOUtils:

    @staticmethod
    def create_dir(path, permissions=0o755):
        if not os.path.exists(path):
            os.makedirs(path, permissions)

    @staticmethod
    def write_to_file(file, content=""):
        with open(file, 'w') as f:
            f.write(content)

    @staticmethod
    def create_file(file):
        file = Path(file)
        if not file.exists():
            IOUtils.write_to_file(file, "")

    @staticmethod
    def read_last_line(file):
        with open(file, 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            return last_line

    @staticmethod
    def append_to_file(file, content=""):
        with open(file, 'a') as f:
            f.write(content + "\n")

    @staticmethod
    def write_to_file_binary(file, content=""):
        with open(file, 'wb') as f:
            f.write(content)

    @staticmethod
    def write_to_file_dict(file, content):
        with open(file, 'w') as f:
            f.write(json.dumps(content, indent=4))

    @staticmethod
    def read_dict_from_file(file):
        try:
            with open(file, 'r') as f:
                return json.loads(f.read())
        except Exception as e:
            raise e

    @staticmethod
    def get_filtered_list_regex(input_list, regex):
        filtered_list = []
        for elem in input_list:
            if not regex.search(elem) and elem.strip() != "":
                filtered_list.append(elem.strip())
        return filtered_list

    @staticmethod
    def delete_file(file):
        file_path = Path(file)
        if file_path.is_file():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"Failed to delete file {file}: {e.__str__()}")

    @staticmethod
    def delete_files(files):
        for file in files:
            IOUtils.delete_file(file)

    @staticmethod
    def read_file(file):
        file_path = Path(file)
        if not file_path.is_file():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
        with open(file, 'r') as f:
            return f.read()

    @staticmethod
    def read_file_byte_array(file):
        file_path = Path(file)
        if not file_path.is_file():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
        with open(file, 'rb') as f:
            return f.read()

    @staticmethod
    def zip_file(name, path):
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)
        shutil.make_archive(f"/tmp/{name}", 'zip', f"{path}")

    @staticmethod
    def create_files(files):
        for file in files:
            IOUtils.create_file(file)

    @classmethod
    def does_file_exist(cls, path):
        return Path(path).exists()
