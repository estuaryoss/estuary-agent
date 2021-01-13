swagger_file_content = '''
swagger: '2.0'
info:
  description: Estuary agent will run your shell commands via REST API
  version: 4.4.0
  title: estuary-agent
  contact:
    name: Catalin Dinuta
    url: 'https://github.com/dinuta'
    email: constantin.dinuta@gmail.com
  license:
    name: Apache 2.0
    url: 'http://www.apache.org/licenses/LICENSE-2.0.html'
host: 'localhost:8080'
basePath: /
tags:
  - name: estuary-agent
    description: root
paths:
  /about:
    get:
      tags:
        - estuary-agent
      summary: Information about the application
      operationId: aboutGet
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Prints the name and version of the application.
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
  /command:
    post:
      tags:
        - estuary-agent
      summary: Starts multiple commands in blocking mode sequentially. Set the client timeout at needed value.
      operationId: commandPost_1
      consumes:
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
      parameters:
        - in: body
          name: commands
          description: Commands to run. E.g. ls -lrt
          required: true
          schema:
            type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Commands start success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Commands start failure
          schema:
            $ref: '#/definitions/ApiResponse'
  /commanddetached:
    get:
      tags:
        - estuary-agent
      summary: Gets information about the last command started in detached mode
      operationId: commandDetachedGet
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Get command detached info success
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Get command detached info failure
          schema:
            $ref: '#/definitions/ApiResponse'
    delete:
      tags:
        - estuary-agent
      summary: Stops all commands that were previously started in detached mode
      operationId: commandDetachedDelete
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: command detached stop success
          schema:
            $ref: '#/definitions/ApiResponse'
        '204':
          description: No Content
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '500':
          description: command detached stop failure
          schema:
            $ref: '#/definitions/ApiResponse'
  '/commanddetached/{id}':
    get:
      tags:
        - estuary-agent
      summary: Gets information about the command identified by id started in detached mode
      operationId: commandDetachedIdGet
      produces:
        - application/json
      parameters:
        - name: id
          in: path
          description: Command detached id set by the user
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Get command detached info success
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Get command detached info failure
          schema:
            $ref: '#/definitions/ApiResponse'
    post:
      tags:
        - estuary-agent
      summary: Starts the shell commands in detached mode and sequentially
      operationId: commandDetachedIdPost
      consumes:
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
      parameters:
        - in: body
          name: commandContent
          description: List of commands to run one after the other. E.g. make/mvn/sh/npm
          required: true
          schema:
            type: string
        - name: id
          in: path
          description: Command detached id set by the user
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Commands start success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Commands start failure
          schema:
            $ref: '#/definitions/ApiResponse'
    delete:
      tags:
        - estuary-agent
      summary: Deletes the associated processes of the shell commands in detached mode
      operationId: commandDetachedIdDelete
      produces:
        - application/json
      parameters:
        - name: id
          in: path
          description: Command detached id set by the user
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Command delete success
          schema:
            $ref: '#/definitions/ApiResponse'
        '204':
          description: No Content
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '500':
          description: Command delete failure
          schema:
            $ref: '#/definitions/ApiResponse'
  '/commanddetachedyaml/{id}':
    post:
      tags:
        - estuary-agent
      summary: Starts the commands in detached mode and sequentially. The commands are described by yaml.
      operationId: commandDetachedIdPostYaml
      consumes:
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
      parameters:
        - in: body
          name: commandContent
          description: List of commands to run one after the other in yaml format.
          required: true
          schema:
            type: string
        - name: id
          in: path
          description: Command detached id set by the user
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Commands start success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Commands start failure
          schema:
            $ref: '#/definitions/ApiResponse'
  /commandparallel:
    post:
      tags:
        - estuary-agent
      summary: Starts multiple commands in blocking mode parallel. Set the client timeout at needed value.
      operationId: commandPost_2
      consumes:
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
      parameters:
        - in: body
          name: commands
          description: Commands to run. E.g. ls -lrt
          required: true
          schema:
            type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: commands start success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: commands start failure
          schema:
            $ref: '#/definitions/ApiResponse'
  /commandyaml:
    post:
      tags:
        - estuary-agent
      summary: Starts multiple commands in blocking mode sequentially. The commands are described in yaml format. Set the client timeout at needed value.
      operationId: commandPost
      consumes:
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
      parameters:
        - in: body
          name: commands
          description: Commands to run in yaml format
          required: true
          schema:
            type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Commands start success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Commands start failure
          schema:
            $ref: '#/definitions/ApiResponse'
  /env:
    get:
      tags:
        - estuary-agent
      summary: Print all environment variables
      operationId: envGet
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: List of the entire environment variables
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
    post:
      tags:
        - estuary-agent
      summary: Set environment variables
      operationId: envPost
      consumes:
        - application/json
      produces:
        - application/json
      parameters:
        - in: body
          name: envVars
          description: List of env vars by key-value pair in JSON format
          required: true
          schema:
            type: string
        - name: Token
          in: header
          description: Authentication Token
          required: false
          type: string
      responses:
        '200':
          description: Set environment variables success
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Set environment variables failure
          schema:
            $ref: '#/definitions/ApiResponse'
    delete:
      tags:
        - estuary-agent
      summary: Deletes the custom defined env vars contained in the virtual environment
      operationId: envDelete
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: 'Deletes the entire virtual env vars, but keeping system env vars.'
          schema:
            $ref: '#/definitions/ApiResponse'
        '204':
          description: No Content
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
  '/env/{env_name}':
    get:
      tags:
        - estuary-agent
      summary: Gets the environment variable value from the environment
      operationId: envEnvNameGet
      produces:
        - application/json
      parameters:
        - name: env_name
          in: path
          description: The name of the env var to get value from
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Get env var success
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: Get env var failure
          schema:
            $ref: '#/definitions/ApiResponse'
  /file:
    get:
      tags:
        - estuary-agent
      summary: Gets the content of the file
      operationId: fileGet
      consumes:
        - application/octet-stream
        - text/plain
      produces:
        - application/json
        - application/zip
      parameters:
        - name: File-Path
          in: header
          description: Target file path to get
          required: false
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: 'The content of the file in plain text, success'
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: 'Failure, the file content could not be read'
          schema:
            $ref: '#/definitions/ApiResponse'
    post:
      tags:
        - estuary-agent
      summary: Uploads a file no mater the format. Binary or raw
      operationId: filePost
      consumes:
        - application/octet-stream
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
        - text/plain
      parameters:
        - in: body
          name: content
          description: The content of the file
          required: false
          schema:
            type: string
            format: byte
        - name: File-Path
          in: header
          description: File-Path
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: The content of the file was uploaded successfully
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: 'Failure, the file content could not be uploaded'
          schema:
            $ref: '#/definitions/ApiResponse'
    put:
      tags:
        - estuary-agent
      summary: Uploads a file no mater the format. Binary or raw
      operationId: filePut
      consumes:
        - application/octet-stream
        - application/json
        - application/x-www-form-urlencoded
        - text/plain
      produces:
        - application/json
        - text/plain
      parameters:
        - in: body
          name: content
          description: The content of the file
          required: false
          schema:
            type: string
            format: byte
        - name: File-Path
          in: header
          description: File-Path
          required: true
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: The content of the file was uploaded successfully
          schema:
            $ref: '#/definitions/ApiResponse'
        '201':
          description: Created
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: 'Failure, the file content could not be uploaded'
          schema:
            $ref: '#/definitions/ApiResponse'
  /folder:
    get:
      tags:
        - estuary-agent
      summary: Gets the folder as zip archive. Useful to get test results folder
      operationId: folderGet
      produces:
        - application/json
        - application/zip
      parameters:
        - name: Folder-Path
          in: header
          description: Target folder path to get as zip
          required: false
          type: string
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: The content of the folder as zip archive
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
        '500':
          description: The content of the folder could not be obtained
          schema:
            $ref: '#/definitions/ApiResponse'
  /ping:
    get:
      tags:
        - estuary-agent
      summary: Ping endpoint which replies with pong
      operationId: pingGet
      produces:
        - application/json
      parameters:
        - name: Token
          in: header
          description: Token
          required: false
          type: string
      responses:
        '200':
          description: Ping endpoint which replies with pong. Useful when checking the alive status of the service
          schema:
            $ref: '#/definitions/ApiResponse'
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '404':
          description: Not Found
definitions:
  ApiResponse:
    type: object
    properties:
      code:
        type: integer
        format: int32
      description:
        type: object
      message:
        type: string
      name:
        type: string
      path:
        type: string
      timestamp:
        type: string
      version:
        type: string
    title: ApiResponse
  ApiResponseCommandDescription:
    type: object
    properties:
      code:
        type: integer
        format: int32
      description:
        $ref: '#/definitions/CommandDescription'
      message:
        type: string
      name:
        type: string
      path:
        type: string
      timestamp:
        type: string
      version:
        type: string
    title: ApiResponseCommandDescription
  CommandDescription:
    type: object
    properties:
      commands:
        type: object
        additionalProperties:
          $ref: '#/definitions/CommandStatus'
      duration:
        type: number
        format: float
      finished:
        type: boolean
      finishedat:
        type: string
      id:
        type: string
      pid:
        type: integer
        format: int64
      processes:
        type: array
        items:
          $ref: '#/definitions/ProcessInfo'
      started:
        type: boolean
      startedat:
        type: string
    title: CommandDescription
  CommandDetails:
    type: object
    properties:
      args:
        type: array
        items:
          type: string
      code:
        type: integer
        format: int64
      err:
        type: string
      out:
        type: string
      pid:
        type: integer
        format: int64
    title: CommandDetails
  CommandStatus:
    type: object
    properties:
      details:
        $ref: '#/definitions/CommandDetails'
      duration:
        type: number
        format: float
      finishedat:
        type: string
        example: 'yyyy-MM-dd HH:mm:ss.SSSSSS'
      startedat:
        type: string
        example: 'yyyy-MM-dd HH:mm:ss.SSSSSS'
      status:
        type: string
    title: CommandStatus
  ProcessHandle:
    type: object
    properties:
      alive:
        type: boolean
    title: ProcessHandle
  ProcessInfo:
    type: object
    properties:
      arguments:
        type: array
        items:
          type: string
      children:
        type: array
        items:
          $ref: '#/definitions/ProcessHandle'
      name:
        type: string
      parent:
        type: integer
        format: int64
      pid:
        type: integer
        format: int64
      status:
        type: string
      username:
        type: string
    title: ProcessInfo
'''
