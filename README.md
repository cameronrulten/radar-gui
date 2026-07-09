# radar-gui

A retro, phosphor-green sweeping radar display for a homemade ultrasonic SODAR
station (Elegoo Mega + HC-SR04 + SG90 servo). It's not actually a radar - it's
a **S**ound-based **O**bject **D**etection **A**nd **R**anging rig - but it's
drawn to look like one anyway.

This replaces the Java `SodarExampleGUI` shown in a lot of Arduino radar
tutorials with a Python GUI that talks to the same kind of sweep hardware.

![status](https://img.shields.io/badge/status-experimental-orange)

## How it works

The Arduino sketch in [`arduino/my_custom_radar.ino`](arduino/my_custom_radar.ino)
sweeps an HC-SR04 ultrasonic sensor on a servo from 0deg to 180deg and back,
printing only the distance for each step over serial, e.g.:

```
23cm
24cm
118cm
...
```

It does **not** send the servo angle. `radar-gui` reconstructs the angle on
the Python side by replaying the exact same 0->180->0 sweep sequence the
sketch's servo loop follows, one step per line received - see
[`src/radar_gui/models.py`](src/radar_gui/models.py). If you change the
sketch's sweep logic, update `sweep_angles()` to match.

## Requirements

- macOS (tested on a MacBook Pro, Apple Silicon)
- [uv](https://docs.astral.sh/uv/) for Python and dependency management
- An Elegoo Mega (or similar Arduino-compatible board) running
  `arduino/my_custom_radar.ino`, connected over USB

You don't need the hardware to try the GUI - see `--demo` below.

## Setup

Clone the repo, then let `uv` create the virtual environment and install
everything (including a matching Python 3.11+ interpreter, if you don't
already have one):

```bash
git clone https://github.com/cameronrulten/radar-gui.git
cd radar-gui
uv sync
```

This creates a `.venv/` in the project directory. You don't need to activate
it - `uv run` uses it automatically.

## Usage

Try it without any hardware attached:

```bash
uv run radar-gui run --demo
```

With the Arduino plugged in, find its serial port:

```bash
uv run radar-gui list-ports
```

On macOS this is usually something like `/dev/cu.usbmodemXXXX` or
`/dev/cu.wchusbserialXXXX` (the Elegoo Mega's CH340 chip tends to show up as
the latter). Then run:

```bash
uv run radar-gui run --port /dev/cu.wchusbserial1101
```

Press `f` to toggle fullscreen, `Esc` or close the window to quit.

### Options

```
uv run radar-gui run --help
```

| Option | Default | Description |
| --- | --- | --- |
| `--port`, `-p` | - | Serial port the Arduino is on. Required unless `--demo`. |
| `--baud`, `-b` | `9600` | Must match `Serial.begin()` in the sketch. |
| `--demo` | off | Simulate sweep data instead of reading from hardware. |
| `--max-range` | `300` | Outer ring distance in cm. |
| `--warn-range` | `40` | Distance in cm below which blips are highlighted red (matches the sketch's buzzer threshold). |
| `--width` / `--height` | `1000` / `720` | Window size in pixels. |
| `--fps` | `60` | Target frame rate. |
| `--fullscreen` | off | Start in fullscreen. |

## Development

`uv sync` installs the `dev` dependency group (pytest, ruff) by default:

```bash
uv run pytest
uv run ruff check .
```

## Project layout

```
arduino/                 Arduino sketch running on the Elegoo Mega
src/radar_gui/
  models.py               Reading data model + sweep-angle reconstruction
  serial_source.py         Reads and parses live data from the Arduino
  demo_source.py            Generates simulated data for --demo
  display.py                 Pygame rendering of the radar sweep
  app.py                      Wires a data source to the display and runs the main loop
  cli.py                       click command-line interface
tests/                    Unit tests for the parsing and sweep logic
```
