#!/bin/bash

# Configure timezone and display current time
configure_timezone() {
    # Source the box_echo function
    source /app/scripts/box_echo.sh
    
    # Set TimeZone based on env variable
    # Print date time before 
    box_echo "Current date time: $(date)"
    box_echo "Setting TimeZone to ${TZ}"
    echo $TZ > /etc/timezone && \
        ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
        dpkg-reconfigure -f noninteractive tzdata > /dev/null 2>&1
    box_echo "Current date time after update: $(date)"
    box_echo "--------------------------------------------------------------------------";
}
