import requests

BASE_URL = "http://localhost:8000"
creds = {"username": "admin", "password": "AM3D@MGR#1"}

def test_audit():
    try:
        # 1. Login
        print("Tentando login...")
        resp = requests.post(f"{BASE_URL}/login", json=creds)
        if resp.status_code != 200:
            print(f"Erro no login: {resp.status_code} - {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK!")

        # 2. Test Stats
        print("Chamando /stats...")
        resp = requests.get(f"{BASE_URL}/stats", headers=headers)
        if resp.status_code != 200:
            print(f"ERRO em /stats: {resp.status_code}")
            print(resp.text)
        else:
            print("Stats OK!")
            print(resp.json())

    except Exception as e:
        print(f"Erro de conexão: {e}")

if __name__ == "__main__":
    test_audit()
