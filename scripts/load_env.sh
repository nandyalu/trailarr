#!/bin/bash

# Load the settings that Trailarr stored in a .env file.
#
# A variable already set in the environment has priority. For example, a
# variable set in `docker-compose.yml` keeps its value, and the stored value is
# used only when that variable is not set. This lets you correct a bad setting
# (URL_BASE, WEBUI_PASSWORD, ...) from your compose file when the WebUI is not
# usable.
load_env_file() {
    local env_file="$1"
    local line key value
    [ -f "$env_file" ] || return 0

    while IFS= read -r line || [ -n "$line" ]; do
        # Remove a carriage return, leading spaces and an 'export ' prefix.
        line="${line%$'\r'}"
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line#export }"

        # Skip empty lines, comments and lines that are not KEY=VALUE.
        case "$line" in
            ''|'#'*) continue ;;
            *=*) ;;
            *) continue ;;
        esac

        key="${line%%=*}"
        value="${line#*=}"

        # Skip a key that is not a valid variable name.
        if ! [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            continue
        fi

        # Remove the quotes that python-dotenv writes around a value.
        if [[ "$value" == \'*\' || "$value" == \"*\" ]]; then
            value="${value:1:${#value}-2}"
        fi

        # Keep the value that is already set in the environment.
        if [ -z "${!key+set}" ]; then
            export "$key=$value"
        fi
    done < "$env_file"
}
