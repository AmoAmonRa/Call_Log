# Telsa64 Call Log Web Interface

A **FastAPI-based web interface** to process, display, and play audio call logs from MP3/WAV files. Automatically detects new files in the `files/` directory. The interface shows calls in **Farsi** with **Persian numerals** and supports **Shamsi (Jalali) dates**.

---

## Features

- **Automatic file detection** using `watchdog`. New `.mp3` or `.wav` files added to `files/` are automatically processed.
- **Telsa64 log processing**:
  - Reads the last line `Telsa64` to verify the file.
  - Extracts the number of lines specified before `Telsa64`.
  - Parses `Info`, `Number`, and `CallWindow` lines.
- **JSON database** (`database.json`) stores all parsed entries.
- **Web interface**:
  - Display call list with:
    - شماره ها (Phone Numbers in Persian digits)
    - نوع تماس (Call Type)
    - تاریخ (Date in Shamsi)
    - زمان ذخیره (Time)
    - پخش مکالمه (Audio Playback)
  - Sortable columns.
  - Sequential playback of all calls.
- **Farsi support**: All numbers converted to Persian digits, RTL layout.
- **Robust error handling**: Logs decoding/parsing errors without crashing.

---

## Directory Structure

````
project_root/
│
├── app.py # Main FastAPI application and call log processor
├── database.json # Auto-generated JSON database of calls
├── files/ # Folder for audio files (MP3/WAV)
├── README.md # This file
└── requirements.txt # Python dependencies
````
## Start the server:

``` uvicorn app:app --reload```


- **Open your browser:**

- ```http://127.0.0.1:8000```


- Add audio files:

- Place .mp3 or .wav files in the files/ directory.

- **Ensure the files contain Telsa64 logs. The script automatically detects new files, parses logs, and updates the web interface.**
Log File Structure

## Example:
```json
2025/12/09 11:34:30|Info|FileName:e9c9be2f-5932-4226-8ac7-5c5ab5de09e9|ServerName:TELSAPC|Card:0x40000047a69dc00|Channel:1
2025/12/09 11:34:42|Number|Number:09123456789
2025/12/09 11:34:42|CallWindow|Status:Start|Call_Type:Voice_Call|Color:Gray
11
Telsa64
```


- The integer before Telsa64 specifies how many lines to read backwards.

 - The script extracts Info, Number, and CallWindow lines and stores them in JSON.
## JSON Database Format
```json
[
    {
        "FileName": "example.mp3",
        "Info": {
            "FileName": "example.mp3",
            "ServerName": "TELSAPC",
            "Card": "0x40000047a69dc00",
            "Channel": "1",
            "Date": "2025/12/09 11:34:30"
        },
        "Number": {
            "Number": "09123456789"
        },
        "CallWindow": {
            "Status": "Start",
            "Call_Type": "Voice_Call",
            "Color": "Gray"
        }
    }
]
```
## Web Interface Features

- Table Columns:
 - ردیف → Row number (Persian numerals)
- شماره ها → Phone numbers (Persian digits)

- نوع تماس → Call type (Voice/Video)

- تاریخ → Date (Shamsi)

- زمان ذخیره → Time
- پخش مکالمه → Audio playback

- Sortable columns by clicking the header.

- Sequential playback with play/stop buttons.

## Sample Workflow

- Add a new call file to files/:
```json
files/
└── 1234abcd.mp3
```



- The script automatically detects the file, parses logs, and updates database.json.

- Open web interface to see the table populated with:

- Phone numbers in Persian digits

- Call type in Farsi

- Dates in Shamsi

- Audio playback controls
- Play all calls sequentially using the ▶️ پخش پشت‌سرهم button.
## Turning into a Standalone EXE

- You can turn this FastAPI app into a Windows executable using PyInstaller:

- Install PyInstaller:

- pip install pyinstaller


- **Create the executable:**

- ```pyinstaller --onefile --add-data "files;files" --add-data "database.json;." app.py```


- **Explanation:**

- --onefile: Bundle everything into a single EXE.

-  ```--add-data "files;files"```: Include the files/ directory.

- ```--add-data "database.json;```": Include the JSON database file.

- Adjust paths for Linux/macOS if needed (: instead of ;).

- **Run the EXE:**

```dist\app.exe```


- **The EXE will start the FastAPI server.**

- Open the browser at http://127.0.0.1:8000/. 
## Error Handling

- If the file is missing Telsa64, it is skipped.

- Default values are used if Number or CallWindow lines are missing.

- Errors are printed in the console; the server continues running.
