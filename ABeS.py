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

def load_settings():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if 'SETTINGS' not in config:
        config['SETTINGS'] = {
            'CALLSIGN': 'NOCALL',
            'PASSCODE': '00000',
            'LAT': '41.00000',
            'LON': '27.00000',
            'SYMBOL': 'r',
            'COMMENT': 'APRS Beacon',
            'INTERVAL': '1200'
        }
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    return config

def save_settings(callsign, passcode, lat, lon, symbol, comment, interval):
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
        'CALLSIGN': callsign,
        'PASSCODE': passcode,
        'LAT': lat,
        'LON': lon,
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

def send_aprs_packet(callsign, passcode, lat, lon, symbol, comment):
    lat_aprs = decimal_to_aprs(lat, True)
    lon_aprs = decimal_to_aprs(lon, False)
    timestamp = datetime.now(timezone.utc).strftime('%d%H%Mz')
    packet = f"{callsign}>APRS,TCPIP*,qAC,CWOP-6:@{timestamp}{lat_aprs}/{lon_aprs}{symbol}#{comment}"
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
    symbol = settings['SYMBOL']
    comment = settings['COMMENT']
    interval = int(settings['INTERVAL'])
    while running:
        send_aprs_packet(callsign, passcode, lat, lon, symbol, comment)
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
    # Create 64x64 px image with blue background and white "ABeS" text
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
    global root
    root.deiconify()

def on_closing():
    # Hide window instead of close
    root.withdraw()

def exit_program():
    stop_beacon()
    tray_icon.stop()
    root.destroy()
    sys.exit()

def save_and_start():
    callsign = entry_callsign.get().strip()
    passcode = entry_passcode.get().strip()
    lat = entry_lat.get().strip()
    lon = entry_lon.get().strip()
    symbol = entry_symbol.get().strip()
    comment = entry_comment.get().strip()
    try:
        interval = int(entry_interval.get().strip())
        if interval < 1200:
            messagebox.showerror("Error", "Interval cannot be less than 20 minutes (1200 seconds).")
            return
    except ValueError:
        messagebox.showerror("Error", "Interval must be a number.")
        return
    save_settings(callsign, passcode, lat, lon, symbol, comment, interval)
    start_beacon()
    root.withdraw()

def setup_tray():
    global tray_icon
    tray_icon = pystray.Icon(
        "abes",
        create_image(),
        title="ABeS - APRS Beacon Sender",
        menu=pystray.Menu(
            item("Settings", lambda: open_settings()),
            item("Stop", lambda: stop_beacon()),
            item("Exit", lambda: exit_program())
        )
    )
    tray_icon.run()

def setup_gui():
    global root, entry_callsign, entry_passcode, entry_lat, entry_lon, entry_symbol, entry_comment, entry_interval
    root = tk.Tk()
    root.title("ABeS - APRS Beacon Settings")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    settings = load_settings()['SETTINGS']

    tk.Label(root, text="Callsign:").grid(row=0, column=0, sticky='e')
    entry_callsign = tk.Entry(root)
    entry_callsign.insert(0, settings['CALLSIGN'])
    entry_callsign.grid(row=0, column=1)

    tk.Label(root, text="Passcode:").grid(row=1, column=0, sticky='e')
    entry_passcode = tk.Entry(root)
    entry_passcode.insert(0, settings['PASSCODE'])
    entry_passcode.grid(row=1, column=1)

    tk.Label(root, text="Latitude:").grid(row=2, column=0, sticky='e')
    entry_lat = tk.Entry(root)
    entry_lat.insert(0, settings['LAT'])
    entry_lat.grid(row=2, column=1)

    tk.Label(root, text="Longitude:").grid(row=3, column=0, sticky='e')
    entry_lon = tk.Entry(root)
    entry_lon.insert(0, settings['LON'])
    entry_lon.grid(row=3, column=1)

    tk.Label(root, text="Symbol:").grid(row=4, column=0, sticky='e')
    entry_symbol = tk.Entry(root)
    entry_symbol.insert(0, settings['SYMBOL'])
    entry_symbol.grid(row=4, column=1)

    tk.Label(root, text="Comment:").grid(row=5, column=0, sticky='e')
    entry_comment = tk.Entry(root)
    entry_comment.insert(0, settings['COMMENT'])
    entry_comment.grid(row=5, column=1)

    tk.Label(root, text="Interval (seconds):").grid(row=6, column=0, sticky='e')
    entry_interval = tk.Entry(root)
    entry_interval.insert(0, settings['INTERVAL'])
    entry_interval.grid(row=6, column=1)

    save_btn = tk.Button(root, text="Save and Start", command=save_and_start)
    save_btn.grid(row=7, column=0, columnspan=2)

def main():
    setup_gui()
    threading.Thread(target=setup_tray, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
