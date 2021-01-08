from rest.api.constants.api_code_constants import ApiCode


class ErrorMessage:
    HTTP_CODE = {
        ApiCode.SUCCESS.value: "Success",
        ApiCode.JINJA2_RENDER_FAILURE.value: "Jinja2 render failed",
        ApiCode.GET_FILE_FAILURE.value: "Getting file %s from the estuary agent service failed",
        ApiCode.COMMAND_DETACHED_START_FAILURE.value: "Starting detached command with id %s failed",
        ApiCode.COMMAND_DETACHED_STOP_FAILURE.value: "Stopping running detached command failed",
        ApiCode.GET_FILE_FAILURE_IS_DIR.value: "Getting %s file failed. It is a directory, not a file.",
        ApiCode.GET_ENV_VAR_FAILURE.value: "Getting env var %s from the agent service failed.",
        ApiCode.MISSING_PARAMETER_POST.value: "Body parameter \"%s\" sent in request missing. Please include "
                                                 "parameter. E.g. {\"parameter\": \"value\"}",
        ApiCode.GET_COMMAND_DETACHED_INFO_FAILURE.value: "Failed to get detached command info.",
        ApiCode.FOLDER_ZIP_FAILURE.value: "Failed to zip folder %s.",
        ApiCode.EMPTY_REQUEST_BODY_PROVIDED.value: "Empty request body provided.",
        ApiCode.UPLOAD_FILE_FAILURE.value: "Failed to upload file.",
        ApiCode.HTTP_HEADER_NOT_PROVIDED.value: "Http header value not provided: '%s'",
        ApiCode.COMMAND_EXEC_FAILURE.value: "Starting command(s) failed",
        ApiCode.UNAUTHORIZED.value: "Unauthorized",
        ApiCode.SET_ENV_VAR_FAILURE.value: "Failed to set env vars \"%s\"",
        ApiCode.INVALID_JSON_PAYLOAD.value: "Invalid json body \"%s\"",
        ApiCode.INVALID_YAML_CONFIG.value: "Invalid yaml config",
    }
