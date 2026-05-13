import urllib.request
import sys

def check():
    url = "http://127.0.0.1:8000/api/auth/login/"
    print(f"📡 Testando conexão com {url}...")
    try:
        response = urllib.request.urlopen(url, timeout=10)
        print(f"✅ Sucesso! Status: {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"⚠️ Resposta do servido (esperado 405): {e.code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    check()
