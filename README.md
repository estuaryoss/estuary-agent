<h1 align="center"><img src="./docs/images/banner_estuary.png" alt="Testing as a service with Docker"></h1>  

Support project: <a href="https://paypal.me/catalindinuta?locale.x=en_US"><img src="https://pbs.twimg.com/profile_images/1145724063106519040/b1L98qh9_400x400.jpg" height="40" width="40" align="center"></a>    

# Testing as a Service

## Estuary testrunner
Estuary test runner service. This service runs your tests.

## Coverage and code quality
[![Coverage Status](https://coveralls.io/repos/github/dinuta/estuary-testrunner/badge.svg?branch=master)](https://coveralls.io/github/dinuta/estuary-testrunner?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/7aeb5e03e5ff4acb9ffc4f1b2e705596)](https://www.codacy.com/manual/dinuta/estuary-testrunner?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dinuta/estuary-testrunner&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/cdce1567b4fa5a77da98/maintainability)](https://codeclimate.com/github/dinuta/estuary-testrunner/maintainability)

## Linux status
[![Build Status](https://travis-ci.org/dinuta/estuary-testrunner.svg?branch=master)](https://travis-ci.org/dinuta/estuary-testrunner)

## Windows status
[![CircleCI](https://circleci.com/gh/dinuta/estuary-testrunner.svg?style=svg)](https://circleci.com/gh/dinuta/estuary-testrunner)  

## Docker Hub
[alpine](https://hub.docker.com/r/dinutac/estuary-testrunner)  ![](https://img.shields.io/docker/pulls/dinutac/estuary-testrunner.svg)  
[centos](https://hub.docker.com/r/dinutac/estuary-testrunner-centos)  ![](https://img.shields.io/docker/pulls/dinutac/estuary-testrunner-centos.svg)

## Api docs
[4.0.1](https://app.swaggerhub.com/apis/dinuta/estuary-testrunner/4.0.1)

## Postman collection
[Postman](https://documenter.getpostman.com/view/2360061/SVYrrdGe)

## Use cases:
-  remote command executor through cli version. Any command can be executed, except "rm" like commands
-  testing: test execution, getting results ...

## Container support
-  mvn & java jdk  
-  make  
-  npm
-  other: you can use this image as base and install on top your dependencies 

## TestRunner service usage
1. use the service embedded in this container and mount your testing framework
2. build your absolute custom framework image and integrate this service as a self-contained application service (cli). Read [doc](https://github.com/dinuta/estuary-testrunner/wiki).

Use cases:
1. estuary-testrunner vs an external SUT / dockerized SUT
2. estuary-testrunner used inside docker-compose with estuary-deployer

## Service run
### Docker compose
    docker-compose up
    
### Docker run

    docker run  
    -d 
    -p 8080:8080
    dinutac/estuary-testrunner:<tag>
    
    
### Kubernetes
    kubectl apply -f k8sdeployment.yml
    
### Eureka registration
To have all your testrunner instances in a central location we use netflix eureka. This means your client will discover
all services used for your test and then spread the tests across all.

Start Eureka server with docker:

    docker run -p 8080:8080 netflixoss/eureka:1.3.1
    or
    docker run -p 8080:8080 dinutac/netflixoss-eureka:1.9.15

Start your containers by specifying the full hostname or ip of the host machine on where your testrunner service resides.
Optionally you can define the WORKSPACE (default=/tmp)or PORT (default=8080).

    docker run \
    -e EUREKA_SERVER=http://10.10.15.28:8080/eureka/v2 -> the eureka server
    -e APP_IP_PORT=10.10.15.28:8081 -> the ip and port of the app
    -e WORKSPACE=/tmp/ -> optional;for multiplatform set it to your needs;default is /tmp/;E.g /workspace/
    -p 8080:8080
    dinutac/estuary-testrunner:<tag>

### Fluentd logging
Please consult [Fluentd](https://github.com/fluent/fluentd) for logging setup.  
Estuary-testrunner tags all logs in format ```estuary-testrunner.**```

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
    dinutac/estuary-testrunner:<tag>

### Authentication
For auth set HTTP_AUTH_TOKEN env variable.  

Run example:

    docker run \
    -e HTTP_AUTH_TOKEN=mysecret
    -p 8080:8080
    dinutac/estuary-testrunner:<tag>

Then, access the Http Api. Call example:
  
    curl -i -H 'Token:mysecret' http:localhost:8080/about

## Estuary stack
[Estuary deployer](https://github.com/dinuta/estuary-deployer)  
[Estuary testrunner](https://github.com/dinuta/estuary-testrunner)  
[Estuary discovery](https://github.com/dinuta/estuary-discovery)  
[Estuary viewer](https://github.com/dinuta/estuary-viewer)  

## Templating service
[Jinja2Docker](https://github.com/dinuta/jinja2docker) 
