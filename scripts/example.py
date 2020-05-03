#!/usr/bin/env python

import os
from pprint import pprint

import requests

APP_ENDPOINT = os.getenv("APP_ENDPOINT", "http://127.0.0.1:8000")
print("APP_ENDPOINT: " + APP_ENDPOINT)
print()

url = f"{APP_ENDPOINT}/ping"
response = requests.get(url)
data = response.json()
print("Response for: " + url)
pprint(data, indent=4)
print()

url = f"{APP_ENDPOINT}/api/v1/example"
a = 5
b = 5
payload = {"a": a, "b": b}
response = requests.post(url, json=payload)
data = response.json()
print("Response for: " + url)
pprint(data, indent=4)
print()
