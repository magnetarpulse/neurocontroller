import requests

BB_IP = "192.168.1.106"  
try:
    response = requests.get(f"http://{BB_IP}:8001/list_files/")
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error:", e)
