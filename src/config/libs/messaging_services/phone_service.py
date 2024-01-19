import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('FARAZ_SMS_API')

url = "https://api2.ippanel.com/api/v1/sms/pattern/normal/send"


def send_otp_phone(to, code):
    payload = json.dumps({
        "code": "2k3wp5r73wans40",
        "sender": "+983000505",
        "recipient": str(to),
        "variable": {
            "code": str(code)
        }
    })
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response)
    # while True:
    #     response = requests.request("POST", url, headers=headers, data=payload)
    #     response_data = response.json()
    #
    #     if response_data["status"] == "OK":
    #         print("OTP sent successfully!")
    #         # You can perform additional actions here if needed
    #         break  # Exit the loop since the OTP was sent successfully
    #     else:
    #         print("OTP sending failed. Retrying...")


def send_order_status_phone(to, pattern, number, track_code=None):
    pattern_values = {
        "order_number": str(number),
    }

    if track_code:
        pattern_values["track_code"] = str(track_code)

    payload = json.dumps({
        "code": str(pattern),
        "sender": "+983000505",
        "recipient": str(to),
        "variable": pattern_values
    })
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
