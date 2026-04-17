import http.client
import os
from dotenv import load_dotenv

load_dotenv()

host = 'jooble.org'
key = os.getenv("JOOBLE_API_KEY", "")

if not key:
    print("ERRO: JOOBLE_API_KEY não encontrada.")
    exit()

print(f"Testando com http.client no host {host}...")
connection = http.client.HTTPConnection(host)
headers = {"Content-type": "application/json"}
body = '{ "keywords": "developer", "location": "Brazil"}'

try:
    connection.request('POST', '/api/' + key, body, headers)
    response = connection.getresponse()
    print(f"Status: {response.status} {response.reason}")
    print(response.read().decode())
except Exception as e:
    print(f"Erro: {e}")
