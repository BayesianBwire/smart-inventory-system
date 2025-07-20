import requests
import base64
from datetime import datetime

# 🔑 Hardcoded credentials (For now. In production, use .env)
consumer_key = "6BEnGPCtLXEmVegJqMTOj9zlVxsbooZGLeP8RGGQgvCtx4r7"
consumer_secret = "9vxPbj1MhpEfcAdE8EcK67KQ2QATxBJGsZr0ELpnxAshqvan3sL9LiGlsoGvNgkt"
shortcode = "174379"  # Replace with your actual Till if you're going live
passkey = "bfb279f9aa9bdbcf15e97dd71a467cd2c2c968d8ab82d008e87c1c6b0ab9d6f3"
callback_url = "https://yourdomain.com/api/v1/mpesa/callback"  # Replace with ngrok or real URL if live
base_url = "https://sandbox.safaricom.co.ke"

def get_access_token():
    token_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(token_url, auth=(consumer_key, consumer_secret))
    return response.json().get("access_token")

def lipa_na_mpesa(phone_number, amount, account_reference="RahaSoft", description="Payment"):
    access_token = get_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",  # For TILL numbers
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": description
    }

    response = requests.post(f"{base_url}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
    return response.json()
