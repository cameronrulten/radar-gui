from __future__ import annotations

import sys

import click
import serial.tools.list_ports

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="radar-gui")
def cli() -> None:
    """A retro green sweeping radar display for an Arduino ultrasonic SODAR station."""


@cli.command("list-ports")
def list_ports() -> None:
    """List serial ports currently visible to this Mac."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        click.echo("No serial ports found. Is the Arduino plugged in?")
        return
    for p in ports:
        click.echo(f"{p.device}  -  {p.description}")


@cli.command("run")
@click.option(
    "--port",
    "-p",
    default=None,
    help="Serial port the Arduino is connected to, e.g. /dev/tty.usbmodem1101. "
    "Run 'radar-gui list-ports' to see what's available. Not needed with --demo.",
)
@click.option(
    "--baud",
    "-b",
    default=9600,
    show_default=True,
    help="Serial baud rate. Must match Serial.begin() in the sketch.",
)
@click.option(
    "--demo",
    is_flag=True,
    default=False,
    help="Run with simulated sweep data, no Arduino required.",
)
@click.option(
    "--max-range",
    default=300.0,
    show_default=True,
    help="Maximum sensor range in cm - sets the outer radar ring.",
)
@click.option(
    "--warn-range",
    default=40.0,
    show_default=True,
    help="Distance in cm below which blips are flagged as close "
    "(matches the sketch's buzzer threshold).",
)
@click.option("--width", default=1000, show_default=True, help="Window width in pixels.")
@click.option("--height", default=720, show_default=True, help="Window height in pixels.")
@click.option("--fps", default=60, show_default=True, help="Target frames per second.")
@click.option("--fullscreen", is_flag=True, default=False, help="Launch in fullscreen mode.")
def run(
    port: str | None,
    baud: int,
    demo: bool,
    max_range: float,
    warn_range: float,
    width: int,
    height: int,
    fps: int,
    fullscreen: bool,
) -> None:
    """Launch the radar GUI."""
    if not demo and not port:
        raise click.UsageError(
            "--port is required unless --demo is set. Run 'radar-gui list-ports' to see "
            "available ports."
        )

    # Imported lazily so 'radar-gui --help' / 'list-ports' stay fast and don't
    # need a display driver available (e.g. in CI or over SSH).
    from .app import run_app

    try:
        run_app(
            port=port,
            baud=baud,
            demo=demo,
            max_range=max_range,
            warn_range=warn_range,
            width=width,
            height=height,
            fps=fps,
            fullscreen=fullscreen,
        )
    except KeyboardInterrupt:
        click.echo("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    cli()
