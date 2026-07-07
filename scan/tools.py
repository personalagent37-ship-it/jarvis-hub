"""tools.py – Custom CrewAI tools for Scan AASM"""
import os
import json
import socket
import ssl
import requests
from datetime import datetime
from typing import List, Dict

# Load API keys from environment (scan/.env)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def serper_search(query: str, num_results: int = 10) -> Dict:
    """Call Serper API to search for subdomains / leaks.
    Returns the raw JSON response.
    """
    url = "https://serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num_results}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        # Return a minimal error structure – callers will handle logging
        return {"error": str(e), "query": query}

def ssl_check(host: str, port: int = 443) -> Dict:
    """Fetch SSL certificate info for a host.
    Returns dict with expiry date and any error.
    """
    context = ssl.create_default_context()
    result = {"host": host, "port": port}
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                result["notAfter"] = cert.get("notAfter")
                result["issuer"] = dict(x[0] for x in cert.get("issuer", []))
    except Exception as e:
        result["error"] = str(e)
    return result

def extract_assets_from_serper(raw: Dict) -> List[Dict]:
    """Simplify Serper output into a list of discovered URLs/subdomains.
    This function is highly placeholder – real implementation would parse organic_results.
    """
    assets = []
    organic = raw.get("organic", [])
    for entry in organic:
        link = entry.get("link")
        if link:
            assets.append({"type": "url", "value": link})
    return assets
