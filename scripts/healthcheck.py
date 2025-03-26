import sys
import requests


def health_check(port):
    try:
        response = requests.get(f"http://localhost:{port}/status")
        if response.status_code == 200:
            print("Healthy")
            sys.exit(0)
        else:
            print("Unhealthy")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: healthcheck.py <port>")
        sys.exit(1)
    port = sys.argv[1]
    health_check(port)
