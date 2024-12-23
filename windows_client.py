# # import win32evtlog
# # import win32evtlogutil
# # import win32security
# # import csv

# # def read_logs(computer=None, log_type="Application"):
# #     """
# #     Read logs from a specific event log type.

# #     Args:
# #         computer (str): Target computer name, None for local logs.
# #         log_type (str): The log type to read (e.g., Application, System, Security).

# #     Returns:
# #         list: List of log entries.
# #     """
# #     logs = []
# #     handle = None
# #     try:
# #         print(f"Opening log type: {log_type}")
# #         # Open the event log
# #         handle = win32evtlog.OpenEventLog(computer, log_type)
# #         if not handle:
# #             print(f"Failed to open log type: {log_type}")
# #             return logs

# #         flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

# #         while True:
# #             try:
# #                 events = win32evtlog.ReadEventLog(handle, flags, 0)
# #                 if not events:
# #                     break  # Exit loop when no more logs are available

# #                 for event in events:
# #                     try:
# #                         # Format the message and user information
# #                         msg = win32evtlogutil.SafeFormatMessage(event, log_type)
# #                         sid_desc = None
# #                         if event.Sid:
# #                             try:
# #                                 domain, user, _ = win32security.LookupAccountSid(computer, event.Sid)
# #                                 sid_desc = f"{domain}/{user}"
# #                             except win32security.error:
# #                                 sid_desc = "Unknown User"

# #                         log_entry = {
# #                             "LogType": log_type,
# #                             "SourceName": event.SourceName,
# #                             "TimeGenerated": event.TimeGenerated.Format(),
# #                             "EventID": event.EventID,
# #                             "EventType": event.EventType,
# #                             "Message": msg,
# #                             "User": sid_desc,
# #                         }
# #                         logs.append(log_entry)
# #                     except Exception as e:
# #                         print(f"Error processing event: {e}")
# #             except Exception as e:
# #                 print(f"Error reading logs from {log_type}: {e}")
# #                 break  # Exit loop on persistent errors
# #     except Exception as e:
# #         print(f"Error opening log {log_type}: {e}")
# #     finally:
# #         if handle:
# #             try:
# #                 win32evtlog.CloseEventLog(handle)
# #             except Exception as e:
# #                 print(f"Error closing log handle for {log_type}: {e}")
# #     return logs

# # def save_logs_to_csv(logs, output_file):
# #     """
# #     Save logs to a CSV file.

# #     Args:
# #         logs (list): List of log entries.
# #         output_file (str): Output CSV file name.
# #     """
# #     try:
# #         with open(output_file, mode="w", newline="", encoding="utf-8") as file:
# #             fieldnames = ["LogType", "SourceName", "TimeGenerated", "EventID", "EventType", "Message", "User"]
# #             writer = csv.DictWriter(file, fieldnames=fieldnames)
# #             writer.writeheader()
# #             writer.writerows(logs)
# #         print(f"Logs successfully saved to '{output_file}'. Total logs: {len(logs)}")
# #     except Exception as e:
# #         print(f"Error saving logs to CSV: {e}")

# # def main():
# #     # Define the log sources
# #     log_types = ["Application", "System", "Security"]
# #     computer = None  # Set to target computer name or None for local logs

# #     print("Starting log collection...")
# #     for log_type in log_types:
# #         logs = read_logs(computer, log_type)
# #         if logs:
# #             output_file = f"{log_type}_logs.csv"
# #             save_logs_to_csv(logs, output_file)
# #         else:
# #             print(f"No logs collected for log type: {log_type}")

# # if __name__ == "__main__":
# #     try:
# #         main()
# #     except KeyboardInterrupt:
# #         print("\nScript stopped.")

import win32evtlog
import win32evtlogutil
import win32security
import socket
import json

# Splunk Server Configuration
SPLUNK_SERVER_IP = "localhost"  # Replace with your Splunk server's IP
SPLUNK_SERVER_PORT = 9000  # Replace with your configured TCP input port

def send_to_splunk(log_entry):
    """
    Send a log entry to the Splunk server via TCP.

    Args:
        log_entry (dict): Log entry to send.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SPLUNK_SERVER_IP, SPLUNK_SERVER_PORT))
            log_data = json.dumps(log_entry)  # Convert log entry to JSON format
            sock.sendall(log_data.encode('utf-8'))
        print(f"Successfully sent log to Splunk: {log_entry}")
    except Exception as e:
        print(f"Error sending log to Splunk: {e}")

def read_logs(computer=None, log_type="Application"):
    """
    Read logs from a specific event log type.

    Args:
        computer (str): Target computer name, None for local logs.
        log_type (str): The log type to read (e.g., Application, System, Security).

    Returns:
        list: List of log entries.
    """
    logs = []
    handle = None
    try:
        print(f"Opening log type: {log_type}")
        # Open the event log
        handle = win32evtlog.OpenEventLog(computer, log_type)
        if not handle:
            print(f"Failed to open log type: {log_type}")
            return logs

        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

        while True:
            try:
                events = win32evtlog.ReadEventLog(handle, flags, 0)
                if not events:
                    break  # Exit loop when no more logs are available

                for event in events:
                    try:
                        # Format the message and user information
                        msg = win32evtlogutil.SafeFormatMessage(event, log_type)
                        sid_desc = None
                        if event.Sid:
                            try:
                                domain, user, _ = win32security.LookupAccountSid(computer, event.Sid)
                                sid_desc = f"{domain}/{user}"
                            except win32security.error:
                                sid_desc = "Unknown User"

                        log_entry = {
                            "LogType": log_type,
                            "SourceName": event.SourceName,
                            "TimeGenerated": event.TimeGenerated.Format(),
                            "EventID": event.EventID,
                            "EventType": event.EventType,
                            "Message": msg,
                            "User": sid_desc,
                        }
                        logs.append(log_entry)
                        send_to_splunk(log_entry)  # Send each log entry to Splunk
                    except Exception as e:
                        print(f"Error processing event: {e}")
            except Exception as e:
                print(f"Error reading logs from {log_type}: {e}")
                break  # Exit loop on persistent errors
    except Exception as e:
        print(f"Error opening log {log_type}: {e}")
    finally:
        if handle:
            try:
                win32evtlog.CloseEventLog(handle)
            except Exception as e:
                print(f"Error closing log handle for {log_type}: {e}")
    return logs

def main():
    # Define the log sources
    log_types = ["Application", "System", "Security"]
    computer = None  # Set to target computer name or None for local logs

    print("Starting log collection...")
    for log_type in log_types:
        read_logs(computer, log_type)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript stopped.")