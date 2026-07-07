"""agents.py – CrewAI workflow and security sweep for Scan AASM"""
import os
import json
from datetime import datetime
from typing import List, Dict

from sqlalchemy.orm import Session

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Local imports
from database import Asset, SecurityReport, get_db
from tools import serper_search, ssl_check, extract_assets_from_serper

import requests
import logging

# Load OpenRouter credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3.5-sonnet"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), "error.log"),
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    """Send a chat request to OpenRouter and return the assistant's content.
    The model is expected to output a markdown string.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo/scan-aasm",  # optional
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }
    try:
        resp = requests.post(OPENROUTER_ENDPOINT, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # OpenRouter returns choices[0].message.content
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        logging.error(f"OpenRouter call failed: {e}")
        raise

def recon_specialist(db: Session) -> List[Dict]:
    """Iterate over all assets and gather reconnaissance data.
    Returns a list of dictionaries, one per asset, containing raw tool outputs.
    """
    results = []
    assets = db.query(Asset).all()
    for asset in assets:
        asset_result = {"id": asset.id, "type": asset.asset_type, "url": asset.asset_url}
        try:
            if asset.asset_type in ("website", "webapp"):
                # Use Serper to discover subdomains/related URLs
                serper_raw = serper_search(asset.asset_url)
                asset_result["serper_raw"] = serper_raw
                asset_result["discovered"] = extract_assets_from_serper(serper_raw)
                # SSL check
                host = asset.asset_url.replace("https://", "").replace("http://", "").split("/")[0]
                asset_result["ssl"] = ssl_check(host)
            elif asset.asset_type == "instagram":
                # Placeholder – real implementation would call Instagram API or scraper
                asset_result["note"] = "Instagram scanning not implemented in this prototype"
            else:
                asset_result["note"] = f"Unknown asset_type {asset.asset_type}"
        except Exception as e:
            logging.error(f"Recon error for asset {asset.id}: {e}")
            asset_result["error"] = str(e)
        results.append(asset_result)
    return results

def senior_secops_analyst(recon_data: List[Dict]) -> Dict:
    """Send Recon JSON to Claude via OpenRouter and get a markdown report.
    The function returns a dict with keys: status_flag, markdown_report.
    """
    system_prompt = (
        "You are a senior security analyst. You receive raw reconnaissance data in JSON format. "
        "Identify any potential vulnerabilities, rate their severity as HIGH, MEDIUM, or LOW, "
        "and produce a concise markdown report that includes a summary table and remediation steps. "
        "If no issues are found, set the status to SECURE."
    )
    user_prompt = json.dumps(recon_data, indent=2)
    markdown = call_openrouter(system_prompt, user_prompt)
    # Very naive extraction of status flag – look for the word SECURE or WARNING in the markdown
    status_flag = "WARNING" if "SECURE" not in markdown.upper() else "SECURE"
    return {"status_flag": status_flag, "markdown_report": markdown}

def run_security_sweep(db_dependency=get_db):
    """Background task invoked by APScheduler.
    It pulls assets, runs Recon, passes results to SecOps, and stores a SecurityReport.
    """
    try:
        # Get a DB session from the dependency generator
        db_gen = db_dependency()
        db = next(db_gen)
        recon_data = recon_specialist(db)
        analysis = senior_secops_analyst(recon_data)
        report = SecurityReport(
            timestamp=datetime.utcnow(),
            status_flag=analysis["status_flag"],
            raw_json_logs=json.dumps(recon_data),
            markdown_report=analysis["markdown_report"],
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        # Close the session
        db.close()
        return {"id": report.id, "status": report.status_flag}
    except Exception as e:
        logging.error(f"run_security_sweep failed: {e}")
        # Swallow exception so scheduler keeps running
        return {"error": str(e)}
