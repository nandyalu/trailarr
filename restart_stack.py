import requests


api_key = "ptr_POGAF4ilj9LLx3w71u7yFSkj+WGf60UFaCq0fKQJ7VM="
stack_id = 45

# URLs
base_url = "http://10.0.10.131:9000/api"
stacks_url = base_url + f"/stacks/{stack_id}"

stop_res = requests.post(
    stacks_url + "/stop", headers={"X-API-KEY": api_key}, params={"endpointId": 1}
)
try:
    stop_res.raise_for_status()
    # print(stop_res.json())
except requests.exceptions.HTTPError as e:
    print("Error: " + str(e))
    print(stop_res.json())
    exit(1)

start_res = requests.post(
    stacks_url + "/start", headers={"X-API-KEY": api_key}, params={"endpointId": 1}
)
try:
    start_res.raise_for_status()
    # print(start_res.json())
except requests.exceptions.HTTPError as e:
    print("Error: " + str(e))
    print(start_res.json())
    exit(1)

print("Stack restarted successfully")
exit(0)
