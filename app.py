import os
import sys
import json
import traceback
import threading
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jdatetime import datetime as jdatetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------
# Paths for EXE compatibility
# -------------------------
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_DIR = os.path.join(APP_DIR, "files")
JSON_FILE = os.path.join(APP_DIR, "database.json")

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
    print(f"[INFO] Created files folder at: {FILES_DIR}")

# -------------------------
# FastAPI setup
# -------------------------
app = FastAPI()
app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")

# -------------------------
# Call logs processing
# -------------------------
def extract_logs(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        text = data.decode('utf-8', errors='ignore')
        return text.splitlines()
    except Exception as e:
        print(f"[ERROR] Failed to read or decode {file_path}: {e}")
        traceback.print_exc()
        return []

def parse_log_line(line):
    try:
        parts = line.split('|')
        if len(parts) < 2:
            return None
        fields = parts[2:]
        parsed = {}
        for field in fields:
            if ':' in field:
                key, val = field.split(':', 1)
                parsed[key] = val
        return parsed
    except Exception as e:
        print(f"[ERROR] Failed to parse line: {line} -- {e}")
        return None

def process_logs(lines, file_name):
    if not lines or len(lines) < 2:
        return None
    if lines[-1].strip() != "Telsa64":
        print(f"[INFO] File '{file_name}' is not Telsa64. Skipping.")
        return None

    try:
        count_line_index = len(lines) - 2
        num_lines_to_read = int(lines[count_line_index].strip())
    except Exception as e:
        print(f"[ERROR] Cannot read integer before Telsa64 in {file_name}: {e}")
        return None

    start_index = max(0, count_line_index - num_lines_to_read)
    selected_lines = lines[start_index:count_line_index]

    db_entry = {"FileName": file_name, "Info": None, "Info_line": None, "Number": None, "CallWindow": None}

    for line in selected_lines:
        line = line.strip()
        parts = line.split('|')
        if len(parts) < 2:
            continue
        line_type = parts[1].strip()
        parsed = parse_log_line(line)
        if not parsed:
            continue
        if line_type == "Info":
            db_entry["Info"] = parsed
            db_entry["Info_line"] = line
        elif line_type == "Number":
            db_entry["Number"] = parsed
        elif line_type == "CallWindow":
            db_entry["CallWindow"] = parsed

    if db_entry["Number"] is None:
        db_entry["Number"] = {"Number": "نامشخص"}

    return db_entry

def save_to_json(db_entry):
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
        else:
            db = []

        if not any(e.get("FileName") == db_entry.get("FileName") for e in db):
            db.append(db_entry)
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=4, ensure_ascii=False)
            print(f"[INFO] Saved entry for {db_entry.get('FileName')}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON database: {e}")
        traceback.print_exc()

def process_file(file_path):
    lines = extract_logs(file_path)
    db_entry = process_logs(lines, os.path.basename(file_path))
    if db_entry:
        save_to_json(db_entry)

# -------------------------
# Watchdog file monitoring
# -------------------------
class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.mp3', '.wav')):
            print(f"[INFO] New file detected: {event.src_path}")
            time.sleep(1)
            process_file(event.src_path)

def start_watcher():
    observer = Observer()
    observer.schedule(FileHandler(), FILES_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

threading.Thread(target=start_watcher, daemon=True).start()

# -------------------------
# Web interface helpers
# -------------------------
def convert_info_line_to_shamsi(line):
    """
    Convert date from log line (YYYY/MM/DD HH:MM:SS) to Shamsi.
    """
    if not line:
        return "", ""
    try:
        date_part, time_part = line.split("|")[0].split(" ")
        y, m, d = map(int, date_part.split("/"))
        h, mi, s = map(int, time_part.split(":"))
        j_date = jdatetime.fromgregorian(year=y, month=m, day=d, hour=h, minute=mi, second=s)
        return j_date.strftime("%Y/%m/%d"), j_date.strftime("%H:%M:%S")
    except Exception as e:
        print(f"[ERROR] Failed to convert date: {line} -- {e}")
        return "", ""

def get_call_type_farsi(callwindow):
    if not callwindow:
        return ""
    call_type = callwindow.get("Call_Type", "").lower()
    mapping = {
        "voice_call": "تماس صوتی",
        "null": "نامشخص",
        "video_call": "تماس ویدیویی",
    }
    return mapping.get(call_type, call_type)

def to_persian_numbers(s):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(persian_digits[int(c)] if c.isdigit() else c for c in str(s))

def parse_entry(entry, index):
    number_value = entry.get("Number", {}).get("Number", "نامشخص")
    info_line = entry.get("Info_line")
    date_shamsi, time_shamsi = convert_info_line_to_shamsi(info_line)
    call_type_farsi = get_call_type_farsi(entry.get("CallWindow"))
    file_name = entry.get("FileName", "")
    audio_path = f"/files/{file_name}" if file_name else ""

    return f"""
    <tr>
        <td>{to_persian_numbers(index)}</td>
        <td>{to_persian_numbers(number_value)}</td>
        <td>{call_type_farsi}</td>
        <td>{date_shamsi}</td>
        <td>{time_shamsi}</td>
        <td>{f'<audio controls src="{audio_path}"></audio>' if audio_path else 'بدون فایل'}</td>
    </tr>
    """

# -------------------------
# FastAPI route
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    rows_html = ""
    for idx, entry in enumerate(data, start=1):
        rows_html += parse_entry(entry, idx)

    html = f"""<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>لیست مکالمات</title>
<style>
@font-face {{
    font-family: 'Vazirmatn';
    src: url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Round-Dots/fonts/webfonts/Vazirmatn-RD[wght].woff2') format('woff2 supports variations');
    font-weight: 100 900;
    font-style: normal;
    font-display: swap;
}}
body {{
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Vazirmatn';
    direction: rtl;
    margin: 20px;
}}
table {{
    border-collapse: separate;
    border-radius: 10px;
    border: 2px solid gray;
    border-spacing: 0;
    padding: 2px;
    max-width: 800px;
    width: 100%;
    background-color: #1e1e1e;
    margin: 0 auto;
}}
th, td {{
    border: 1px solid #333;
    padding: 8px 20px;
    text-align: center;
    vertical-align: top;
}}
th {{
    background-color: #2c2c2c;
    cursor: pointer;
}}
tr:nth-child(even) {{
    background-color: #2a2a2a;
}}
tr:hover {{
    background-color: #333;
}}
audio {{
    width: 500px;
    height: 35px;
}}
h1 {{
    text-align: center;
}}
.controls {{
    text-align: center;
    margin-bottom: 12px;
}}
.btn {{
    display: inline-block;
    padding: 8px 14px;
    margin: 0 6px;
    border-radius: 8px;
    background: linear-gradient(180deg, #2b2b2b, #212121);
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    cursor: pointer;
}}
.btn:active {{ transform: translateY(1px); }}
</style>
</head>
<body>
<h1>لیست مکالمات</h1>

<div class="controls">
    <button id="playAllBtn" class="btn">▶️ پخش پشت‌سرهم</button>
    <button id="stopBtn" class="btn">■ توقف</button>
</div>

<table id="recordTable">
<thead>
<tr>
<th>ردیف</th>
<th class='sortable'>شماره ها</th>
<th class='sortable'>نوع تماس</th>
<th class='sortable'>تاریخ</th>
<th class='sortable'>زمان ذخیره</th>
<th>پخش مکالمه</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>

<script>
document.querySelectorAll("th.sortable").forEach((th, index) => {{
    th.addEventListener("click", () => {{
        const table = th.closest("table");
        const tbody = table.querySelector("tbody");
        const rows = Array.from(tbody.querySelectorAll("tr"));
        const ascending = !th.classList.contains("asc");

        rows.sort((a, b) => {{
            const aText = a.children[index+1].textContent.trim();
            const bText = b.children[index+1].textContent.trim();
            const aVal = isNaN(aText) ? aText.toLowerCase() : parseFloat(aText);
            const bVal = isNaN(bText) ? bText.toLowerCase() : parseFloat(bText);
            return ascending ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
        }});

        document.querySelectorAll("th").forEach(th => th.classList.remove("asc", "desc"));
        th.classList.toggle("asc", ascending);
        th.classList.toggle("desc", !ascending);

        tbody.innerHTML = "";
        rows.forEach(row => tbody.appendChild(row));
    }});
}});

let _isPlayingSequential = false;

function playOne(audioEl) {{
    return new Promise((resolve) => {{
        function cleanup() {{
            audioEl.removeEventListener('ended', onEnded);
            audioEl.removeEventListener('pause', onPause);
        }}
        function onEnded() {{ cleanup(); resolve(); }}
        function onPause() {{ cleanup(); resolve(); }}
        audioEl.currentTime = 0;
        audioEl.play().catch(() => resolve());
        audioEl.addEventListener('ended', onEnded);
        audioEl.addEventListener('pause', onPause);
    }});
}}

async function playAllSequential() {{
    if (_isPlayingSequential) return;
    _isPlayingSequential = true;
    const audios = Array.from(document.querySelectorAll('tbody tr audio'));
    for (const a of audios) {{
        if (!_isPlayingSequential) break;
        document.querySelectorAll('audio').forEach(x => {{ if (x !== a) x.pause(); }});
        await playOne(a);
    }}
    _isPlayingSequential = false;
}}

function stopAll() {{
    _isPlayingSequential = false;
    document.querySelectorAll('audio').forEach(a => {{ a.pause(); a.currentTime = 0; }});
}}

document.getElementById('playAllBtn').addEventListener('click', playAllSequential);
document.getElementById('stopBtn').addEventListener('click', stopAll);
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)

# -------------------------
# Run FastAPI
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
