#!/bin/bash

# Display startup banner and initial configuration information
display_startup_banner() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh

    # Print 'TRAILARR' as ASCII Art 
    # Generated using https://www.asciiart.eu/text-to-ascii-art
    # Font: Banner3, Horizontal Layout: Wide, Vertical Layout: Wide, Width: 80
    # Border: PlusBox v2, V. Padding: 1, H. Padding: 3
    # Whitespace break: enabled, Trim Whitespace: enabled, Replace Whitespace: disabled
    echo "+==============================================================================+";
    echo "|                                                                              |";
    echo "|   ######## ########     ###    #### ##          ###    ########  ########    |";
    echo "|      ##    ##     ##   ## ##    ##  ##         ## ##   ##     ## ##     ##   |";
    echo "|      ##    ##     ##  ##   ##   ##  ##        ##   ##  ##     ## ##     ##   |";
    echo "|      ##    ########  ##     ##  ##  ##       ##     ## ########  ########    |";
    echo "|      ##    ##   ##   #########  ##  ##       ######### ##   ##   ##   ##     |";
    echo "|      ##    ##    ##  ##     ##  ##  ##       ##     ## ##    ##  ##    ##    |";
    echo "|      ##    ##     ## ##     ## #### ######## ##     ## ##     ## ##     ##   |";
    echo "|                                                                              |";
    echo "+==============================================================================+";
    box_echo "";
    box_echo "               App Version: ${APP_VERSION}";
    box_echo "";
    box_echo "--------------------------------------------------------------------------";
    box_echo "Starting Trailarr container with the following configuration:"
    box_echo "APP_DATA_DIR: ${APP_DATA_DIR}"
    box_echo "APP_PORT: ${APP_PORT}"
    box_echo "PUID: ${PUID}"
    box_echo "PGID: ${PGID}"
    box_echo "TZ: ${TZ}"
    box_echo "--------------------------------------------------------------------------";
}
