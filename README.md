# X-Rite 310 Densitometer Interface

A cross-platform Python application to communicate with an **X-Rite 310** densitometer (models 310T or 310TR), enabling data acquisition, analysis, and graphical visualization of density measurements.

## Key Features

- Serial connection to the X-Rite 310 densitometer
- Automatic acquisition of 21-point density readings
- Real-time visualization of density curves (VIS, R, G, B)
- Overlay of reference and measured curves
- History tracking of measurements (average, D-min, D-max, gamma evolution)
- Built-in markdown document viewer (manual, notes, etc.)

---

## Requirements

- **Python 3.9 or 3.10 (64-bit)**
- A serial port (RS-232 or USB/serial adapter) to connect the densitometer
- Windows or macOS

---

## Installation

1. **Download the project archive**
2. **Install 64-bit Python** if not already installed:  
   [https://www.python.org/downloads/](https://www.python.org/downloads/)
3. **Open a terminal:**

### On **Windows**:

Double-click `install.bat`  
*(or right-click > Run as administrator)*

### On **macOS / Linux**:

```bash
chmod +x install.sh
./install.sh
```

---

## Launch the Application

```bash
python main.py
```

or, if required:

```bash
python3 main.py
```

---

## Python Dependencies

- `PySide6` (GUI with Qt6)
- `matplotlib` (graph plotting)
- `numpy` (math and array handling)
- `pyserial` (serial communication)
- `markdown` (HTML rendering for help and manuals)

---

## Troubleshooting

- Make sure you are using **64-bit Python**.
- If the app fails to launch or shows an empty window, verify that the densitometer is connected and detected (correct serial port).
- If `QWebEngineView` fails, ensure your Python environment includes a compatible `PySide6` build with WebEngine support.

---

## References

- [X-Rite 310 User Manual (PDF)](docs/310-42_310_Densitometer_Operation_Manual_en.pdf)
- ASCII serial communication protocol documented in Chapter 3 of the manual
