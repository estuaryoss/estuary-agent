import py_eureka_client.eureka_client as eureka_client

from about import properties


class Eureka:

    def __init__(self, host):
        self.host = host

    def register_app(self, app_ip_port):
        app_ip = app_ip_port.split(":")[0]
        app_port = int(app_ip_port.split(":")[1].split("/")[0])
        pre_url = "/".join(app_ip_port.split(":")[1].split("/")[1:])
        home_page_url = ""
        deployment_id = ""
        if pre_url:
            home_page_url = pre_url + "/"
            deployment_id = app_ip_port.split(":")[1].split("/")[3]
        print("Starting eureka register on eureka server " + self.host + ". \n")
        print(properties['name'] + " registering with: ip=" + app_ip + ", port=" + str(app_port) + ". \n")
        eureka_client.init(eureka_server=self.host,
                           app_name=f"{properties['name']}{deployment_id}",
                           instance_port=app_port,
                           instance_ip=app_ip,
                           health_check_url=f"{pre_url}/ping",
                           home_page_url=f"{home_page_url}",
                           status_page_url=f"{pre_url}/ping"
                           )
