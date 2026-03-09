"""
Monk & Demon River Crossing Puzzle
====================================
Get 3 monks and 3 demons safely across the river.
Rules:
  - The boat holds at most 2 people.
  - At least 1 person must be in the boat to sail.
  - Demons must NEVER outnumber monks on either bank (or the monks get eaten!).
  - Get all 6 across to win.

Controls: click characters to board/unboard, click SAIL to cross.
"""

import pygame
import sys
import math
import random

# ─────────────────────────── constants ────────────────────────────
WIDTH, HEIGHT = 1000, 650
FPS = 60

WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
DARK_GRAY    = (40, 40, 40)

SKY_TOP      = (25, 25, 60)
SKY_BOT      = (80, 130, 190)


RIVER_COL    = (30, 100, 170)
RIVER_LIGHT  = (50, 140, 210)
RIVER_DARK   = (20, 70, 140)


BANK_GREEN   = (50, 130, 50)
BANK_DARK    = (35, 95, 35)
BANK_LIGHT   = (70, 160, 70)
SAND         = (180, 160, 110)


MONK_ROBE    = (230, 150, 30)
MONK_ROBE_D  = (190, 120, 20)
MONK_SKIN    = (240, 210, 170)
MONK_HEAD    = (160, 100, 40)


DEMON_BODY   = (180, 30, 30)
DEMON_BODY_D = (140, 20, 20)
DEMON_SKIN   = (100, 180, 80)
DEMON_HORN   = (60, 60, 60)
DEMON_EYE    = (255, 255, 0)


BTN_COLOR    = (60, 60, 100)
BTN_HOVER    = (80, 80, 140)
BTN_TEXT     = (230, 230, 255)
HIGHLIGHT    = (255, 255, 100, 120)
OVERLAY_BG   = (0, 0, 0, 180)


BOAT_WOOD    = (120, 75, 35)
BOAT_DARK    = (85, 50, 20)
BOAT_RIM     = (150, 100, 50)


BANK_WIDTH   = 250
RIVER_Y      = 340
RIVER_H      = 180
LEFT_CENTER  = BANK_WIDTH // 2
RIGHT_CENTER = WIDTH - BANK_WIDTH // 2
BOAT_LEFT_X  = BANK_WIDTH + 60
BOAT_RIGHT_X = WIDTH - BANK_WIDTH - 60
BOAT_Y       = RIVER_Y + RIVER_H // 2 - 10
CHAR_SIZE    = 44

# ─────────────────────────── helpers ──────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t


def is_state_valid(monks_left, demons_left, monks_right, demons_right):
    """Return True if monks are safe on BOTH banks."""
    if monks_left > 0 and demons_left > monks_left:
        return False
    if monks_right > 0 and demons_right > monks_right:
        return False
    return True


class Particle:
    """Simple water sparkle."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(BANK_WIDTH + 10, WIDTH - BANK_WIDTH - 10)
        self.y = random.randint(RIVER_Y, RIVER_Y + RIVER_H)
        self.life = random.uniform(0.5, 2.0)
        self.max_life = self.life
        self.size = random.uniform(1, 3)
        self.speed_x = random.uniform(-8, 8)
        self.speed_y = random.uniform(-2, 2)

    def update(self, dt):
        self.life -= dt
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        if self.life <= 0:
            self.reset()

    def draw(self, surf):
        alpha = max(0, self.life / self.max_life)
        r = int(self.size * alpha * 2)
        if r < 1:
            return
        col = (200, 230, 255)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), r)


# ─────────────────────── drawing functions ────────────────────────

def draw_gradient_sky(surf):
    for y in range(RIVER_Y + 30):
        t = y / (RIVER_Y + 30)
        r = int(lerp(SKY_TOP[0], SKY_BOT[0], t))
        g = int(lerp(SKY_TOP[1], SKY_BOT[1], t))
        b = int(lerp(SKY_TOP[2], SKY_BOT[2], t))
        pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))


def draw_stars(surf, time_val):
    random.seed(42)
    for _ in range(40):
        sx = random.randint(0, WIDTH)
        sy = random.randint(0, RIVER_Y - 60)
        brightness = int(120 + 60 * math.sin(time_val * 2 + sx))
        brightness = max(0, min(255, brightness))
        pygame.draw.circle(surf, (brightness, brightness, brightness + 30), (sx, sy), 1)
    random.seed()  # unseed


def draw_moon(surf, time_val):
    mx, my = 800, 80
    glow_r = int(45 + 5 * math.sin(time_val))
    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    for r in range(glow_r, 0, -1):
        alpha = int(40 * (r / glow_r))
        pygame.draw.circle(glow_surf, (255, 255, 200, alpha), (glow_r, glow_r), r)
    surf.blit(glow_surf, (mx - glow_r, my - glow_r))
    pygame.draw.circle(surf, (240, 240, 220), (mx, my), 28)
    pygame.draw.circle(surf, (220, 220, 200), (mx + 6, my - 4), 8)
    pygame.draw.circle(surf, (210, 210, 190), (mx - 8, my + 6), 5)


def draw_river(surf, time_val):
    pygame.draw.rect(surf, RIVER_COL, (BANK_WIDTH, RIVER_Y, WIDTH - 2 * BANK_WIDTH, RIVER_H))

    for i in range(6):
        wy = RIVER_Y + 20 + i * 28
        points = []
        for x in range(BANK_WIDTH, WIDTH - BANK_WIDTH + 1, 8):
            off = math.sin(time_val * 1.5 + x * 0.015 + i * 1.2) * 5
            points.append((x, wy + off))
        if len(points) > 1:
            col = RIVER_LIGHT if i % 2 == 0 else RIVER_DARK
            pygame.draw.lines(surf, col, False, points, 2)


def draw_banks(surf):

    pygame.draw.rect(surf, BANK_DARK, (0, RIVER_Y - 5, BANK_WIDTH + 5, RIVER_H + 40))
    pygame.draw.rect(surf, BANK_GREEN, (0, RIVER_Y, BANK_WIDTH, RIVER_H + 30))
    pygame.draw.rect(surf, SAND, (BANK_WIDTH - 15, RIVER_Y, 15, RIVER_H + 30))

    for gx in range(10, BANK_WIDTH - 20, 25):
        gy = RIVER_Y - 2
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx - 4, gy - 10), 2)
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx + 4, gy - 12), 2)
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx + 1, gy - 14), 2)

    pygame.draw.rect(surf, BANK_DARK, (WIDTH - BANK_WIDTH - 5, RIVER_Y - 5, BANK_WIDTH + 10, RIVER_H + 40))
    pygame.draw.rect(surf, BANK_GREEN, (WIDTH - BANK_WIDTH, RIVER_Y, BANK_WIDTH, RIVER_H + 30))
    pygame.draw.rect(surf, SAND, (WIDTH - BANK_WIDTH, RIVER_Y, 15, RIVER_H + 30))
    for gx in range(WIDTH - BANK_WIDTH + 15, WIDTH - 10, 25):
        gy = RIVER_Y - 2
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx - 4, gy - 10), 2)
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx + 4, gy - 12), 2)
        pygame.draw.line(surf, BANK_LIGHT, (gx, gy), (gx + 1, gy - 14), 2)

    pygame.draw.rect(surf, BANK_DARK, (0, RIVER_Y + RIVER_H, WIDTH, HEIGHT - RIVER_Y - RIVER_H))


def draw_boat(surf, x, y, time_val):
    bob = math.sin(time_val * 2.5) * 3
    by = y + bob

    pts = [
        (x - 50, int(by)),
        (x - 40, int(by + 22)),
        (x + 40, int(by + 22)),
        (x + 50, int(by)),
    ]
    pygame.draw.polygon(surf, BOAT_WOOD, pts)
    pygame.draw.polygon(surf, BOAT_DARK, pts, 3)

    pygame.draw.line(surf, BOAT_RIM, (x - 50, int(by)), (x + 50, int(by)), 3)

    pygame.draw.line(surf, BOAT_RIM, (x - 18, int(by + 2)), (x - 18, int(by + 18)), 3)
    pygame.draw.line(surf, BOAT_RIM, (x + 18, int(by + 2)), (x + 18, int(by + 18)), 3)
    return int(by)


def draw_monk(surf, cx, cy, highlighted=False):
    """Draw a monk character centered at (cx, cy)."""
    if highlighted:
        hs = pygame.Surface((CHAR_SIZE + 16, CHAR_SIZE + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(hs, (255, 255, 100, 70), (0, 0, CHAR_SIZE + 16, CHAR_SIZE + 20))
        surf.blit(hs, (cx - CHAR_SIZE // 2 - 8, cy - CHAR_SIZE // 2 - 10))


    body_rect = pygame.Rect(cx - 12, cy, 24, 22)
    pygame.draw.rect(surf, MONK_ROBE, body_rect, border_radius=6)
    pygame.draw.rect(surf, MONK_ROBE_D, body_rect, 2, border_radius=6)


    pygame.draw.circle(surf, MONK_SKIN, (cx, cy - 6), 12)
    pygame.draw.circle(surf, MONK_HEAD, (cx, cy - 14), 8)  # shaved top / hair


    pygame.draw.circle(surf, BLACK, (cx - 4, cy - 7), 2)
    pygame.draw.circle(surf, BLACK, (cx + 4, cy - 7), 2)


    pygame.draw.arc(surf, BLACK, (cx - 5, cy - 6, 10, 8), 3.4, 6.0, 1)


    font_sm = pygame.font.SysFont("arial", 11, bold=True)
    label = font_sm.render("M", True, WHITE)
    surf.blit(label, (cx - label.get_width() // 2, cy + 24))


def draw_demon(surf, cx, cy, highlighted=False):
    """Draw a demon character centered at (cx, cy)."""
    if highlighted:
        hs = pygame.Surface((CHAR_SIZE + 16, CHAR_SIZE + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(hs, (255, 80, 80, 70), (0, 0, CHAR_SIZE + 16, CHAR_SIZE + 20))
        surf.blit(hs, (cx - CHAR_SIZE // 2 - 8, cy - CHAR_SIZE // 2 - 10))


    body_rect = pygame.Rect(cx - 12, cy, 24, 22)
    pygame.draw.rect(surf, DEMON_BODY, body_rect, border_radius=6)
    pygame.draw.rect(surf, DEMON_BODY_D, body_rect, 2, border_radius=6)


    pygame.draw.circle(surf, DEMON_SKIN, (cx, cy - 6), 12)


    pygame.draw.polygon(surf, DEMON_HORN, [(cx - 10, cy - 14), (cx - 14, cy - 28), (cx - 6, cy - 16)])
    pygame.draw.polygon(surf, DEMON_HORN, [(cx + 10, cy - 14), (cx + 14, cy - 28), (cx + 6, cy - 16)])


    pygame.draw.circle(surf, DEMON_EYE, (cx - 4, cy - 7), 3)
    pygame.draw.circle(surf, BLACK, (cx - 4, cy - 7), 1)
    pygame.draw.circle(surf, DEMON_EYE, (cx + 4, cy - 7), 3)
    pygame.draw.circle(surf, BLACK, (cx + 4, cy - 7), 1)


    pygame.draw.arc(surf, (200, 0, 0), (cx - 6, cy - 2, 12, 8), 3.4, 6.0, 2)

    # Label
    font_sm = pygame.font.SysFont("arial", 11, bold=True)
    label = font_sm.render("D", True, WHITE)
    surf.blit(label, (cx - label.get_width() // 2, cy + 24))


# ─────────────────────── button class ─────────────────────────────

class Button:
    def __init__(self, x, y, w, h, text, font, color=BTN_COLOR, hover=BTN_HOVER):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover = hover
        self.is_hovered = False

    def draw(self, surf):
        col = self.hover if self.is_hovered else self.color
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, (180, 180, 220), self.rect, 2, border_radius=10)
        txt = self.font.render(self.text, True, BTN_TEXT)
        surf.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                        self.rect.centery - txt.get_height() // 2))

    def update(self, mpos):
        self.is_hovered = self.rect.collidepoint(mpos)

    def clicked(self, mpos):
        return self.rect.collidepoint(mpos)


# ────────────────────────── character ─────────────────────────────

class Character:
    def __init__(self, kind, cid):
        self.kind = kind        # 'monk' or 'demon'
        self.id = cid
        self.location = 'left'  # 'left', 'boat', 'right'
        self.target_x = 0
        self.target_y = 0
        self.x = 0.0
        self.y = 0.0

    def hit(self, mx, my):
        return abs(mx - self.x) < CHAR_SIZE // 2 + 4 and abs(my - self.y) < CHAR_SIZE // 2 + 10


# ─────────────────────────── game ─────────────────────────────────

class Game:
    def __init__(self):
        self.characters = []
        for i in range(3):
            self.characters.append(Character('monk', i))
        for i in range(3):
            self.characters.append(Character('demon', i + 3))

        self.boat_side = 'left'  # 'left' or 'right'
        self.boat_x = float(BOAT_LEFT_X)
        self.boat_target_x = float(BOAT_LEFT_X)
        self.boat_moving = False
        self.boat_anim_t = 0.0

        self.moves = 0
        self.state = 'playing'  # 'playing', 'won', 'lost', 'animating'
        self.message = ""
        self.msg_timer = 0.0

        self.particles = [Particle() for _ in range(30)]
        self._assign_positions()

    def _assign_positions(self):
        """Compute target positions for all characters based on their location."""
        left_chars = [c for c in self.characters if c.location == 'left']
        right_chars = [c for c in self.characters if c.location == 'right']
        boat_chars = [c for c in self.characters if c.location == 'boat']


        for i, c in enumerate(left_chars):
            col = i % 3
            row = i // 3
            c.target_x = 40 + col * 65
            c.target_y = RIVER_Y + 40 + row * 65


        for i, c in enumerate(right_chars):
            col = i % 3
            row = i // 3
            c.target_x = WIDTH - BANK_WIDTH + 30 + col * 65
            c.target_y = RIVER_Y + 40 + row * 65


        bx = BOAT_LEFT_X if self.boat_side == 'left' else BOAT_RIGHT_X
        for i, c in enumerate(boat_chars):
            offset = -20 + i * 40
            c.target_x = bx + offset
            c.target_y = BOAT_Y - 20

    def _count(self, location, kind):
        return sum(1 for c in self.characters if c.location == location and c.kind == kind)

    def _boat_count(self):
        return sum(1 for c in self.characters if c.location == 'boat')

    def set_message(self, text, duration=2.5):
        self.message = text
        self.msg_timer = duration

    def handle_click(self, mx, my):
        if self.state != 'playing':
            return


        for c in self.characters:
            if c.hit(mx, my):
                self._toggle_character(c)
                return

    def _toggle_character(self, char):
        """Toggle a character between their bank and the boat."""
        if char.location == 'boat':

            char.location = self.boat_side
            self._assign_positions()
            return

        if char.location == self.boat_side:

            if self._boat_count() >= 2:
                self.set_message("⚠ Boat is full! (max 2)")
                return
            char.location = 'boat'
            self._assign_positions()
            return


        self.set_message("⚠ That character is on the other bank!")

    def try_sail(self):
        if self.state != 'playing':
            return
        if self._boat_count() == 0:
            self.set_message("⚠ Boat needs at least 1 person!")
            return


        other = 'right' if self.boat_side == 'left' else 'left'


        monks_left = self._count('left', 'monk')
        demons_left = self._count('left', 'demon')
        monks_right = self._count('right', 'monk')
        demons_right = self._count('right', 'demon')
        monks_boat = self._count('boat', 'monk')
        demons_boat = self._count('boat', 'demon')

        if other == 'right':
            monks_right += monks_boat
            demons_right += demons_boat
        else:
            monks_left += monks_boat
            demons_left += demons_boat

        if self.boat_side == 'right':
            monks_right -= monks_boat
            demons_right -= demons_boat
        else:
            monks_left -= monks_boat
            demons_left -= demons_boat


        self.state = 'animating'
        self.boat_target_x = float(BOAT_RIGHT_X if other == 'right' else BOAT_LEFT_X)
        self.boat_moving = True
        self.boat_anim_t = 0.0
        self._pending_side = other
        self._pending_valid = is_state_valid(monks_left, demons_left, monks_right, demons_right)
        self._pending_monks_left = monks_left
        self._pending_demons_left = demons_left
        self._pending_monks_right = monks_right
        self._pending_demons_right = demons_right

    def _finish_sail(self):
        """Called when boat animation finishes."""
        other = self._pending_side

        for c in self.characters:
            if c.location == 'boat':
                c.location = other

        self.boat_side = other
        self.moves += 1
        self.boat_moving = False
        self._assign_positions()

        if not self._pending_valid:
            self.state = 'lost'
            self.set_message("☠ Demons outnumbered monks! Game Over!", 999)
            return


        if all(c.location == 'right' for c in self.characters):
            self.state = 'won'
            self.set_message(f"🎉 Victory in {self.moves} moves!", 999)
            return

        self.state = 'playing'

    def reset(self):
        for c in self.characters:
            c.location = 'left'
        self.boat_side = 'left'
        self.boat_x = float(BOAT_LEFT_X)
        self.boat_target_x = float(BOAT_LEFT_X)
        self.boat_moving = False
        self.moves = 0
        self.state = 'playing'
        self.message = ""
        self.msg_timer = 0
        self._assign_positions()

    def update(self, dt):

        if self.msg_timer > 0:
            self.msg_timer -= dt
            if self.msg_timer <= 0:
                self.message = ""


        if self.boat_moving:
            self.boat_anim_t += dt * 0.65
            if self.boat_anim_t >= 1.0:
                self.boat_anim_t = 1.0
                self.boat_x = self.boat_target_x
                self._finish_sail()
            else:
                start_x = BOAT_LEFT_X if self._pending_side == 'right' else BOAT_RIGHT_X
                self.boat_x = lerp(start_x, self.boat_target_x, self.boat_anim_t)

                boat_chars = [c for c in self.characters if c.location == 'boat']
                for i, c in enumerate(boat_chars):
                    offset = -20 + i * 40
                    c.target_x = self.boat_x + offset
                    c.target_y = BOAT_Y - 20


        speed = 12.0
        for c in self.characters:
            c.x += (c.target_x - c.x) * speed * dt
            c.y += (c.target_y - c.y) * speed * dt


        for p in self.particles:
            p.update(dt)


# ───────────────────────── main loop ──────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🛶 Monk & Demon — River Crossing Puzzle")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("segoeui", 28, bold=True)
    font_btn   = pygame.font.SysFont("segoeui", 20, bold=True)
    font_info  = pygame.font.SysFont("segoeui", 18)
    font_msg   = pygame.font.SysFont("segoeui", 22, bold=True)
    font_big   = pygame.font.SysFont("segoeui", 44, bold=True)
    font_sub   = pygame.font.SysFont("segoeui", 22)

    game = Game()

    sail_btn  = Button(WIDTH // 2 - 55, HEIGHT - 60, 110, 42, "⛵  SAIL", font_btn,
                       (40, 90, 160), (60, 120, 200))
    reset_btn = Button(WIDTH - 130, 12, 110, 36, "↻  Reset", font_info,
                       (120, 40, 40), (160, 60, 60))

    time_val = 0.0


    for c in game.characters:
        c.x = c.target_x
        c.y = c.target_y

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        time_val += dt
        mpos = pygame.mouse.get_pos()


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.reset()
                    for c in game.characters:
                        c.x = c.target_x
                        c.y = c.target_y
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state in ('won', 'lost'):

                    play_again_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 50, 180, 44)
                    if play_again_rect.collidepoint(mpos):
                        game.reset()
                        for c in game.characters:
                            c.x = c.target_x
                            c.y = c.target_y
                elif game.state == 'playing':
                    if sail_btn.clicked(mpos):
                        game.try_sail()
                    elif reset_btn.clicked(mpos):
                        game.reset()
                        for c in game.characters:
                            c.x = c.target_x
                            c.y = c.target_y
                    else:
                        game.handle_click(*mpos)


        game.update(dt)
        sail_btn.update(mpos)
        reset_btn.update(mpos)


        screen.fill(BLACK)
        draw_gradient_sky(screen)
        draw_stars(screen, time_val)
        draw_moon(screen, time_val)
        draw_river(screen, time_val)
        draw_banks(screen)


        for p in game.particles:
            p.draw(screen)


        boat_draw_y = draw_boat(screen, int(game.boat_x), BOAT_Y, time_val)


        for c in game.characters:
            is_hl = (c.location == game.boat_side or c.location == 'boat') and game.state == 'playing'
            if c.kind == 'monk':
                draw_monk(screen, int(c.x), int(c.y), highlighted=is_hl)
            else:
                draw_demon(screen, int(c.x), int(c.y), highlighted=is_hl)

        title_surf = font_title.render("Monk & Demon — River Crossing", True, (220, 220, 240))
        screen.blit(title_surf, (20, 14))


        moves_surf = font_info.render(f"Moves: {game.moves}", True, (180, 200, 220))
        screen.blit(moves_surf, (20, 52))


        left_label = font_info.render("← Left Bank", True, (200, 220, 200))
        screen.blit(left_label, (20, RIVER_Y - 28))
        right_label = font_info.render("Right Bank →", True, (200, 220, 200))
        screen.blit(right_label, (WIDTH - BANK_WIDTH + 15, RIVER_Y - 28))


        arrow = "◄── Boat" if game.boat_side == 'left' else "Boat ──►"
        boat_label = font_info.render(arrow, True, (200, 200, 255))
        screen.blit(boat_label, (WIDTH // 2 - boat_label.get_width() // 2, RIVER_Y - 28))


        lm = game._count('left', 'monk')
        ld = game._count('left', 'demon')
        rm = game._count('right', 'monk')
        rd = game._count('right', 'demon')
        left_count = font_info.render(f"M:{lm}  D:{ld}", True, (220, 220, 180))
        screen.blit(left_count, (20, RIVER_Y + RIVER_H + 10))
        right_count = font_info.render(f"M:{rm}  D:{rd}", True, (220, 220, 180))
        screen.blit(right_count, (WIDTH - BANK_WIDTH + 15, RIVER_Y + RIVER_H + 10))


        if game.state == 'playing':
            sail_btn.draw(screen)
        reset_btn.draw(screen)


        if game.message and game.state == 'playing':
            msg_surf = font_msg.render(game.message, True, (255, 230, 100))
            mx_pos = WIDTH // 2 - msg_surf.get_width() // 2
            bg_rect = pygame.Rect(mx_pos - 12, HEIGHT - 105, msg_surf.get_width() + 24, 34)
            pygame.draw.rect(screen, (30, 30, 30, 200), bg_rect, border_radius=8)
            screen.blit(msg_surf, (mx_pos, HEIGHT - 102))


        if game.state in ('won', 'lost'):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            if game.state == 'won':
                big_text = font_big.render("🎉  YOU WON!  🎉", True, (100, 255, 100))
                sub_text = font_sub.render(f"Crossed the river in {game.moves} moves", True, (200, 255, 200))
            else:
                big_text = font_big.render("💀  GAME OVER  💀", True, (255, 80, 80))
                sub_text = font_sub.render("Demons outnumbered the monks!", True, (255, 180, 180))

            screen.blit(big_text, (WIDTH // 2 - big_text.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, HEIGHT // 2 - 10))


            pa_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 50, 180, 44)
            pa_hover = pa_rect.collidepoint(mpos)
            pa_col = (80, 80, 140) if pa_hover else (60, 60, 100)
            pygame.draw.rect(screen, pa_col, pa_rect, border_radius=10)
            pygame.draw.rect(screen, (180, 180, 220), pa_rect, 2, border_radius=10)
            pa_text = font_btn.render("Play Again", True, BTN_TEXT)
            screen.blit(pa_text, (pa_rect.centerx - pa_text.get_width() // 2,
                                  pa_rect.centery - pa_text.get_height() // 2))


        if game.state == 'playing' and game.moves == 0 and game._boat_count() == 0:
            inst_text = font_info.render(
                "Click characters to board the boat. Click SAIL to cross. Don't let demons outnumber monks!",
                True, (180, 180, 210))
            screen.blit(inst_text, (WIDTH // 2 - inst_text.get_width() // 2, HEIGHT - 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
