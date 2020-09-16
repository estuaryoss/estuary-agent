<h1 align="center"><img src="./docs/images/banner_estuary.png" alt="Testing as a service with Docker"></h1>  

Support project: <a href="https://paypal.me/catalindinuta?locale.x=en_US"><img src="https://lh3.googleusercontent.com/Y2_nyEd0zJftXnlhQrWoweEvAy4RzbpDah_65JGQDKo9zCcBxHVpajYgXWFZcXdKS_o=s180-rw" height="40" width="40" align="center"></a>    

## Estuary agent
Estuary agent is a service that exposes your cli commands/app via REST API.

## Code quality
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/2b4052d9749348c49543fe6b830dc052)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=estuaryoss/estuary-agent&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/e993e853603af9dd0906/maintainability)](https://codeclimate.com/github/estuaryoss/estuary-agent/maintainability)

## Linux status
[![Build Status](https://travis-ci.org/estuaryoss/estuary-agent.svg?branch=master)](https://travis-ci.org/estuaryoss/estuary-agent)

## Windows status
[![CircleCI](https://circleci.com/gh/estuaryoss/estuary-agent.svg?style=svg)](https://circleci.com/gh/estuaryoss/estuary-agent)  

## Docker Hub
[alpine](https://hub.docker.com/r/estuaryoss/agent)  ![](https://img.shields.io/docker/pulls/estuaryoss/agent.svg)  
[centos](https://hub.docker.com/r/estuaryoss/agent-centos)  ![](https://img.shields.io/docker/pulls/estuaryoss/agent-centos.svg)

## Api docs
[4.0.8](https://app.swaggerhub.com/apis/dinuta/estuary-testrunner/4.0.8)

## Postman collection
[Postman](https://documenter.getpostman.com/view/2360061/SVYrrdGe?version=latest)

## Katacoda playground
[estuary-agent](https://katacoda.com/dinuta/scenarios/estuary-agent)

## General use cases:
- remote command executor
- exposing CLI app through REST API
- controlling the test automation framework (maven/python, etc)
- integration testing by controlling and configuring the SUT

## Testing use cases:
Some use cases are documented in [wiki](https://github.com/dinuta/estuary-agent/wiki)

## Service run
### Docker compose
    docker-compose up
    
### Docker run

    docker run  
    -d 
    -p 8080:8080
    estuaryoss/agent:<tag>
    
    
### Kubernetes
    kubectl apply -f k8sdeployment.yml
    
### Eureka registration
To have all your estuary-agent instances in a central location, Netflix Eureka is used. This means your client will discover
all services used for your test and then spread the tests across all.

Start Eureka server with docker:

    docker run -p 8080:8080 estuaryoss/netflix-eureka:1.9.25

Start your containers by specifying the full hostname or ip of the host machine on where your agent service resides.
Optionally you can define the WORKSPACE (default=/tmp)or PORT (default=8080).

    docker run \
    -e EUREKA_SERVER=http://10.10.15.30:8080/eureka/v2 -> the eureka server
    -e APP_IP_PORT=10.10.15.28:8081 -> the ip and port of the app
    -e WORKSPACE=/tmp/ -> optional;for multiplatform set it to your needs;default is /tmp/;E.g /workspace/
    -p 8081:8080
    estuaryoss/agent:<tag>

### Fluentd logging
Please consult [Fluentd](https://github.com/fluent/fluentd) for logging setup.  
Agent tags all logs in format ```estuary-agent.**```

Matcher example:  

``` xml
<match estuary*.**>
    @type stdout
</match>
```

Run example:

    docker run \
    -e FLUENTD_IP_PORT=10.10.15.28:24224
    -p 8080:8080
    estuaryoss/agent:<tag>

### Authentication
For auth set HTTP_AUTH_TOKEN env variable.  

Run example:

    docker run \
    -e HTTP_AUTH_TOKEN=mysecret
    -p 8080:8080
    estuaryoss/agent:<tag>

Then, access the Http Api. Call example:
  
    curl -i -H 'Token:mysecret' http:localhost:8080/about

## Environment variables injection
User defined environment variables will be stored in a 'virtual' environment. The extra env vars will be used by the process that executes system commands.  
There are two ways to inject user defined environment variables.    
-   call POST on **/env** endpoint. The body will contain the env vars in JSON format. E.g. {"FOO1":"BAR1"}  
-   create an **environment.properties** file with the extra env vars needed and place it in the same path as the JAR. Example in this repo.  

*! All environment variables described above can also be set using **environment.properties**.*

## Example output
curl -X POST -d 'ls -lrt' http://localhost:8080/command

```json
{
    "code": 1000,
    "message": "Success",
    "description": {
        "finished": true,
        "started": false,
        "startedat": "2020-08-15 19:38:16.138962",
        "finishedat": "2020-08-15 19:38:16.151067",
        "duration": 0.012,
        "pid": 2315,
        "id": "none",
        "commands": {
            "ls -lrt": {
                "status": "finished",
                "details": {
                    "out": "total 371436\n-rwxr-xr-x 1 dinuta qa  13258464 Jun 24 09:25 main-linux\ndrwxr-xr-x 4 dinuta qa        40 Jul  1 11:42 tmp\n-rw-r--r-- 1 dinuta qa  77707265 Jul 25 19:38 testrunner-linux.zip\n-rw------- 1 dinuta qa   4911271 Aug 14 10:00 nohup.out\n",
                    "err": "",
                    "code": 0,
                    "pid": 6803,
                    "args": [
                        "/bin/sh",
                        "-c",
                        "ls -lrt"
                    ]
                },
                "startedat": "2020-08-15 19:38:16.138970",
                "finishedat": "2020-08-15 19:38:16.150976",
                "duration": 0.012
            }
        }
    },
    "timestamp": "2020-08-15 19:38:16.151113",
    "path": "/command?",
    "name": "estuary-agent",
    "version": "4.0.8"
}
```

## Estuary stack
[Estuary deployer](https://github.com/estuaryoss/estuary-deployer)  
[Estuary agent](https://github.com/estuaryoss/estuary-agent)  
[Estuary discovery](https://github.com/estuaryoss/estuary-discovery)  
[Estuary viewer](https://github.com/estuaryoss/estuary-viewer)  

## Templating service
[Jinja2Docker](https://github.com/dinuta/jinja2docker) 
