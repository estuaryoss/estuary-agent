swagger_file_content = '''
"swagger": '2.0'
info:
  description: |
    Estuary agent which will run your shell commands via REST API
  version: "4.0.8"
  title: estuary-agent
  termsOfService: http://swagger.io/terms/
  contact:
    email: constantin.dinuta@gmail.com
  license:
    name: Apache 2.0
    url: http://www.apache.org/licenses/LICENSE-2.0.html
# host: localhost:8080
basePath: /
tags:
  - name: estuary-agent
    description: Estuary-agent runs shell commands and exposes CLI apps via pure REST API
    externalDocs:
      description: Find out more on github
      url: https://github.com/dinuta/estuary-agent
schemes:
  - http
paths:
  /env:
    get:
      tags:
        - estuary-agent
      summary: Print all environment variables
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      responses:
        200:
          description: List of the entire environment variables
          schema:
            $ref: "#/definitions/ApiResponse"
    post:
      tags:
        - estuary-agent
      summary: Set environment variables
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: EnvVars
        in: body
        description: List of env vars by key-value pair
        required: true
        schema:
          $ref: '#/definitions/envvar'
      responses:
        200:
          description: Set environment variables response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: Set environment variables failure
          schema:
            $ref: "#/definitions/ApiResponse"
  /env/{env_name}:
    get:
      tags:
        - estuary-agent
      summary: Gets the environment variable value from the environment
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: env_name
        in: path
        description: The name of the env var to get value from
        required: true
        type: string
      responses:
        200:
          description: Get env var value
          schema:
            $ref: "#/definitions/ApiResponse"
  /ping:
    get:
      tags:
        - estuary-agent
      summary: Ping endpoint which replies with pong
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      responses:
        200:
          description: Ping endpoint which replies with pong. Useful when checking the alive status of the service
          schema:
            $ref: "#/definitions/ApiResponse"
  /about:
    get:
      tags:
        - estuary-agent
      summary: Information about the application
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      responses:
        200:
          description: Prints the name and version of the application.
          schema:
            $ref: "#/definitions/ApiResponse"
  /render/{template}/{variables}:
    get:
      tags:
        - estuary-agent
      summary: Jinja2 render 
      description: Gets the rendered output from template and variable files
      produces:
        - application/json
        - text/plain
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: template
        in: path
        description: The template file
        required: true
        type: string
      - name: variables
        in: path
        description: The variables file
        required: true
        type: string
      responses:
        200:
          description: jinja2 templating response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: jinja2 templating failure
          schema:
            $ref: "#/definitions/ApiResponse"
    post:
      tags:
        - estuary-agent
      summary: jinja2 render where env vars can be inserted
      consumes:
        - application/json
        - application/x-www-form-urlencoded
      produces:
        - application/json
        - text/plain
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: template
        in: path
        description: Template file 
        required: true
        type: string
      - name: variables
        in: path
        description: Variables file
        required: true
        type: string
      - name: EnvVars
        in: body
        description: List of env vars by key-value pair
        required: false
        schema:
          $ref: '#/definitions/envvar'
      responses:
        200:
          description: jinja2 templating response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: jinja2 templating failure
          schema:
            $ref: "#/definitions/ApiResponse"
  /commanddetached/{id}:
    post:
      tags:
        - estuary-agent
      summary: Starts the commands in detached mode and sequentially
      consumes:
        - text/plain
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: id
        in: path
        description: Command detached id set by the user
        required: true
        type: string
      - name: test_file_content
        in: body
        description: List of commands to run one after the other. E.g. make/mvn/sh/npm
        required: true
        schema:
          $ref: '#/definitions/test_file_content'
      responses:
        200:
          description: commands start response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: commands start failure
          schema:
            $ref: "#/definitions/ApiResponse"
  /commanddetached:
    get:
      tags:
        - estuary-agent
      summary: Gets information about running detached commands, running processes, test status
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      responses:
        200:
          description: Get command detached info response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: Get command detached info failure
          schema:
            $ref: "#/definitions/ApiResponse"
    delete:
      tags:
        - estuary-agent
      summary: Stops all detached commands previously started
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      responses:
        200:
          description: command detached stop success
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: command detached stop failure
          schema:
            $ref: "#/definitions/ApiResponse"
  /file:
    put:
      tags:
        - estuary-agent
      summary: Uploads a file no mater the format. Binary or raw
      consumes:
        - application/json
        - application/x-www-form-urlencoded
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: content
        in: body
        description: The content of the file
        required: true
        schema:
          $ref: '#/definitions/filecontent'
      - in: header
        name: File-Path
        type: string
        required: true
      responses:
        200:
          description: The content of the file was uploaded successfully
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: Failure, the file content could not be uploaded
          schema:
            $ref: "#/definitions/ApiResponse"
    get:
      tags:
        - estuary-agent
      summary: Gets the content of the file
      consumes:
        - application/json
        - application/x-www-form-urlencoded
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: File-Path
        type: string
        in: header
        description: Target file path to get
        required: false
      responses:
        200:
          description: The content of the file in plain text, response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: Failure, the file content could not be read
          schema:
            $ref: "#/definitions/ApiResponse"
  /folder:
    get:
      tags:
        - estuary-agent
      summary: Gets the folder as zip archive. Useful to get test results folder
      consumes:
        - application/json
        - application/x-www-form-urlencoded
      produces:
        - application/zip
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: Folder-Path
        type: string
        in: header
        description: Target folder path to get as zip
        required: true
      responses:
        200:
          description: The content of the folder as zip archive
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: The content of the folder could not be obtained
          schema:
            $ref: "#/definitions/ApiResponse"
  /command:
    post:
      tags:
        - estuary-agent
      summary: Starts multiple commands in blocking mode, but executed sequentially. Set the client timeout at needed value.
      consumes:
        - text/plain
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: commands
        in: body
        description: Commands to run. E.g. ls -lrt
        required: true
        schema:
          $ref: '#/definitions/commands_content'
      responses:
        200:
          description: commands start response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: commands start failure
          schema:
            $ref: "#/definitions/ApiResponse"
  /commandparallel:
    post:
      tags:
        - estuary-agent
      summary: Starts multiple commands in blocking mode, but executed in parallel. Set the client timeout at needed value.
      consumes:
        - text/plain
      produces:
        - application/json
      parameters:
      - in: header
        name: Token
        type: string
        required: false
      - name: commands
        in: body
        description: Commands to run. E.g. ls -lrt
        required: true
        schema:
          $ref: '#/definitions/commands_content'
      responses:
        200:
          description: commands start response
          schema:
            $ref: "#/definitions/ApiResponse"
        404:
          description: commands start failure
          schema:
            $ref: "#/definitions/ApiResponse"  
definitions:
    ApiResponse:
      type: object
      properties:
        message:
          type: object
        description:
          type: "string"
        code:
          type: "string"
        time:
          type: "string"
          format: "date-time"
        name:
          type: "string"
        version:
          type: "string"
    envvar:
      type: object
      example: |
          {"DATABASE" : "mysql56", "IMAGE":"latest"}
    filecontent:
      type: object
      example: {"file" : "/home/automation/config.properties", "content" : "ip=10.0.0.1\nrequest_sec=100\nthreads=10\ntype=dual"}
    test_file_content:
      type: string
      minLength: 3
      example: |
        mvn test -Dtype=Prepare
        mvn test -Dtype=ExecuteTests
    commands_content:
      type: string
      minLength: 3
      example: |
        ls -lrt
        cat config.json
externalDocs:
  description: Find out more on github
  url: https://github.com/dinuta/estuary-agent
'''
