import requests


class RestApi:

    def __init__(self, connection):
        """ REST API Service usually used for self calls """
        self.conn = connection
        self.__timeout = 5 if not self.conn.get('timeout') else self.conn.get('timeout')

    def post(self, data, headers):
        url_format = f"{self.conn.get('protocol')}://{self.conn.get('ip')}:{self.conn.get('port')}{self.conn.get('endpoint')}"
        return requests.post(url_format, headers=headers, data=data, timeout=self.__timeout,
                             verify=self.conn.get('cert'))

    def put(self, data, headers):
        url_format = f"{self.conn.get('protocol')}://{self.conn.get('ip')}:{self.conn.get('port')}{self.conn.get('endpoint')}"
        return requests.put(url_format, headers=headers, data=data, timeout=self.__timeout,
                            verify=self.conn.get('cert'))

    def delete(self, headers):
        url_format = f"{self.conn.get('protocol')}://{self.conn.get('ip')}:{self.conn.get('port')}{self.conn.get('endpoint')}"
        return requests.delete(url_format, headers=headers, timeout=self.__timeout, verify=self.conn.get('cert'))

    def get(self, headers):
        url_format = f"{self.conn.get('protocol')}://{self.conn.get('ip')}:{self.conn.get('port')}{self.conn.get('endpoint')}"
        return requests.get(url_format, headers=headers, timeout=self.__timeout, verify=self.conn.get('cert'))
