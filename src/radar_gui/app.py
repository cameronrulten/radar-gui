from __future__ import annotations

from queue import Empty, Queue

import pygame

from .audio_warning import ProximityWarning
from .demo_source import DemoSource
from .display import RadarDisplay
from .models import Reading
from .serial_source import SerialSource

MAX_READINGS_PER_FRAME = 20


def run_app(
    *,
    port: str | None,
    baud: int,
    demo: bool,
    max_range: float,
    warn_range: float,
    width: int,
    height: int,
    fps: int,
    fullscreen: bool,
    warn_sound: bool,
    warn_volume: float,
) -> None:
    queue: "Queue[Reading]" = Queue(maxsize=1000)

    if demo:
        source = DemoSource(max_range=max_range)
        source_label = "DEMO"
    else:
        assert port is not None
        source = SerialSource(port=port, baudrate=baud)
        source_label = f"{port} @ {baud}"

    if warn_sound:
        # Must happen before pygame.init() (called inside RadarDisplay) to
        # take effect, so the mixer format matches what ProximityWarning
        # synthesizes its beeps at.
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
        proximity = ProximityWarning(warn_range=warn_range, volume=warn_volume)
    else:
        proximity = None

    source.start(queue)

    display = RadarDisplay(
        width=width,
        height=height,
        max_range=max_range,
        warn_range=warn_range,
        fps=fps,
        fullscreen=fullscreen,
        source_label=source_label,
    )

    scanning = False
    current_distance: float | None = None

    try:
        running = True
        while running:
            running, toggle_requested = display.handle_events()
            if toggle_requested:
                scanning = not scanning
                source.send_command("START" if scanning else "STOP")
            display.set_scanning(scanning)

            latest: Reading | None = None
            for _ in range(MAX_READINGS_PER_FRAME):
                try:
                    latest = queue.get_nowait()
                except Empty:
                    break
            if latest is not None:
                current_distance = latest.distance

            display.update(latest)
            if proximity is not None and current_distance is not None:
                proximity.update(current_distance, scanning)
            display.render()
    finally:
        source.stop()
        display.quit()
