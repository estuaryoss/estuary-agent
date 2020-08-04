import py_eureka_client.eureka_client as eureka_client


class EurekaClient:

    def __init__(self, host):
        self.host = host

    def get_apps(self):
        apps_list = []
        print("Getting apps from eureka server " + self.host + ". \n")
        for app in eureka_client.get_applications(eureka_server=self.host).applications:
            for instance in app.up_instances:
                # print(instance.app)
                apps_list.append(instance.hostName)
        return apps_list


if __name__ == '__main__':
    # step 1 - get all services registed in eureka
    up_services = EurekaClient("http://10.133.14.238:8080/eureka/v2").get_apps()
    print(up_services)

    # step 2 - spread the tests across all services obtained at step 2. Use multi thread
    # if using external SUT / dockerized SUT instruct each agent where to hit requests
    # can be used in docker-compose with estuary-deployer. TODO
    # TODO
