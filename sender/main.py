# system_monitor.py

import psutil
import time
import datetime
import requests  # Import the requests library for making HTTP requests

# Configuration for the API endpoint
API_URL = "http://127.0.0.1:1337/stats"  # Ensure this matches your API server's address and port

def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def get_cpu_metrics():
    return psutil.cpu_percent(), datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

def get_memory_metrics():
    virtual_mem = psutil.virtual_memory()
    total_memory_mb = virtual_mem.total / (1024 * 1024)
    used_memory_mb = virtual_mem.used / (1024 * 1024)
    free_memory_mb = virtual_mem.free / (1024 * 1024)
    return used_memory_mb, total_memory_mb, free_memory_mb

def get_network_io_metrics():
    net_io_counters_before = psutil.net_io_counters()
    time.sleep(1)
    net_io_counters_after = psutil.net_io_counters()

    bytes_sent_per_sec = (net_io_counters_after.bytes_sent - net_io_counters_before.bytes_sent) / 1024 / 1024
    bytes_recv_per_sec = (net_io_counters_after.bytes_recv - net_io_counters_before.bytes_recv) / 1024 / 1024
    return bytes_sent_per_sec, bytes_recv_per_sec

def get_disk_io_metrics():
    disk_io_counters_before = psutil.disk_io_counters()
    time.sleep(1)
    disk_io_counters_after = psutil.disk_io_counters()

    read_bytes_per_sec = (disk_io_counters_after.read_bytes - disk_io_counters_before.read_bytes) / 1024 / 1024
    write_bytes_per_sec = (disk_io_counters_after.write_bytes - disk_io_counters_before.write_bytes) / 1024 / 1024
    return read_bytes_per_sec, write_bytes_per_sec

def send_metrics_to_api(data):
    """
    Sends the collected system metrics to the configured API endpoint.
    """
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        response.raise_for_status()
        print(f"API Response: {response.status_code} - {response.json().get('message', 'Success')}")
    except requests.exceptions.ConnectionError as e:
        print(f"API Connection Error: Could not connect to {API_URL}. Is the server running? {e}")
    except requests.exceptions.Timeout:
        print(f"API Request Timeout: No response from {API_URL} within 5 seconds.")
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while sending data to API: {e}")

def main():
    print("Starting Python System Monitor. Press Ctrl+C to stop.")
    print("Note: CPU temperature availability is OS-dependent and may require additional setup (e.g., lm-sensors on Linux).")
    print("Run the script with administrator/root privileges for best results.")

    while True:
        try:
            current_timestamp = datetime.datetime.now().isoformat()
            display_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{display_timestamp}]")

            # CPU Metrics
            cpu_usage, sys_boot_time = get_cpu_metrics()
            print(f"CPU Usage: {cpu_usage:.1f}% | System Boot Time: {sys_boot_time}")

            # Memory Metrics
            mem_used, mem_total, mem_free = get_memory_metrics()
            print(f"Memory Used: {mem_used:.1f} MB | Total Memory: {mem_total:.1f} MB | Free Memory: {mem_free:.1f} MB")

            # Network IO Metrics
            net_upload, net_download = get_network_io_metrics()
            print(f"Network IO (Up/Down): {net_upload:.2f} MB/s / {net_download:.2f} MB/s")

            # Disk IO Metrics
            disk_read, disk_write = get_disk_io_metrics()
            print(f"Disk IO (Read/Write): {disk_read:.2f} MB/s / {disk_write:.2f} MB/s")

            payload = {
                "timestamp": current_timestamp,
                "cpu": {
                    "usage": cpu_usage,
                    "temperature": sys_boot_time 
                },
                "gpu": {
                    "usage": None,
                    "temperature": None
                },
                "memory": {
                    "total": mem_total,
                    "used": mem_used,
                    "free": mem_free
                },
                "disk": {
                    "io": {
                        "read": disk_read,
                        "write": disk_write
                    }
                },
                "network": {
                    "io": {
                        "received": net_download,
                        "sent": net_upload
                    }
                }
            }

            send_metrics_to_api(payload)
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)  # Wait before retrying after an error

if __name__ == "__main__":
    main()
