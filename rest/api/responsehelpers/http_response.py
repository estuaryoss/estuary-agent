import datetime

from flask import request

from about import properties


class HttpResponse:

    @staticmethod
    def response(code, message, description):
        return {
            "code": code,
            "message": message,
            "description": description,
            "path": request.full_path,
            "timestamp": str(datetime.datetime.now()),
            "name": properties["name"],
            "version": properties["version"]
        }
