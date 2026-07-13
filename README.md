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
printing two lines per step over serial - the angle, then the distance:

```
90 degrees
23 cm
118 degrees
24 cm
...
```

`radar-gui` pairs each distance line with the angle line that preceded it -
see [`_parse_line`](src/radar_gui/serial_source.py). `--demo` mode has no
Arduino to read from, so it generates its own angle sequence by replaying the
sketch's 0->180->0 sweep - see
[`sweep_angles()`](src/radar_gui/models.py).

The sketch idles (servo parked, no sweeping) until it receives a `START`
command over serial, and stops as soon as it receives `STOP` - the GUI's
Start/Stop button sends these. There's no active buzzer on the instrument
anymore; proximity warnings are handled in software instead (see `--warn-sound`
below), since the buzzer could only vary its beep rate via a blocking
`delay()`, which made it sound like it was beeping constantly rather than
scaling smoothly with distance.

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

The radar starts idle. Click the **Start** button (or press `Space`) to tell
the Arduino to begin sweeping; click it again (or press `Space`) to stop.
Press `f` to toggle fullscreen. Click **Quit** (top-right), press `Esc`, or
close the window to exit - all three send `STOP` first if the Arduino is
still scanning, then shut everything down cleanly.

Add a software proximity warning through your Mac's speakers - beep tempo and
pitch step up as an object gets closer, instead of the instrument's old active
buzzer:

```bash
uv run radar-gui run --demo --warn-sound
```

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
| `--warn-range` | `40` | Distance in cm below which blips are highlighted red and the warning sound (if enabled) starts beeping. |
| `--width` / `--height` | `1000` / `720` | Window size in pixels. |
| `--fps` | `60` | Target frame rate. |
| `--fullscreen` | off | Start in fullscreen. |
| `--warn-sound` / `--no-warn-sound` | off | Play the proximity warning beep through this computer's speakers. |
| `--warn-volume` | `0.5` | Warning beep volume, `0.0`-`1.0`. |

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
  models.py               Reading data model + demo sweep-angle generator
  serial_source.py         Reads and parses live data from the Arduino, sends START/STOP
  demo_source.py            Generates simulated data for --demo, responds to START/STOP
  audio_warning.py           Synthesizes and plays the proximity warning beep
  display.py                  Pygame rendering: radar sweep + Start/Stop button
  app.py                       Wires a data source to the display and runs the main loop
  cli.py                        click command-line interface
tests/                    Unit tests for the parsing, sweep, and warning-zone logic
```
