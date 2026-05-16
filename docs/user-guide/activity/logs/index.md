# Logs

This page displays the `Trailarr` application logs. 

- You can filter them using the `Logs Type` dropdown and text field at the top.

    !!! tip "Logs Type"
        Selecting a Logs Type shows all logs for selected type and above.

        Log Types are as following (lowest to highest):

        - Trace
        - Debug
        - Info
        - Warning
        - Error
        - Exception
        - Critical

        For example, if you select `Info`, then all logs of types `Info`, `Warning`, `Error`, `Exception` and `Critical` are shown.

- Refresh button will fetch new logs from server.
- Download button will download the logs file to your computer.
- Logs are shown in Descending order - most recent logs are shown first!


!!! info "Logs & Retention"
    Trailarr saves all logs in its database starting from version `v0.4.3` and cleans up logs older than 30 days automatically.


!!! tip "Enable Debug Logging for Detailed Troubleshooting"
    When actively trying to diagnose a complex issue, you might find it helpful to change the logs filter to `Debug`. This will provide more granular details about the application's operations, which can be invaluable for pinpointing problems.