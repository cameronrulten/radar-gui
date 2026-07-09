from __future__ import annotations

from queue import Empty, Queue

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
) -> None:
    queue: "Queue[Reading]" = Queue(maxsize=1000)

    if demo:
        source = DemoSource(max_range=max_range)
        source_label = "DEMO"
    else:
        assert port is not None
        source = SerialSource(port=port, baudrate=baud)
        source_label = f"{port} @ {baud}"

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

    try:
        running = True
        while running:
            running = display.handle_events()

            latest: Reading | None = None
            for _ in range(MAX_READINGS_PER_FRAME):
                try:
                    latest = queue.get_nowait()
                except Empty:
                    break

            display.update(latest)
            display.render()
    finally:
        source.stop()
        display.quit()
