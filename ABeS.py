import sys
import threading
import time
import configparser
import socket
from datetime import datetime, timezone

import tkinter as tk
from tkinter import messagebox
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont

CONFIG_FILE = "settings.ini"
running = False
beacon_thread = None
tray_icon = None
root = None

# -------------------- PASSCODE ALGORITHM --------------------
# Local Passcode Control
def _aprs_base_callsign(callsign: str) -> str:
    """Remove SSID, Make all letters capital."""
    if not callsign:
        return ""
    return callsign.split('-')[0].strip().upper()

def compute_passcode(callsign: str) -> int: 
    cs = _aprs_base_callsign(callsign)
    h = 0x73E2
    for i, ch in enumerate(cs):
        if i % 2 == 0:
            h ^= (ord(ch) << 8)
        else:
            h ^= ord(ch)
    return h & 0x7FFF

def verify_passcode(callsign: str, passcode: str) -> bool:
    try:
        return int(passcode) == compute_passcode(callsign)
    except Exception:
        return False
# -------------------------------------------------------------

def load_settings():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'SETTINGS' not in config:
        config['SETTINGS'] = {
            'CALLSIGN': 'NOCALL',
            'PASSCODE': '00000',
            'LAT': '41.00000',
            'LON': '27.00000',
            'TABLE': '/',
            'SYMBOL': 'r',
            'COMMENT': 'APRS Beacon',
            'INTERVAL': '1200'
        }
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    return config

def save_settings(callsign, passcode, lat, lon, table, symbol, comment, interval):
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
        'CALLSIGN': callsign,
        'PASSCODE': passcode,
        'LAT': lat,
        'LON': lon,
        'TABLE': table,
        'SYMBOL': symbol,
        'COMMENT': comment,
        'INTERVAL': str(interval)
    }
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

def decimal_to_aprs(value, is_latitude=True):
    if is_latitude:
        direction = 'N' if value >= 0 else 'S'
    else:
        direction = 'E' if value >= 0 else 'W'
    abs_val = abs(value)
    degrees = int(abs_val)
    minutes = (abs_val - degrees) * 60
    if is_latitude:
        return f"{degrees:02d}{minutes:05.2f}{direction}"
    else:
        return f"{degrees:03d}{minutes:05.2f}{direction}"

def send_aprs_packet(callsign, passcode, lat, lon, table, symbol, comment):
    lat_aprs = decimal_to_aprs(lat, True)
    lon_aprs = decimal_to_aprs(lon, False)
    timestamp = datetime.now(timezone.utc).strftime('%d%H%Mz')
    packet = f"{callsign}>APRS,TCPIP*,qAC,CWOP-6:@{timestamp}{lat_aprs}{table}{lon_aprs}{symbol}{comment}"
    try:
        s = socket.socket()
        s.settimeout(10)
        s.connect(('rotate.aprs2.net', 14580))
        s.send(f"user {callsign} pass {passcode} vers aprs_simple 1.0\n".encode())
        s.send((packet + "\n").encode())
        s.close()
        print(f"{datetime.now()} - Beacon sent: {packet}")
    except Exception as e:
        print(f"{datetime.now()} - Send error: {e}")

def beacon_loop():
    global running
    settings = load_settings()['SETTINGS']
    callsign = settings['CALLSIGN']
    passcode = settings['PASSCODE']
    lat = float(settings['LAT'])
    lon = float(settings['LON'])
    table = settings['TABLE']
    symbol = settings['SYMBOL']
    comment = settings['COMMENT']
    interval = int(settings['INTERVAL'])
    while running:
        send_aprs_packet(callsign, passcode, lat, lon, table, symbol, comment)
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)

def start_beacon():
    global running, beacon_thread
    if not running:
        running = True
        beacon_thread = threading.Thread(target=beacon_loop, daemon=True)
        beacon_thread.start()
        print("Beacon started.")

def stop_beacon():
    global running
    running = False
    print("Beacon stopped.")

def create_image():
    image = Image.new('RGBA', (64, 64), (0, 120, 255, 255))
    dc = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        font = ImageFont.load_default()
    text = "ABeS"
    bbox = dc.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (64 - w) // 2
    y = (64 - h) // 2
    dc.text((x, y), text, fill="white", font=font)
    return image

def open_settings():
    if root:
        root.after(0, lambda: (root.deiconify(), root.lift(), root.focus_force()))

def on_closing():
    root.withdraw()

def exit_program():
    stop_beacon()
    try:
        if tray_icon:
            tray_icon.stop()
    except Exception:
        pass
    root.destroy()
    sys.exit()

def save_and_start():
    callsign = entry_callsign.get().strip()
    passcode = entry_passcode.get().strip()
    
    if not verify_passcode(callsign, passcode):
        messagebox.showerror("Error", "Passcode is invalid for the given callsign!")
        return
    
    lat = entry_lat.get().strip()
    lon = entry_lon.get().strip()
    table = table_var.get()
    symbol = entry_symbol.get().strip()
    comment = entry_comment.get().strip()
    try:
        interval = int(entry_interval.get().strip())
        if interval < 300:
            messagebox.showerror("Error", "Interval cannot be less than 5 minutes (300 seconds).")
            return
    except ValueError:
        messagebox.showerror("Error", "Interval must be a number.")
        return
    if len(symbol) != 1:
        messagebox.showerror("Error", "Symbol must be a single character!")
        return
    save_settings(callsign, passcode, lat, lon, table, symbol, comment, interval)
    start_beacon()
    root.withdraw()

def setup_tray():
    global tray_icon
    tray_icon = pystray.Icon(
        "abes",
        create_image(),
        title="ABeS APRS BEACON SENDER",
        menu=pystray.Menu(
            item("Settings", open_settings, default=True),
            item("Stop", stop_beacon),
            item("Exit", exit_program)
        )
    )
    tray_icon.run()

def setup_gui():
    global root, entry_callsign, entry_passcode, entry_lat, entry_lon, entry_symbol, entry_comment, entry_interval, table_var
    root = tk.Tk()
    root.title("ABeS")
    root.configure(bg="black")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    WIDTH, HEIGHT = 300, 250
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.resizable(False, False)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - WIDTH) // 2
    y = (root.winfo_screenheight() - HEIGHT) // 2
    root.geometry(f"+{x}+{y}")

    settings = load_settings()['SETTINGS']

    tk.Label(root, text="ABeS APRS BEACON SENDER",
             bg="black", fg="white",
             font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(6, 10), sticky='w', padx=10)

    tk.Label(root, text="Callsign:", bg="black", fg="white").grid(row=1, column=0, sticky='w', padx=10)
    entry_callsign = tk.Entry(root)
    entry_callsign.insert(0, settings['CALLSIGN'])
    entry_callsign.grid(row=1, column=1, sticky='w', padx=10)

    tk.Label(root, text="Passcode:", bg="black", fg="white").grid(row=2, column=0, sticky='w', padx=10)
    entry_passcode = tk.Entry(root, show="*")
    entry_passcode.insert(0, settings['PASSCODE'])
    entry_passcode.grid(row=2, column=1, sticky='w', padx=10)

    tk.Label(root, text="Latitude:", bg="black", fg="white").grid(row=3, column=0, sticky='w', padx=10)
    entry_lat = tk.Entry(root)
    entry_lat.insert(0, settings['LAT'])
    entry_lat.grid(row=3, column=1, sticky='w', padx=10)

    tk.Label(root, text="Longitude:", bg="black", fg="white").grid(row=4, column=0, sticky='w', padx=10)
    entry_lon = tk.Entry(root)
    entry_lon.insert(0, settings['LON'])
    entry_lon.grid(row=4, column=1, sticky='w', padx=10)

    ts_frame = tk.Frame(root, bg="black")
    ts_frame.grid(row=5, column=0, columnspan=2, pady=4, sticky='w', padx=10)

    tk.Label(ts_frame, text="Table:", bg="black", fg="white").pack(side="left")
    table_var = tk.StringVar()
    table_var.set(settings.get('TABLE', '/'))
    table_menu = tk.OptionMenu(ts_frame, table_var, "/", "\\")
    table_menu.pack(side="left", padx=(6, 20))

    tk.Label(ts_frame, text="Symbol:", bg="black", fg="white").pack(side="left")
    entry_symbol = tk.Entry(ts_frame, width=3)
    entry_symbol.insert(0, settings.get('SYMBOL', 'r'))
    entry_symbol.pack(side="left", padx=(6, 0))

    def limit_symbol_char(event):
        value = entry_symbol.get()
        if len(value) > 1:
            entry_symbol.delete(1, tk.END)
    entry_symbol.bind("<KeyRelease>", limit_symbol_char)

    tk.Label(root, text="Comment:", bg="black", fg="white").grid(row=6, column=0, sticky='w', padx=10)
    entry_comment = tk.Entry(root, width=28)
    entry_comment.insert(0, settings['COMMENT'])
    entry_comment.grid(row=6, column=1, sticky='w', padx=10)

    tk.Label(root, text="Interval (seconds):", bg="black", fg="white").grid(row=7, column=0, sticky='w', padx=10)
    entry_interval = tk.Entry(root)
    entry_interval.insert(0, settings['INTERVAL'])
    entry_interval.grid(row=7, column=1, sticky='w', padx=10)

    btn_frame = tk.Frame(root, bg="black")
    btn_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky='w', padx=10)

    save_btn = tk.Button(btn_frame, text="Start", command=save_and_start, bg="green", fg="white", width=8)
    save_btn.pack(side="left", padx=5)

    stop_btn = tk.Button(btn_frame, text="Stop", command=stop_beacon, bg="red", fg="white", width=8)
    stop_btn.pack(side="left", padx=5)

    exit_btn = tk.Button(btn_frame, text="Exit", command=exit_program, bg="gray", fg="white", width=8)
    exit_btn.pack(side="left", padx=5)

def main():
    setup_gui()
    threading.Thread(target=setup_tray, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
