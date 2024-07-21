import json
import requests


api_key = "ptr_POGAF4ilj9LLx3w71u7yFSkj+WGf60UFaCq0fKQJ7VM="
stack_id = 45

# URLs
base_url = "http://10.0.10.131:9000/api"
stacks_url = base_url + f"/stacks/{stack_id}"

# Get stack file content
stack_file = requests.get(stacks_url + "/file", headers={"X-API-KEY": api_key})
try:
    stack_file.raise_for_status()
    json_file = stack_file.json()
except Exception as e:
    print("Error: " + str(e))
    print(stack_file.json())
    exit(1)

stack_file_content = json_file["StackFileContent"]

# Get Stack details
stack_details_res = requests.get(stacks_url, headers={"X-API-KEY": api_key})
try:
    stack_details_res.raise_for_status()
    stack_details = stack_details_res.json()
except Exception as e:
    print("Error: " + str(e))
    print(stack_details_res.json())
    exit(1)
stack_env = stack_details["Env"]
stack_webhook = stack_details["Webhook"]

# Now update the stack
update_data = {
    "stackFileContent": stack_file_content,
    "env": stack_env,
    "prune": False,
    "webhook": stack_webhook,
    "pullImage": False,
}
update_json = json.dumps(update_data)  # Convert to JSON
api_response = requests.put(
    stacks_url,
    headers={"X-API-KEY": api_key},
    params={"endpointId": 1},
    data=update_json,
)
try:
    api_response.raise_for_status()
    # print(api_response.json())
except Exception as e:
    print("Error: " + str(e))
    print(api_response.json())
    exit(1)

# stop_res = requests.post(
#     stacks_url + "/stop", headers={"X-API-KEY": api_key}, params={"endpointId": 1}
# )
# try:
#     stop_res.raise_for_status()
#     # print(stop_res.json())
# except requests.exceptions.HTTPError as e:
#     print("Error: " + str(e))
#     print(stop_res.json())
#     exit(1)

# start_res = requests.post(
#     stacks_url + "/start", headers={"X-API-KEY": api_key}, params={"endpointId": 1}
# )
# try:
#     start_res.raise_for_status()
#     # print(start_res.json())
# except requests.exceptions.HTTPError as e:
#     print("Error: " + str(e))
#     print(start_res.json())
#     exit(1)

print("Stack restarted successfully")
exit(0)
