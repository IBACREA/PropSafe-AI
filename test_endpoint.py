"""Test endpoint de búsqueda"""
import requests
import json

url = "http://localhost:8081/api/property/search"
data = {"matricula": "110814602"}

try:
    print(f"Enviando POST a {url}")
    print(f"Body: {json.dumps(data)}")
    
    response = requests.post(url, json=data)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
except Exception as e:
    print(f"Error: {e}")
