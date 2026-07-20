"""Scan deployed frontend bundles for embedded API URLs — no secrets."""
from __future__ import annotations

import json
import re

import httpx

FRONTENDS = [
    ("Sampada", "https://sampada.blackholeinfiverse.com/"),
    ("Artha", "https://artha.blackholeinfiverse.com/"),
    ("SETU/CRM", "https://setu.blackholeinfiverse.com/"),
    ("Niyantran", "https://niyantran.blackholeinfiverse.com/"),
]

PATTERNS = [
    ("gateway", r"https://bhiv-hr-gateway[^\s\"']+"),
    ("agent", r"https://bhiv-hr-agent[^\s\"']+"),
    ("langgraph", r"https://bhiv-hr-langgraph[^\s\"']+"),
    ("artha", r"https://ai-artha[^\s\"']+"),
    ("crm", r"https://ai-crm[^\s\"']+"),
    ("niyantran", r"https://blackholeworkflow[^\s\"']+"),
    ("localhost", r"http://localhost:\d+"),
]


def scan_text(text: str, found: dict[str, str]) -> None:
    for key, pat in PATTERNS:
        if key in found:
            continue
        m = re.search(pat, text)
        if m:
            found[key] = m.group(0)


def main() -> None:
    out = []
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for name, url in FRONTENDS:
            found: dict[str, str] = {}
            r = client.get(url)
            scan_text(r.text or "", found)
            for js in re.findall(r'src="(/assets/[^"]+\.js)"', r.text or "")[:5]:
                jr = client.get(url.rstrip("/") + js)
                scan_text(jr.text or "", found)
            out.append({"frontend": name, "status": r.status_code, "api_urls_found": found})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
