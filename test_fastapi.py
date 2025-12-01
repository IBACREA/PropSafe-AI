"""Test simple del endpoint"""
import sys
sys.path.insert(0, 'D:/projects/datos/backend')

from fastapi.testclient import TestClient
from main_simple import app

client = TestClient(app)

print("Probando endpoint...")
try:
    response = client.post("/api/property/search", json={"matricula": "110814602"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
