import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "security_test_urllib@example.com"
TEST_PASS = "password123"

def post_json(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as response:
        return response.getcode(), response.read().decode('utf-8')

def run_security_test():
    print("🛡️ Iniciando Teste de Segurança: Verificação de Email Único...")
    
    # 1. Tentar registrar
    print(f"Passo 1: Registrando usuário {TEST_EMAIL}...")
    try:
        code, body = post_json(f"{BASE_URL}/register", {"email": TEST_EMAIL, "password": TEST_PASS})
        print(f"✅ Primeiro registro bem-sucedido (Code: {code}).")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print("⚠️ Usuário já existia no banco, continuando teste...")
        else:
            print(f"❌ Erro no servidor: {e.code}")
            return
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return

    # 2. Tentar registrar novamente
    print(f"Passo 2: Tentando registrar o MESMO e-mail ({TEST_EMAIL}) novamente...")
    try:
        code, body = post_json(f"{BASE_URL}/register", {"email": TEST_EMAIL, "password": TEST_PASS})
        print("❌ FALHA DE SEGURANÇA: O sistema permitiu a criação de conta duplicada.")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print("✅ TESTE BEM-SUCEDIDO: O sistema bloqueou o registro duplicado!")
            print(f"Mensagem do Servidor: {e.read().decode('utf-8')}")
        else:
            print(f"❓ Status inesperado: {e.code}")

if __name__ == "__main__":
    run_security_test()
