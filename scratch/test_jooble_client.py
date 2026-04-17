import http.client
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

def test_jooble_client():
    host = 'jooble.org'
    key = os.getenv("JOOBLE_API_KEY", "")

    if not key:
        pytest.skip("JOOBLE_API_KEY não encontrada. Configure a variável de ambiente para executar este teste.")

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
