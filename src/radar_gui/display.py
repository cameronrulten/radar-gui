from __future__ import annotations

import math
import time
from dataclasses import dataclass

import pygame

from .models import Reading

BG_COLOR = (4, 10, 7)
GRID_COLOR = (0, 90, 45)
GRID_LABEL_COLOR = (0, 140, 70)
SWEEP_COLOR = (80, 255, 140)
TEXT_COLOR = (110, 255, 160)
DIM_TEXT_COLOR = (0, 140, 70)
BLIP_COLOR = (120, 255, 160)
WARN_COLOR = (255, 90, 60)

TRAIL_DECAY = 6          # per-frame alpha subtraction, controls comet-tail length
BLIP_LIFETIME = 4.0      # seconds a detected blip stays visible before fading out
PANEL_HEIGHT = 112
MARGIN = 40
BUTTON_SIZE = (170, 40)
QUIT_BUTTON_SIZE = (90, 32)


@dataclass
class _Blip:
    x: float
    y: float
    distance: float
    warn: bool
    created_at: float


class RadarDisplay:
    """Renders sweep readings as a classic phosphor-green half-circle radar."""

    def __init__(
        self,
        width: int,
        height: int,
        max_range: float,
        warn_range: float,
        fps: int,
        fullscreen: bool,
        source_label: str,
    ) -> None:
        pygame.init()
        pygame.display.set_caption("SODAR - radar-gui")
        self._windowed_size = (width, height)
        self._fullscreen = False
        if fullscreen:
            self._enter_fullscreen()
        else:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.max_range = max_range
        self.warn_range = warn_range
        self.fps = fps
        self.source_label = source_label

        self.font = pygame.font.SysFont("Menlo,Consolas,Courier New,monospace", 16)
        self.font_small = pygame.font.SysFont("Menlo,Consolas,Courier New,monospace", 13)
        self.font_big = pygame.font.SysFont("Menlo,Consolas,Courier New,monospace", 22, bold=True)

        self.trail_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

        self.latest: Reading | None = None
        self.blips: list[_Blip] = []
        self.scanning = False
        self._recompute_geometry()

    def _recompute_geometry(self) -> None:
        width, height = self.screen.get_size()
        if self.trail_surface.get_size() != (width, height):
            self.trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.cx = width / 2
        self.cy = height - PANEL_HEIGHT - MARGIN
        self.radius = max(50.0, min((width - 2 * MARGIN) / 2, self.cy - MARGIN))

        panel_top = height - PANEL_HEIGHT
        button_width, button_height = BUTTON_SIZE
        self.button_rect = pygame.Rect(
            self.cx - button_width / 2,
            panel_top + (PANEL_HEIGHT - button_height) / 2,
            button_width,
            button_height,
        )

        quit_width, quit_height = QUIT_BUTTON_SIZE
        self.quit_button_rect = pygame.Rect(
            width - MARGIN - quit_width,
            MARGIN // 2 - 8,
            quit_width,
            quit_height,
        )

    def set_scanning(self, scanning: bool) -> None:
        self.scanning = scanning

    def handle_events(self) -> tuple[bool, bool]:
        """Processes pending window events.

        Returns (running, toggle_requested) - running is False when the app
        should quit, toggle_requested is True when the user clicked the
        Start/Stop button or pressed Space.
        """
        running = True
        toggle_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not self._fullscreen:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self._recompute_geometry()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_SPACE:
                    toggle_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.button_rect.collidepoint(event.pos):
                    toggle_requested = True
                elif self.quit_button_rect.collidepoint(event.pos):
                    running = False
        return running, toggle_requested

    def _toggle_fullscreen(self) -> None:
        if self._fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()
        self._recompute_geometry()

    def _enter_fullscreen(self) -> None:
        # A real exclusive display-mode switch (pygame.FULLSCREEN) is flaky
        # under SDL2 on macOS, especially on Retina displays - it can leave a
        # black window or silently fail to resize. A borderless window sized
        # to the desktop resolution is the reliable equivalent and avoids a
        # mode switch entirely.
        if not self._fullscreen:
            self._windowed_size = self.screen.get_size()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        self._fullscreen = True

    def _exit_fullscreen(self) -> None:
        self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        self._fullscreen = False

    def update(self, reading: Reading | None) -> None:
        if reading is None:
            return
        self.latest = reading
        if reading.distance <= self.max_range:
            x, y = self._point_for(reading.angle, reading.distance)
            self.blips.append(
                _Blip(
                    x=x,
                    y=y,
                    distance=reading.distance,
                    warn=reading.distance < self.warn_range,
                    created_at=reading.timestamp,
                )
            )
        now = time.monotonic()
        self.blips = [b for b in self.blips if now - b.created_at < BLIP_LIFETIME]

    def _point_for(self, angle: float, distance: float) -> tuple[float, float]:
        frac = min(distance, self.max_range) / self.max_range
        rad = math.radians(angle)
        x = self.cx + frac * self.radius * math.cos(rad)
        y = self.cy - frac * self.radius * math.sin(rad)
        return x, y

    def render(self) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        self._draw_trail()
        self._draw_blips()
        self._draw_panel()
        self._draw_button()
        self._draw_quit_button()
        pygame.display.flip()
        self.clock.tick(self.fps)

    def _draw_grid(self) -> None:
        for i in range(1, 5):
            r = self.radius * i / 4
            points = [
                (
                    self.cx + r * math.cos(math.radians(a)),
                    self.cy - r * math.sin(math.radians(a)),
                )
                for a in range(0, 181, 2)
            ]
            pygame.draw.lines(self.screen, GRID_COLOR, False, points, 1)
            label_distance = self.max_range * i / 4
            label = self.font_small.render(f"{label_distance:.0f}cm", True, GRID_LABEL_COLOR)
            lx = self.cx + r * math.cos(math.radians(20)) + 4
            ly = self.cy - r * math.sin(math.radians(20))
            self.screen.blit(label, (lx, ly))

        for a in range(0, 181, 30):
            x, y = self._point_for(a, self.max_range)
            pygame.draw.line(self.screen, GRID_COLOR, (self.cx, self.cy), (x, y), 1)
            lx = self.cx + (self.radius + 18) * math.cos(math.radians(a))
            ly = self.cy - (self.radius + 18) * math.sin(math.radians(a))
            label = self.font_small.render(f"{a}", True, GRID_LABEL_COLOR)
            rect = label.get_rect(center=(lx, ly))
            self.screen.blit(label, rect)

        pygame.draw.line(
            self.screen, GRID_COLOR, (self.cx - self.radius, self.cy), (self.cx + self.radius, self.cy), 1
        )

    def _draw_trail(self) -> None:
        self.trail_surface.fill((0, 0, 0, TRAIL_DECAY), special_flags=pygame.BLEND_RGBA_SUB)
        if self.latest is not None:
            x, y = self._point_for(self.latest.angle, self.max_range)
            pygame.draw.line(self.trail_surface, (*SWEEP_COLOR, 255), (self.cx, self.cy), (x, y), 3)
        self.screen.blit(self.trail_surface, (0, 0))

    def _draw_blips(self) -> None:
        now = time.monotonic()
        for blip in self.blips:
            age = now - blip.created_at
            alpha = max(0, int(255 * (1 - age / BLIP_LIFETIME)))
            color = WARN_COLOR if blip.warn else BLIP_COLOR
            surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (5, 5), 4)
            self.screen.blit(surf, (blip.x - 5, blip.y - 5))

    def _draw_panel(self) -> None:
        width, height = self.screen.get_size()
        panel_top = height - PANEL_HEIGHT
        pygame.draw.line(self.screen, GRID_COLOR, (0, panel_top), (width, panel_top), 1)

        title = self.font_big.render("SODAR", True, TEXT_COLOR)
        self.screen.blit(title, (MARGIN, MARGIN // 2 - 8))

        state_text = "STATE  SCANNING" if self.scanning else "STATE  STOPPED"
        state_color = TEXT_COLOR if self.scanning else DIM_TEXT_COLOR

        if self.latest is not None:
            angle_text = f"ANGLE  {self.latest.angle:>3}deg"
            distance_text = f"RANGE  {self.latest.distance:>6.1f}cm"
            in_range = self.latest.distance <= self.max_range
            status_text = "TRACKING" if not in_range else (
                "*** OBJECT CLOSE ***" if self.latest.distance < self.warn_range else "clear"
            )
            status_color = WARN_COLOR if (in_range and self.latest.distance < self.warn_range) else TEXT_COLOR
        else:
            angle_text = "ANGLE  ---"
            distance_text = "RANGE  ---"
            status_text = "waiting for data..."
            status_color = DIM_TEXT_COLOR

        lines = [
            (state_text, state_color),
            (angle_text, TEXT_COLOR),
            (distance_text, TEXT_COLOR),
            (status_text, status_color),
        ]
        for i, (text, color) in enumerate(lines):
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (MARGIN, panel_top + 10 + i * 20))

        meta_lines = [
            f"SOURCE  {self.source_label}",
            f"MAX RANGE  {self.max_range:.0f}cm   WARN  {self.warn_range:.0f}cm",
            f"FPS  {self.clock.get_fps():.0f}",
        ]
        for i, text in enumerate(meta_lines):
            surf = self.font_small.render(text, True, DIM_TEXT_COLOR)
            rect = surf.get_rect()
            self.screen.blit(surf, (width - rect.width - MARGIN, panel_top + 10 + i * 20))

    def _draw_button(self) -> None:
        if self.scanning:
            fill_color = (50, 15, 15)
            border_color = WARN_COLOR
            label = "STOP  (space)"
        else:
            fill_color = (10, 40, 20)
            border_color = SWEEP_COLOR
            label = "START  (space)"
        pygame.draw.rect(self.screen, fill_color, self.button_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, self.button_rect, width=2, border_radius=6)
        text = self.font.render(label, True, border_color)
        self.screen.blit(text, text.get_rect(center=self.button_rect.center))

    def _draw_quit_button(self) -> None:
        pygame.draw.rect(self.screen, (50, 15, 15), self.quit_button_rect, border_radius=6)
        pygame.draw.rect(self.screen, WARN_COLOR, self.quit_button_rect, width=2, border_radius=6)
        text = self.font_small.render("QUIT", True, WARN_COLOR)
        self.screen.blit(text, text.get_rect(center=self.quit_button_rect.center))

    def quit(self) -> None:
        pygame.quit()
