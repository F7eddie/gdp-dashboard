import streamlit as st
import pygame
import math
import random
import sys

# ---------------- SETTINGS ---------------- #
DOT_SIZE = 10
GAP = 30
BASE_COLOR = (82, 39, 255)
ACTIVE_COLOR = (255, 255, 255)
PROXIMITY = 50
SPEED_TRIGGER = 100
SHOCK_RADIUS = 250
SHOCK_STRENGTH = 5
MAX_SPEED = 5000
RESISTANCE = 750
RETURN_DURATION = 1.5
FPS = 180
FULLSCREEN = False  # set True for fullscreen
# ------------------------------------------- #

pygame.init()
screen = pygame.display.set_mode(
    (0, 0), pygame.FULLSCREEN if FULLSCREEN else 0
)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

# -------------------------------------------------------
# DOT CLASS
# -------------------------------------------------------
class Dot:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.x_offset = 0
        self.y_offset = 0
        self.vx = 0
        self.vy = 0
        self.color = BASE_COLOR
        self._inertia_applied = False
        self.return_timer = 0

    def update(self, dt, pointer):
        # Distance to pointer
        dx = self.cx - pointer.x
        dy = self.cy - pointer.y
        dist_sq = dx * dx + dy * dy

        # Color interpolation
        if dist_sq <= PROXIMITY ** 2:
            dist = math.sqrt(dist_sq)
            t = 1 - dist / PROXIMITY
            r = int(BASE_COLOR[0] + (ACTIVE_COLOR[0] - BASE_COLOR[0]) * t)
            g = int(BASE_COLOR[1] + (ACTIVE_COLOR[1] - BASE_COLOR[1]) * t)
            b = int(BASE_COLOR[2] + (ACTIVE_COLOR[2] - BASE_COLOR[2]) * t)
            self.color = (r, g, b)
        else:
            self.color = BASE_COLOR

        # Update velocity with resistance
        self.vx *= 1 - dt * (RESISTANCE / 5000)
        self.vy *= 1 - dt * (RESISTANCE / 5000)

        # Move
        self.x_offset += self.vx * dt
        self.y_offset += self.vy * dt

        # Return motion if inactive
        if abs(self.x_offset) > 0.1 or abs(self.y_offset) > 0.1:
            self.x_offset -= self.x_offset * dt * 2
            self.y_offset -= self.y_offset * dt * 2
        else:
            self.x_offset = self.y_offset = 0

    def draw(self, surface):
        x = int(self.cx + self.x_offset)
        y = int(self.cy + self.y_offset)
        pygame.draw.circle(surface, self.color, (x, y), DOT_SIZE // 2)

# -------------------------------------------------------
# POINTER (MOUSE) STATE
# -------------------------------------------------------
class Pointer:
    def __init__(self):
        self.x, self.y = 0, 0
        self.vx, self.vy = 0, 0
        self.speed = 0
        self.last_x, self.last_y = 0, 0
        self.last_time = 0

    def update(self, x, y, dt):
        self.vx = (x - self.last_x) / dt if dt > 0 else 0
        self.vy = (y - self.last_y) / dt if dt > 0 else 0
        self.speed = math.hypot(self.vx, self.vy)
        if self.speed > MAX_SPEED:
            scale = MAX_SPEED / self.speed
            self.vx *= scale
            self.vy *= scale
            self.speed = MAX_SPEED
        self.last_x, self.last_y = x, y
        self.x, self.y = x, y

# -------------------------------------------------------
# BUILD DOT GRID
# -------------------------------------------------------
def build_grid():
    dots = []
    cols = int((WIDTH + GAP) / (DOT_SIZE + GAP))
    rows = int((HEIGHT + GAP) / (DOT_SIZE + GAP))
    cell = DOT_SIZE + GAP
    grid_w = cell * cols - GAP
    grid_h = cell * rows - GAP
    start_x = (WIDTH - grid_w) / 2 + DOT_SIZE / 2
    start_y = (HEIGHT - grid_h) / 2 + DOT_SIZE / 2
    for y in range(rows):
        for x in range(cols):
            dots.append(Dot(start_x + x * cell, start_y + y * cell))
    return dots

dots = build_grid()
pointer = Pointer()

# -------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for dot in dots:
                dx = dot.cx - mx
                dy = dot.cy - my
                dist = math.hypot(dx, dy)
                if dist < SHOCK_RADIUS and not dot._inertia_applied:
                    dot._inertia_applied = True
                    falloff = max(0, 1 - dist / SHOCK_RADIUS)
                    push_x = dx * SHOCK_STRENGTH * falloff
                    push_y = dy * SHOCK_STRENGTH * falloff
                    dot.vx += push_x
                    dot.vy += push_y
                    dot._inertia_applied = False

    # Update pointer & apply forces
    mx, my = pygame.mouse.get_pos()
    pointer.update(mx, my, dt)
    for dot in dots:
        # Trigger movement when fast
        dist = math.hypot(dot.cx - pointer.x, dot.cy - pointer.y)
        if pointer.speed > SPEED_TRIGGER and dist < PROXIMITY and not dot._inertia_applied:
            dot._inertia_applied = True
            push_x = (dot.cx - pointer.x) + pointer.vx * 0.005
            push_y = (dot.cy - pointer.y) + pointer.vy * 0.005
            dot.vx += push_x
            dot.vy += push_y
            dot._inertia_applied = False
        dot.update(dt, pointer)
        dot.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
