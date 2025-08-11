# ABeS APRS Beacon Sender

ABeS (APRS Beacon Sender) is a lightweight Python application that periodically sends APRS position beacons to the APRS network via TCP/IP. It runs quietly in the system tray and allows configuration of callsign, passcode, beacon interval, and other settings.

This project is created with respect and gratitude to Bob Bruninga (WB4APR), the founder of APRS, whose vision and work laid the foundation for amateur radio digital communications.

## Features

- Sends APRS position packets with custom callsign and passcode  
- Runs in system tray with icon and menu  
- Configurable beacon interval with a **minimum of 20 minutes** to avoid overloading APRS servers  
- Save settings to `settings.ini`  
- Cross-platform support (Windows and Linux)

## Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/ercanolcay/ABeS.git

2. Install required Python packages:
   ```bash
   pip install pystray pillow

4. Run the application:
   ```bash
   python abes.py

## Usage

The program runs in the system tray after start.

Right-click the tray icon to access settings or exit.

Settings window allows you to change:

Callsign

Passcode

Longitude

Latitude

Beacon interval **(minimum 20 minutes)**

## Building Executable

To create a standalone executable (Windows):
```bash
pyinstaller --onefile --windowed --icon=abes.ico abes.py
```
## License

his project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Executable files (`.exe`) are not included in the repository but can be found in the Releases section.

---

Feel free to contribute or report issues!

---

*Created by Ercan Olcay*
