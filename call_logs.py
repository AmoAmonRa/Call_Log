import os
import json
import traceback

def extract_logs(file_path):
    """
    Reads raw bytes from a file and extracts UTF-8 log lines.
    Returns a list of strings.
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        text = data.decode('utf-8', errors='ignore')
        lines = text.splitlines()
        print(f"[DEBUG] Total lines extracted from {file_path}: {len(lines)}")
        return lines
    except Exception as e:
        print(f"[ERROR] Failed to read or decode file: {e}")
        traceback.print_exc()
        return []

def parse_log_line(line):
    """
    Parses a log line into a dictionary of key:value pairs.
    The line format is: date|Type|key1:val1|key2:val2|...
    Returns a dictionary with parsed fields.
    """
    try:
        parts = line.split('|')
        if len(parts) < 2:
            return None
        # Skip the first part (date) and second part (Type) for parsing fields
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
    """
    Processes the lines according to Telsa64 rules.
    Extracts N lines before the integer preceding Telsa64.
    Parses Info, Number, CallWindow lines into JSON-friendly dictionaries.
    """
    if not lines:
        print(f"[ERROR] No lines to process in file: {file_name}")
        return None

    last_line = lines[-1].strip()
    if last_line != "Telsa64":
        print(f"[INFO] File '{file_name}' is not Telsa64. Skipping.")
        return None
    print(f"[INFO] Telsa64 detected in file: {file_name}")

    try:
        count_line_index = len(lines) - 2
        num_lines_to_read = int(lines[count_line_index].strip())
    except Exception as e:
        print(f"[ERROR] Failed to read integer line before Telsa64 in {file_name}: {e}")
        return None

    start_index = count_line_index - num_lines_to_read
    if start_index < 0:
        print(f"[ERROR] Not enough lines to read in file '{file_name}'.")
        return None

    selected_lines = lines[start_index:count_line_index]
    print(f"[INFO] Extracted {len(selected_lines)} lines for processing in {file_name}.")

    # Initialize database entry with file name
    db_entry = {
        "FileName": file_name,
        "Info": None,
        "Number": None,
        "CallWindow": None
    }

    # Process each line and parse it
    for line in selected_lines:
        line = line.strip()
        parts = line.split('|')
        if len(parts) < 2:
            continue
        line_type = parts[1].strip()
        parsed_data = parse_log_line(line)
        if not parsed_data:
            continue

        if line_type == "Info":
            parsed_data["Date"] = parts[0]  # store the first field (timestamp)
            parsed_data["RawLine"] = line  # optional, full raw line
            db_entry["Info"] = parsed_data
        elif line_type == "Number":
            db_entry["Number"] = parsed_data
            print(f"[DEBUG] Parsed Number line: {parsed_data}")
        elif line_type == "CallWindow":
            db_entry["CallWindow"] = parsed_data
            print(f"[DEBUG] Parsed CallWindow line: {parsed_data}")

    # Default Number if missing
    if db_entry["Number"] is None:
        db_entry["Number"] = {"Number": "null"}
        print("[DEBUG] Number line not found. Defaulting to 'Wirelees'.")

    print(f"[INFO] Database entry created for file: {file_name}")
    return db_entry

def save_to_json(db_entry, json_file="database.json"):
    """
    Save or append the database entry to a JSON file.
    """
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                db = json.load(f)
        else:
            db = []

        db.append(db_entry)
        with open(json_file, 'w') as f:
            json.dump(db, f, indent=4)
        print(f"[INFO] Entry saved to {json_file}. Total entries now: {len(db)}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON database: {e}")
        traceback.print_exc()

def process_all_files_in_directory():
    """
    Process all MP3 and WAV files in the current directory.
    """
    current_dir = 'files'
    print(f"[INFO] Scanning directory: {current_dir}")

    files_processed = 0
    for file_name in os.listdir(current_dir):
        if file_name.lower().endswith(('.mp3', '.wav')):
            print(f"[INFO] Processing file: {file_name}")
            file_path = os.path.join(current_dir, file_name)
            lines = extract_logs(file_path)
            db_entry = process_logs(lines, file_name)
            if db_entry:
                save_to_json(db_entry)
                files_processed += 1

    print(f"[INFO] Processing complete. Total files processed: {files_processed}")

if __name__ == "__main__":
    process_all_files_in_directory()
