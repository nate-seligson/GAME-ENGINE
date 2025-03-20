#!/usr/bin/python3

import sys
import json
import socket
import os

# Define ESP32 connection details
ESP32_IP = "192.168.1.186"
ESP32_PORT = 8888

def send_pixel_data(pixel_data):
    print(pixel_data)
    try:
        # Format pixel data to a string
        messages = [
            f"{p[0]},{p[1]},{p[2]},{p[3]},{p[4]}\n"
            for p in pixel_data
        ]
        payload = "".join(messages).encode()

        # Send the data to the ESP32 via socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ESP32_IP, ESP32_PORT))
            s.sendall(payload)
            print(f"Sent {len(pixel_data)} pixels to ESP32")
    except Exception as e:
        print(f"Error: {e}")
        return False
    return True

# CGI output (inform the browser that the response will be JSON)
print("Content-type: application/json\n")

# Handle POST requests
if os.environ.get('REQUEST_METHOD') == 'POST':
    # Read the raw POST data from stdin
    try:
        length = int(os.environ.get('CONTENT_LENGTH', 0))
        post_data = sys.stdin.read(length)  # Read the raw POST data
        
        # Parse the data into a Python dictionary
        data = json.loads(post_data)  # Convert JSON string to Python dict

        # Optionally, you can print the received data for debugging
        print(f"Received data: {data}")

        # Send the received data to the ESP32
        result = send_pixel_data(data['grid'])  # Assume the data contains a 'grid' key

        # Send appropriate response based on the result of the data transmission
        if result:
            response = {'status': 'success', 'message': 'Pixel data sent successfully'}
        else:
            response = {'status': 'error', 'message': 'Failed to send pixel data'}

    except Exception as e:
        response = {'status': 'error', 'message': f'Error processing request: {str(e)}'}

else:
    response = {'status': 'error', 'message': 'Invalid HTTP method. Only POST is allowed.'}
