from tests.rest_win.api_code_constants import ApiCodeConstants


class ErrorCodes:
    HTTP_CODE = {
        ApiCodeConstants.SUCCESS: "Success",
        ApiCodeConstants.JINJA2_RENDER_FAILURE: "Jinja2 render failed",
        ApiCodeConstants.GET_FILE_FAILURE: "Getting file or folder from the estuary agent service container failed",
        ApiCodeConstants.TEST_START_FAILURE: "Starting test id %s failed",
        ApiCodeConstants.TEST_STOP_FAILURE: "Stopping running test %s failed",
        ApiCodeConstants.GET_FILE_FAILURE_IS_DIR: "Getting %s from the container %s failed. It is a directory, not a file.",
        ApiCodeConstants.GET_ENV_VAR_FAILURE: "Getting env var %s from the container failed.",
        ApiCodeConstants.MISSING_PARAMETER_POST: "Body parameter \"%s\" sent in request missing. Please include parameter. E.g. {\"parameter\": \"value\"}",
        ApiCodeConstants.GET_TEST_INFO_FAILURE: "Failed to get test info.",
        ApiCodeConstants.FOLDER_ZIP_FAILURE: "Failed to zip folder %s.",
        ApiCodeConstants.EMPTY_REQUEST_BODY_PROVIDED: "Empty request body provided.",
        ApiCodeConstants.UPLOAD_TEST_CONFIG_FAILURE: "Failed to upload test configuration.",
        ApiCodeConstants.HTTP_HEADER_NOT_PROVIDED: "Http header value not provided: '%s'",
        ApiCodeConstants.COMMAND_EXEC_FAILURE: "Starting command(s) failed",
        ApiCodeConstants.EXEC_COMMAND_NOT_ALLOWED: "'rm' commands are filtered. Command '%s' was not executed.",
        ApiCodeConstants.UNAUTHORIZED: "Unauthorized",
        ApiCodeConstants.SET_ENV_VAR_FAILURE: "Failed to set env vars \"%s\"",
        ApiCodeConstants.INVALID_JSON_PAYLOAD: "Invalid json body \"%s\"",
    }
