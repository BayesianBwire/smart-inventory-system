import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64


def lipa_na_mpesa(phone_number, amount):
    base_url = "https://sandbox.safaricom.co.ke"

    # 🔐 Load credentials from environment
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")

    # ✅ Debug output for env variables
    print("🔑 Consumer Key:", repr(consumer_key))
    print("🔑 Consumer Secret:", repr(consumer_secret))

    if not consumer_key or not consumer_secret:
        raise EnvironmentError("❌ Consumer Key or Secret not found in environment variables.")

    # ✅ Step 1: Get access token
    token_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    token_response = requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))

    if token_response.status_code != 200:
        print("❌ Failed to get token:", token_response.text)
        raise ValueError("Failed to get access token from Safaricom.")

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    print("✅ Access Token:", access_token)

    if not access_token:
        raise ValueError("❌ Access token not found in Safaricom response.")

    # ✅ Step 2: Prepare STK Push request
    shortcode = os.getenv("MPESA_SHORTCODE")
    passkey = os.getenv("MPESA_PASSKEY")
    callback_url = os.getenv("MPESA_CALLBACK_URL")

    if not all([shortcode, passkey, callback_url]):
        raise EnvironmentError("❌ One or more M-Pesa configuration values missing.")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": "SmartShop",
        "TransactionDesc": "SmartShop Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print("📤 Sending STK Push request with payload:")
    print(payload)

    # ✅ Step 3: Send STK Push
    stk_url = f"{base_url}/mpesa/stkpush/v1/processrequest"
    r = requests.post(stk_url, json=payload, headers=headers)

    # ✅ Step 4: Handle Safaricom response
    try:
        response_data = r.json()
        print("✅ Safaricom JSON Response:")
        print(response_data)
        # Add this line for convenience:
        response_data['description'] = response_data.get("ResponseDescription") or response_data.get("errorMessage") or "No response description"
        return response_data
    except Exception as e:
        print("❌ Could not decode response. Raw response text:\n", r.text)
        raise ValueError("Could not decode Safaricom response.")
