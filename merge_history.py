import openpyxl
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
KWH_FILE = os.path.join(BASE_DIR, "backend", "kwh_history.json")

if os.path.exists(KWH_FILE):
    with open(KWH_FILE, "r") as f:
        db = json.load(f)
else:
    db = {}

for fname in sorted(os.listdir(EXPORTS_DIR)):
    if not fname.startswith("sensor_") or not fname.endswith(".xlsx"):
        continue

    date_str = fname.replace("sensor_", "").replace(".xlsx", "")

    if date_str in db and db[date_str].get("samples", 0) > 0:
        print(f"⏭️  {date_str} sudah ada di kwh_history, skip")
        continue

    path = os.path.join(EXPORTS_DIR, fname)
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    all_rows = list(ws.iter_rows(min_row=1, values_only=True))
    if not all_rows:
        print(f"⚠️  {date_str} kosong, skip")
        continue

    header = [str(h).strip() for h in all_rows[0]]

    def col_idx(*names):
        for n in names:
            if n in header:
                return header.index(n)
        return None

    idx_ts   = col_idx("Timestamp")
    idx_daya = col_idx("Daya (W)", "Daya", "daya")

    if idx_ts is None or idx_daya is None:
        print(f"⚠️  {date_str} header tidak dikenali: {header}, skip")
        continue

    rows = all_rows[1:]

    wh = 0.0
    peak = 0.0
    total_daya = 0.0
    samples = 0
    prev_time = None
    first_ts = None
    last_ts = None

    for row in rows:
        ts_raw = row[idx_ts]
        daya = row[idx_daya]
        if ts_raw is None or daya is None:
            continue

        daya = float(daya)
        ts = datetime.strptime(str(ts_raw), "%Y-%m-%d %H:%M:%S")

        if first_ts is None:
            first_ts = ts
        last_ts = ts

        if prev_time is not None:
            dt = (ts - prev_time).total_seconds()
            if 0 < dt <= 10:
                wh += daya * dt / 3600.0

        prev_time = ts
        total_daya += daya
        samples += 1
        if daya > peak:
            peak = daya

    if samples == 0:
        continue

    avg_watt = total_daya / samples
    kwh = wh / 1000.0

    db[date_str] = {
        "date": date_str,
        "kwh": round(kwh, 4),
        "wh": round(wh, 2),
        "samples": samples,
        "peak_watt": round(peak, 2),
        "avg_watt": round(avg_watt, 2),
        "first_seen": first_ts.isoformat(),
        "last_seen": last_ts.isoformat()
    }

    print(f"✅ {date_str}: kwh={kwh:.4f}, samples={samples}, peak={peak}, avg={avg_watt:.2f}")

with open(KWH_FILE, "w") as f:
    json.dump(db, f, indent=2)

print("\n🎉 Selesai. Total tanggal di kwh_history:", len(db))
