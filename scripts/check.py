#!/usr/bin/env python3
"""
Health check script — reads config.yml, probes each service,
writes results to data/status.json.
"""
import json
import time
import yaml
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yml"
HISTORY_PATH = Path(__file__).parent.parent / "data" / "history.json"
MAX_HISTORY = 144  # keep 24h of 10-min samples


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def probe(service):
    url     = service["url"]
    timeout = service.get("timeout", 10)
    expect  = service.get("expected_status", 200)
    expect_text = service.get("expected_text", None)

    start = time.monotonic()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "StatusMonitor/1.0 (+https://github.com)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096).decode("utf-8", errors="ignore")
            latency_ms = round((time.monotonic() - start) * 1000)
            status_code = resp.status

            ok = status_code == expect
            if ok and expect_text:
                ok = expect_text.lower() in body.lower()

            return {
                "status": "up" if ok else "degraded",
                "status_code": status_code,
                "latency_ms": latency_ms,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        ok = e.code == expect
        return {
            "status": "up" if ok else "down",
            "status_code": e.code,
            "latency_ms": latency_ms,
            "error": str(e),
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "down",
            "status_code": None,
            "latency_ms": latency_ms,
            "error": str(e)[:200],
        }


def main():
    cfg = load_config()
    now = datetime.now(timezone.utc).isoformat()

    results = []
    for svc in cfg.get("services", []):
        result = probe(svc)
        results.append({
            "name": svc["name"],
            "url":  svc["url"],
            **result,
        })

    # Load / update history
    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text())
        except Exception:
            history = []

    history.append({"time": now, "services": results})
    history = history[-MAX_HISTORY:]
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False))

    # Build output
    output = {
        "updated_at": now,
        "services": results,
        "history": history[-48:],  # last 4h in output json
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
