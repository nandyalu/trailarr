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


!!! tip "Enable Debug Logging for Detailed Troubleshooting"
    When actively trying to diagnose a complex issue, temporarily setting the application's [Log Level to `Debug`](../settings/general-settings/index.md#log-level) in the General Settings can provide much more detailed operational information. Remember to set it back to a less verbose level (like `Info` or `Warning`) afterwards to prevent excessive log file growth and performance impact.