import json
import os
import threading
from datetime import datetime

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "kwh_history.json"
)

_lock = threading.Lock()

def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Gagal simpan kWh:", e)

def update_kwh(daya_watt, interval_seconds=1):
    today = datetime.now().strftime("%Y-%m-%d")

    with _lock:
        db = _load()
        if today not in db:
            db[today] = {
                "date":       today,
                "kwh":        0.0,
                "wh":         0.0,
                "samples":    0,
                "peak_watt":  0.0,
                "avg_watt":   0.0,
                "first_seen": datetime.now().isoformat(),
                "last_seen":  datetime.now().isoformat()
            }
        rec = db[today]
        rec["wh"]       += daya_watt * interval_seconds / 3600.0
        rec["kwh"]       = rec["wh"] / 1000.0
        rec["samples"]  += 1
        rec["last_seen"] = datetime.now().isoformat()
        n = rec["samples"]
        rec["avg_watt"]  = (rec["avg_watt"] * (n - 1) + daya_watt) / n
        if daya_watt > rec["peak_watt"]:
            rec["peak_watt"] = daya_watt
        _save(db)

def get_kwh_history():
    with _lock:
        db = _load()
    return sorted(db.values(), key=lambda x: x["date"], reverse=True)

def get_kwh_today():
    today = datetime.now().strftime("%Y-%m-%d")
    with _lock:
        db = _load()
    return db.get(today, {
        "date": today, "kwh": 0.0, "wh": 0.0,
        "samples": 0, "peak_watt": 0.0, "avg_watt": 0.0,
        "first_seen": None, "last_seen": None
    })