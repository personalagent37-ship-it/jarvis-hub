import requests
try:
    res = requests.get("https://openrouter.ai/api/v1/models")
    models = res.json()["data"]
    free_models = [m["id"] for m in models if ":free" in m["id"] or m.get("pricing", {}).get("prompt") == "0"]
    print("FREE MODELS:")
    for m in free_models:
        print(m)
except Exception as e:
    print("Error:", e)
