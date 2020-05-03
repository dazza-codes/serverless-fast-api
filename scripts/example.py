#!/usr/bin/env python

import requests
from pprint import pprint

BASE_URI = "http://127.0.0.1:8000"

url = f"{BASE_URI}/ping"
response = requests.get(url)
data = response.json()
pprint(data, indent=4)

url = f"{BASE_URI}/api/v1/example"
a = 5
b = 5
payload = {"a": a, "b": b}
response = requests.post(url, json=payload)
data = response.json()
pprint(data, indent=4)
