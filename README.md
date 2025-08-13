# ABeS APRS Beacon Sender

ABeS (APRS Beacon Sender) is a lightweight Python application that periodically sends APRS position beacons to the APRS network via TCP/IP. It runs quietly in the system tray and allows configuration of callsign, passcode, beacon interval, and other settings.

This project is created with respect and gratitude to Bob Bruninga (WB4APR), the founder of APRS, whose vision and work laid the foundation for amateur radio digital communications.

## Features

- Sends APRS position packets with custom callsign and passcode  
- Runs in system tray with icon and menu  
- Configurable beacon interval with a **minimum of 5 minutes** to avoid overloading APRS servers  
- Save settings to `settings.ini`  
- Cross-platform support (Windows and Linux)

## Installation

### Windows
1. Download and extract the ZIP file.
2. Run the included `ABeS.exe`.
3. On first launch, enter your callsign, passcode, location, and other settings.
4. Click **Start**.

**Optional: Automatic Startup**

**Method 1 – Startup Folder**
1. Right-click `ABeS.exe` → **Create shortcut**.
2. Move the shortcut to:
```bash
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```
**Method 2 – Task Scheduler**
1. Open **Task Scheduler** from the Start menu.
2. Create a **Basic Task**, name it `ABeS Beacon`.
3. Trigger: “At log on” or “At startup”.
4. Action: “Start a program” → select `ABeS_.exe`.
5. Save and test.
---
### Linux
1. Make sure Python 3 is installed.
2. Make the script executable:
```bash
chmod +x /path/to/ABeS.py
```
3. Install required packages:

```bash
pip install pystray Pillow
```
4. Run the application:
```bash
./ABeS_.py
```
---
**Optional: Automatic Startup with systemd**

1. Create a service file:

```bash
nano ~/.config/systemd/user/abes.service
```
2. Paste the following:

```bash
[Unit]
Description=ABeS APRS Beacon

[Service]
ExecStart=/usr/bin/python3 /path/to/ABeS.py
Restart=always

[Install]
WantedBy=default.target

3. Enable and start the service:
```
```bash
systemctl --user enable abes.service
systemctl --user start abes.service
```
## Usage 

The program runs in the system tray after start.

Left-click to open settings and right-click the tray icon to access settings or exit.

Settings window allows you to change:

Callsign

Passcode

Longitude

Latitude

Aprs Symbol (both primary and secondary tables)

Beacon interval **(minimum 5 minutes)**

## Screenshot of GUI
<img width="378" height="354" alt="image" src="https://github.com/user-attachments/assets/51f4a2b2-0b94-42f6-831e-fff940f43bc7" />

## License

Project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Executable files (`.exe`) are not included in the repository but can be found in the Releases section.

---

Feel free to contribute or report issues!

---

*Created by Ercan Olcay*
**ercan@ercanolcay.com**
