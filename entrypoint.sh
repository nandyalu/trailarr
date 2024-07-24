#!/bin/sh

# THIS SCRIPT WILL BE RUN AS THE ROOT USER IN THE CONTAINER BEFOR APP STARTS

# Set TimeZone based on env variable
# Print date time before 
echo "Current date time: $(date)"
echo "Setting TimeZone to ${TZ}"
echo $TZ > /etc/timezone && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
echo "Current date time after tzdate: $(date)"

# Create data folder for storing database and other config files
echo "Creating '/data' folder for storing database and other config files"
mkdir -p /data/logs && chmod -R 755 /data
chmod -R 755 /app/assets

# Change the owner of /data to the non-root user
echo "Changing the owner of data directory to the appuser"
chown -R appuser:appuser /data

# Switch to the non-root user and execute the command
echo "Switching to appuser and starting the application"
exec gosu appuser bash -c /app/start.sh

# DO NOT ADD ANY OTHER COMMANDS HERE! THEY WON'T BE EXECUTED!
# Instead add them in the start.sh script
