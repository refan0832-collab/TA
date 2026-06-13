import json
import os
import shutil
import threading
from datetime import datetime

# =========================
# PATH FILE
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE   = os.path.join(BASE_DIR, "kwh_history.json")
BACKUP_FILE = os.path.join(BASE_DIR, "kwh_history.backup.json")

_lock = threading.Lock()

# =========================
# LOAD
# Urutan: coba file utama → coba backup → return {}
# =========================

def _load():

    # COBA FILE UTAMA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)

            if isinstance(data, dict) and len(data) > 0:
                return data

            print("⚠️  kwh_history.json kosong, coba backup...")

        except Exception as e:
            print(f"⚠️  Gagal baca kwh_history.json: {e}, coba backup...")

    # COBA BACKUP
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r") as f:
                data = json.load(f)

            if isinstance(data, dict) and len(data) > 0:
                print("✅ Data kWh dipulihkan dari backup")
                return data

        except Exception as e:
            print(f"❌ Gagal baca backup juga: {e}")

    print("⚠️  Tidak ada data kWh tersimpan, mulai dari kosong")
    return {}

# =========================
# SAVE
# Tulis ke file sementara dulu, lalu rename
# agar tidak corrupt kalau proses tiba-tiba berhenti
# =========================

def _save(data):

    # VALIDASI — jangan simpan data kosong
    if not isinstance(data, dict) or len(data) == 0:
        print("⚠️  Data kWh kosong, tidak disimpan")
        return

    TEMP_FILE = DATA_FILE + ".tmp"

    try:
        # TULIS KE FILE SEMENTARA DULU
        with open(TEMP_FILE, "w") as f:
            json.dump(data, f, indent=2)

        # BACKUP FILE LAMA sebelum ditimpa
        if os.path.exists(DATA_FILE):
            shutil.copy2(DATA_FILE, BACKUP_FILE)

        # RENAME TEMP → FILE UTAMA (atomic operation)
        os.replace(TEMP_FILE, DATA_FILE)

    except Exception as e:
        print(f"❌ Gagal simpan kWh: {e}")

        if os.path.exists(TEMP_FILE):
            try:
                os.remove(TEMP_FILE)
            except:
                pass

# =========================
# UPDATE kWh
# =========================

def update_kwh(daya_watt, interval_seconds=2):

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

        rec["wh"]      += daya_watt * interval_seconds / 3600.0
        rec["kwh"]      = rec["wh"] / 1000.0
        rec["samples"] += 1
        rec["last_seen"] = datetime.now().isoformat()

        n = rec["samples"]
        rec["avg_watt"] = (rec["avg_watt"] * (n - 1) + daya_watt) / n

        if daya_watt > rec["peak_watt"]:
            rec["peak_watt"] = daya_watt

        _save(db)

# =========================
# RESET
# =========================

def reset_kwh():
    with _lock:

        if os.path.exists(DATA_FILE):
            try:
                os.remove(DATA_FILE)
            except Exception as e:
                print(f"❌ Gagal hapus kwh_history.json: {e}")

        if os.path.exists(BACKUP_FILE):
            try:
                os.remove(BACKUP_FILE)
            except Exception as e:
                print(f"❌ Gagal hapus backup: {e}")

        TEMP_FILE = DATA_FILE + ".tmp"
        if os.path.exists(TEMP_FILE):
            try:
                os.remove(TEMP_FILE)
            except:
                pass

        print("🗑️  kwh_history direset")

# =========================
# GET HISTORY
# =========================

def get_kwh_history():

    with _lock:
        db = _load()

    return sorted(
        db.values(),
        key=lambda x: x["date"],
        reverse=True
    )

# =========================
# GET TODAY
# =========================

def get_kwh_today():

    today = datetime.now().strftime("%Y-%m-%d")

    with _lock:
        db = _load()

    return db.get(today, {
        "date":       today,
        "kwh":        0.0,
        "wh":         0.0,
        "samples":    0,
        "peak_watt":  0.0,
        "avg_watt":   0.0,
        "first_seen": None,
        "last_seen":  None
    })