import json
import hashlib
import requests
from socketio import Client

sio = Client()

SERVER_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{SERVER_URL}/api/auth/login"

USERNAME = "Tim"
PASSWORD = hashlib.sha256("12345678".encode("utf-8")).hexdigest()  # SHA256 

def login_and_get_token():
    try:
        response = requests.post(LOGIN_URL, json={"username": USERNAME, "password": PASSWORD})
        response.raise_for_status()  
        data = response.json()
        return data.get("token")  
    except Exception as e:
        print(f"Login failed: {e}")
        return None

@sio.event
def connect():
    print("Connected to the server")
    sio.emit("join", {"room": "task_updates"})  

@sio.event
def disconnect():
    print("Disconnected from the server")

@sio.on("task_updates")
def handle_task_updates(data):
    print("Received task updates:")
    print(json.dumps(data, indent=4))

@sio.on("error")
def handle_error(data):
    print(f"Server error: {data['message']}")
    sio.disconnect()  

if __name__ == "__main__":
    JWT_TOKEN = login_and_get_token()

    if not JWT_TOKEN:
        print("Unable to retrieve JWT token. Exiting...")
    else:
        try:
            sio.connect(SERVER_URL, auth={"token": JWT_TOKEN})  
            print("Listening for task updates...")
            sio.wait()
        except Exception as e:
            print(f"An error occurred: {e}")
