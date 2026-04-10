"""
UI module for the Sliding Puzzle Game.

Handles all rendering: board, tiles, HUD, menus, animations, and
win screen.  Features a premium dark theme with particle effects,
gradient backgrounds, glassmorphism elements, and smooth animations.
"""

import os
import math
import random
import pygame

# ======================================================================
# Colour palette — premium dark theme with vibrant accents
# ======================================================================
COLORS = {
    "bg_top": (12, 12, 30),
    "bg_bottom": (25, 18, 45),
    "bg": (18, 18, 28),
    "board_bg": (20, 20, 35),
    "board_border": (60, 70, 140),
    "tile_text": (255, 255, 255),
    "tile_correct": (30, 180, 90),
    "tile_hover": (100, 130, 220),
    "empty": (15, 15, 28),
    "hud_bg": (15, 15, 28, 220),
    "hud_text": (170, 175, 195),
    "hud_accent": (100, 140, 255),
    "hud_accent2": (180, 120, 255),
    "button": (35, 40, 80),
    "button_hover": (55, 65, 120),
    "button_text": (230, 235, 255),
    "button_border": (80, 100, 200),
    "title": (100, 140, 255),
    "title_glow": (80, 120, 255),
    "win_text": (255, 220, 50),
    "overlay": (0, 0, 0, 180),
    "pause_text": (255, 200, 60),
    "star": (255, 220, 100),
}

# Richer gradient endpoints for numbered tiles
TILE_GRAD_A = (50, 80, 180)
TILE_GRAD_B = (150, 60, 220)
TILE_GRAD_C = (80, 200, 160)  # Third gradient point for more variety


# ======================================================================
# Particle system for visual flair
# ======================================================================
class Particle:
    """A single floating particle for ambient background effects."""

    def __init__(self, x, y, vx, vy, size, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        if alpha < 10:
            return
        s = max(1, int(self.size * (self.life / self.max_life)))
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            surf, (*self.color, alpha), (s, s), s
        )
        surface.blit(surf, (int(self.x) - s, int(self.y) - s))


class ParticleSystem:
    """Manages a collection of ambient particles."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.particles: list[Particle] = []
        self._spawn_timer = 0.0
        # Pre-spawn some particles
        for _ in range(15):
            self._spawn_ambient()

    def _spawn_ambient(self):
        """Spawn a gentle floating particle."""
        x = random.uniform(0, self.width)
        y = random.uniform(0, self.height)
        vx = random.uniform(-8, 8)
        vy = random.uniform(-12, -3)
        size = random.uniform(1.5, 4)
        colors = [
            (100, 140, 255), (150, 100, 255), (80, 200, 180),
            (200, 120, 255), (120, 180, 255),
        ]
        color = random.choice(colors)
        life = random.uniform(4, 10)
        self.particles.append(Particle(x, y, vx, vy, size, color, life))

    def spawn_burst(self, x, y, count=30):
        """Spawn a celebratory burst of particles at (x, y)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 180)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 6)
            colors = [
                (255, 220, 50), (255, 150, 50), (100, 255, 150),
                (100, 180, 255), (255, 100, 150), (200, 120, 255),
            ]
            color = random.choice(colors)
            life = random.uniform(1.0, 2.5)
            self.particles.append(Particle(x, y, vx, vy, size, color, life))

    def update(self, dt):
        self._spawn_timer += dt
        if self._spawn_timer > 0.4:
            self._spawn_timer = 0
            self._spawn_ambient()

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)


# ======================================================================
# Animation helper
# ======================================================================
class TileAnimation:
    """Smooth ease-out slide animation for a single tile."""

    def __init__(self, tile_value, from_px, to_px, duration=0.14):
        self.tile_value = tile_value
        self.from_px = from_px       # (x, y) pixel start
        self.to_px = to_px           # (x, y) pixel end
        self.duration = duration
        self.elapsed = 0.0
        self.done = False

    def update(self, dt):
        """Advance animation clock by *dt* seconds."""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done = True

    def current_pos(self):
        """Return current (x, y) using ease-out cubic interpolation."""
        t = min(self.elapsed / self.duration, 1.0)
        t = 1 - (1 - t) ** 3  # ease-out cubic
        x = self.from_px[0] + (self.to_px[0] - self.from_px[0]) * t
        y = self.from_px[1] + (self.to_px[1] - self.from_px[1]) * t
        return x, y


# ======================================================================
# Renderer
# ======================================================================
class Renderer:
    """Main renderer for the sliding puzzle game with premium visuals."""

    # Layout constants
    WIN_W = 620
    HUD_H = 120
    PAD = 10
    GAP = 5
    RADIUS = 12

    def __init__(self, screen):
        self.screen = screen
        self.animations: list[TileAnimation] = []
        self.hover_tile = None          # (row, col) under mouse
        self.puzzle_image = None        # loaded pygame.Surface
        self.tile_surfaces: dict = {}   # {tile_value: Surface}
        self.particles = ParticleSystem(self.WIN_W, self.WIN_W + self.HUD_H)
        self._time = 0.0               # Global clock for animated effects
        self._bg_surface = None         # Cached gradient background
        self._init_fonts()
        self._create_bg_gradient()

    # ------------------------------------------------------------------
    # Font setup
    # ------------------------------------------------------------------
    def _init_fonts(self):
        """Load system fonts with fallback to PyGame defaults."""
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 30)
        self.font_tile = pygame.font.Font(None, 64)
        self.font_tile_sm = pygame.font.Font(None, 46)
        self.font_hud = pygame.font.Font(None, 26)
        self.font_tiny = pygame.font.Font(None, 20)

        # Attempt to use Segoe UI (Windows) for a modern look
        for path in (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ):
            if os.path.exists(path):
                try:
                    self.font_large = pygame.font.Font(path, 52)
                    self.font_medium = pygame.font.Font(path, 34)
                    self.font_small = pygame.font.Font(path, 22)
                    self.font_hud = pygame.font.Font(path, 19)
                    self.font_tiny = pygame.font.Font(path, 15)
                    bold = path.replace("segoeui", "segoeuib").replace(
                        "arial", "arialbd"
                    )
                    tf = bold if os.path.exists(bold) else path
                    self.font_tile = pygame.font.Font(tf, 48)
                    self.font_tile_sm = pygame.font.Font(tf, 34)
                except Exception:
                    pass
                break

    # ------------------------------------------------------------------
    # Background gradient
    # ------------------------------------------------------------------
    def _create_bg_gradient(self):
        """Create a cached vertical gradient background surface."""
        h = self.WIN_W + self.HUD_H
        self._bg_surface = pygame.Surface((self.WIN_W, h))
        top = COLORS["bg_top"]
        bot = COLORS["bg_bottom"]
        for y in range(h):
            t = y / h
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(self._bg_surface, (r, g, b), (0, y), (self.WIN_W, y))

    def draw_background(self):
        """Draw the gradient background with particles."""
        self.screen.blit(self._bg_surface, (0, 0))
        self.particles.draw(self.screen)

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def board_rect(self, _size):
        """Pixel rect of the board area (below HUD)."""
        side = self.WIN_W - 2 * self.PAD
        return pygame.Rect(self.PAD, self.HUD_H, side, side)

    def tile_rect(self, row, col, size):
        """Pixel rect of a single tile at grid position (row, col)."""
        br = self.board_rect(size)
        ts = (br.width - (size + 1) * self.GAP) / size
        x = br.x + self.GAP + col * (ts + self.GAP)
        y = br.y + self.GAP + row * (ts + self.GAP)
        return pygame.Rect(x, y, ts, ts)

    def tile_size_px(self, size):
        """Pixel side-length of one tile."""
        br = self.board_rect(size)
        return (br.width - (size + 1) * self.GAP) / size

    def pixel_to_grid(self, px, py, size):
        """Convert pixel (px, py) -> grid (row, col) or ``None``."""
        br = self.board_rect(size)
        if not br.collidepoint(px, py):
            return None
        ts = self.tile_size_px(size)
        col = int((px - br.x - self.GAP) / (ts + self.GAP))
        row = int((py - br.y - self.GAP) / (ts + self.GAP))
        if 0 <= row < size and 0 <= col < size:
            tr = self.tile_rect(row, col, size)
            if tr.collidepoint(px, py):
                return row, col
        return None

    # ------------------------------------------------------------------
    # Puzzle image helpers (Image Mode)
    # ------------------------------------------------------------------
    def load_puzzle_image(self, image_path, size):
        """Load *image_path*, scale, and slice it into per-tile surfaces."""
        try:
            img = pygame.image.load(image_path).convert()
            ts = int(self.tile_size_px(size))
            total = ts * size
            img = pygame.transform.smoothscale(img, (total, total))
            self.puzzle_image = img
            self.tile_surfaces.clear()
            for r in range(size):
                for c in range(size):
                    num = r * size + c + 1
                    if num < size * size:
                        rect = pygame.Rect(c * ts, r * ts, ts, ts)
                        self.tile_surfaces[num] = img.subsurface(rect).copy()
        except Exception as exc:
            print(f"[UI] Could not load puzzle image: {exc}")
            self.puzzle_image = None

    # ------------------------------------------------------------------
    # Animation management
    # ------------------------------------------------------------------
    def start_animation(self, value, fr, fc, tr, tc, size):
        """Queue a slide animation from grid (fr,fc) -> (tr,tc)."""
        src = self.tile_rect(fr, fc, size)
        dst = self.tile_rect(tr, tc, size)
        self.animations.append(
            TileAnimation(value, (src.x, src.y), (dst.x, dst.y))
        )

    def update_animations(self, dt):
        """Tick all animations, removing finished ones."""
        self._time += dt
        self.particles.update(dt)
        for a in self.animations:
            a.update(dt)
        self.animations = [a for a in self.animations if not a.done]

    def is_animating(self):
        return bool(self.animations)

    # ------------------------------------------------------------------
    # Tile drawing
    # ------------------------------------------------------------------
    @staticmethod
    def _tile_color(value, total):
        """Rich multi-point gradient colour based on tile number."""
        t = value / max(total - 1, 1)
        if t < 0.5:
            t2 = t * 2
            return tuple(
                int(TILE_GRAD_A[i] + (TILE_GRAD_B[i] - TILE_GRAD_A[i]) * t2)
                for i in range(3)
            )
        else:
            t2 = (t - 0.5) * 2
            return tuple(
                int(TILE_GRAD_B[i] + (TILE_GRAD_C[i] - TILE_GRAD_B[i]) * t2)
                for i in range(3)
            )

    def _draw_tile(self, rect, value, size, correct, hover, image_mode):
        """Render a single tile with enhanced visuals."""
        if value == 0:
            # Empty cell with subtle inner shadow
            empty_surf = pygame.Surface(
                (int(rect.width), int(rect.height)), pygame.SRCALPHA
            )
            pygame.draw.rect(
                empty_surf, (*COLORS["empty"], 180),
                pygame.Rect(0, 0, int(rect.width), int(rect.height)),
                border_radius=self.RADIUS,
            )
            # Inner shadow top-left
            pygame.draw.rect(
                empty_surf, (0, 0, 0, 30),
                pygame.Rect(2, 2, int(rect.width) - 4, int(rect.height) - 4),
                border_radius=self.RADIUS - 2,
            )
            self.screen.blit(empty_surf, rect.topleft)
            return

        if image_mode and value in self.tile_surfaces:
            surf = self.tile_surfaces[value]
            scaled = pygame.transform.smoothscale(
                surf, (int(rect.width), int(rect.height))
            )
            # Draw with a subtle border
            border_rect = rect.inflate(2, 2)
            pygame.draw.rect(
                self.screen, (40, 40, 60),
                border_rect, border_radius=self.RADIUS,
            )
            self.screen.blit(scaled, rect.topleft)

            # Correct-position tint
            if correct:
                ov = pygame.Surface(
                    (int(rect.width), int(rect.height)), pygame.SRCALPHA
                )
                ov.fill((40, 220, 80, 45))
                self.screen.blit(ov, rect.topleft)
                pygame.draw.rect(
                    self.screen, (40, 220, 80, 180), rect,
                    2, border_radius=self.RADIUS,
                )
            # Hover glow
            if hover:
                pygame.draw.rect(
                    self.screen, (180, 200, 255),
                    rect, 3, border_radius=self.RADIUS,
                )
                # Outer glow
                glow_rect = rect.inflate(6, 6)
                glow_surf = pygame.Surface(
                    (glow_rect.width, glow_rect.height), pygame.SRCALPHA
                )
                pygame.draw.rect(
                    glow_surf, (100, 140, 255, 30),
                    pygame.Rect(0, 0, glow_rect.width, glow_rect.height),
                    border_radius=self.RADIUS + 3,
                )
                self.screen.blit(glow_surf, glow_rect.topleft)
            return

        # --- Numbered tile with premium look ---
        total = size * size

        if correct:
            base = COLORS["tile_correct"]
        elif hover:
            base = COLORS["tile_hover"]
        else:
            base = self._tile_color(value, total)

        tile_surf = pygame.Surface(
            (int(rect.width), int(rect.height) + 4), pygame.SRCALPHA
        )

        # Shadow (offset below)
        shadow_c = tuple(max(0, c - 50) for c in base)
        pygame.draw.rect(
            tile_surf, (*shadow_c, 120),
            pygame.Rect(0, 4, int(rect.width), int(rect.height)),
            border_radius=self.RADIUS,
        )

        # Main body
        pygame.draw.rect(
            tile_surf, base,
            pygame.Rect(0, 0, int(rect.width), int(rect.height)),
            border_radius=self.RADIUS,
        )

        # Top highlight gradient (glassmorphism feel)
        hl_h = int(rect.height * 0.4)
        hl = pygame.Surface((int(rect.width) - 6, hl_h), pygame.SRCALPHA)
        for y in range(hl_h):
            alpha = int(50 * (1 - y / hl_h))
            pygame.draw.line(hl, (255, 255, 255, alpha), (0, y), (int(rect.width) - 6, y))
        tile_surf.blit(hl, (3, 3))

        # Bottom edge darker line
        pygame.draw.rect(
            tile_surf, (*[max(0, c - 30) for c in base], 80),
            pygame.Rect(3, int(rect.height) - 3, int(rect.width) - 6, 3),
            border_radius=2,
        )

        self.screen.blit(tile_surf, rect.topleft)

        # Hover glow ring
        if hover:
            glow_rect = rect.inflate(6, 6)
            glow_surf = pygame.Surface(
                (glow_rect.width, glow_rect.height), pygame.SRCALPHA
            )
            pygame.draw.rect(
                glow_surf, (120, 160, 255, 40),
                pygame.Rect(0, 0, glow_rect.width, glow_rect.height),
                border_radius=self.RADIUS + 3,
            )
            self.screen.blit(glow_surf, glow_rect.topleft)

        # Correct position subtle check indicator
        if correct:
            check_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(check_surf, (40, 220, 80, 200), (10, 10), 8)
            pygame.draw.circle(check_surf, (255, 255, 255, 220), (10, 10), 5)
            self.screen.blit(check_surf, (rect.right - 18, rect.top + 4))

        # Number label with subtle shadow
        font = self.font_tile if size <= 3 else self.font_tile_sm
        # Text shadow
        txt_shadow = font.render(str(value), True, (0, 0, 0))
        txt_shadow.set_alpha(80)
        self.screen.blit(
            txt_shadow,
            txt_shadow.get_rect(center=(rect.centerx + 1, rect.centery + 2)),
        )
        # Main text
        txt = font.render(str(value), True, COLORS["tile_text"])
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # Full board drawing
    # ------------------------------------------------------------------
    def draw_board(self, board, image_mode=False):
        """Draw the grid background and all tiles with enhanced visuals."""
        size = board.size
        br = self.board_rect(size)

        # Board background with subtle border glow
        board_glow = br.inflate(6, 6)
        glow_surf = pygame.Surface(
            (board_glow.width, board_glow.height), pygame.SRCALPHA
        )
        # Animated glow intensity
        glow_alpha = int(20 + 10 * math.sin(self._time * 1.5))
        pygame.draw.rect(
            glow_surf,
            (*COLORS["board_border"], glow_alpha),
            pygame.Rect(0, 0, board_glow.width, board_glow.height),
            border_radius=15,
        )
        self.screen.blit(glow_surf, board_glow.topleft)

        # Main board background
        board_surf = pygame.Surface((br.width, br.height), pygame.SRCALPHA)
        pygame.draw.rect(
            board_surf, (*COLORS["board_bg"], 230),
            pygame.Rect(0, 0, br.width, br.height),
            border_radius=14,
        )
        self.screen.blit(board_surf, br.topleft)

        # Subtle border
        pygame.draw.rect(
            self.screen, COLORS["board_border"], br, 1, border_radius=14
        )

        animating = {a.tile_value for a in self.animations}

        for r in range(size):
            for c in range(size):
                val = board.get_tile_value(r, c)
                if val in animating:
                    tr = self.tile_rect(r, c, size)
                    # Show empty placeholder
                    empty_s = pygame.Surface(
                        (int(tr.width), int(tr.height)), pygame.SRCALPHA
                    )
                    pygame.draw.rect(
                        empty_s, (*COLORS["empty"], 120),
                        pygame.Rect(0, 0, int(tr.width), int(tr.height)),
                        border_radius=self.RADIUS,
                    )
                    self.screen.blit(empty_s, tr.topleft)
                    continue
                tr = self.tile_rect(r, c, size)
                self._draw_tile(
                    tr, val, size,
                    board.is_tile_in_correct_position(r, c),
                    self.hover_tile == (r, c) and val != 0,
                    image_mode,
                )

        # Animated tiles (drawn on top)
        for a in self.animations:
            px, py = a.current_pos()
            ts = self.tile_size_px(size)
            ar = pygame.Rect(px, py, ts, ts)
            self._draw_tile(ar, a.tile_value, size, False, False, image_mode)

    # ------------------------------------------------------------------
    # HUD (heads-up display) — glassmorphism style
    # ------------------------------------------------------------------
    def draw_hud(self, board, image_mode=False, image_name=""):
        """Draw the top bar with glassmorphism effect."""
        # Semi-transparent HUD background
        hud_surf = pygame.Surface((self.WIN_W, self.HUD_H), pygame.SRCALPHA)
        hud_surf.fill((15, 15, 28, 210))
        self.screen.blit(hud_surf, (0, 0))

        # Accent line at bottom of HUD
        for x in range(self.WIN_W):
            t = x / self.WIN_W
            r = int(80 + 60 * t)
            g = int(120 + 40 * (1 - t))
            b = 255
            pygame.draw.line(
                self.screen, (r, g, b),
                (x, self.HUD_H - 2), (x, self.HUD_H),
            )

        # Title
        title = self.font_medium.render("Sliding Puzzle", True, COLORS["title"])
        self.screen.blit(title, (18, 8))

        # Size & mode badges with pill styling
        badge_text = f"{board.size}x{board.size}"
        self._draw_pill(18 + title.get_width() + 10, 12, badge_text, COLORS["hud_accent"])

        mode_label = image_name if image_mode and image_name else ("Image" if image_mode else "Numbers")
        self._draw_pill(
            18 + title.get_width() + 65, 12,
            mode_label,
            COLORS["hud_accent2"] if image_mode else (100, 120, 150),
        )

        # Stats row
        self._hud_stat("MOVES", str(board.move_count), 18, 52)
        elapsed = board.get_elapsed_time()
        m, s = divmod(int(elapsed), 60)
        self._hud_stat("TIME", f"{m:02d}:{s:02d}", 130, 52)

        if board.best_moves is not None:
            bm, bs = board.best_moves, int(board.best_time or 0)
            bmin, bsec = divmod(bs, 60)
            self._hud_stat("BEST", f"{bm} / {bmin:02d}:{bsec:02d}", 240, 52)

        # Control hints (2x2 grid between stats and goal preview)
        start_x_base = 360
        start_y_base = 42
        
        hints = [("R", "Restart"), ("U", "Undo"), ("P", "Pause"), ("M", "Menu")]
        
        hud_buttons = []
        mouse = pygame.mouse.get_pos()
        
        for i, (key, action) in enumerate(hints):
            col = i % 2
            row = i // 2
            
            x = start_x_base + col * 70
            y = start_y_base + row * 24
            
            # Render the key name
            key_txt = self.font_tiny.render(key, True, (255, 255, 255))
            kw, kh = 18, 18 # Fixed tiny size for the box
            
            # Draw rounded box
            k_surf = pygame.Surface((kw, kh), pygame.SRCALPHA)
            
            # Action description
            act_txt = self.font_tiny.render(action, True, (130, 140, 170))
            
            # Interactive bounds
            btn_rect = pygame.Rect(x, y, kw + 4 + act_txt.get_width(), kh)
            hov = btn_rect.collidepoint(mouse)
            
            if hov:
                pygame.draw.rect(k_surf, (80, 100, 150, 200), pygame.Rect(0, 0, kw, kh), border_radius=3)
                pygame.draw.rect(k_surf, (150, 180, 255, 255), pygame.Rect(0, 0, kw, kh), 1, border_radius=3)
                act_txt = self.font_tiny.render(action, True, (200, 210, 255))
            else:
                pygame.draw.rect(k_surf, (60, 70, 100, 150), pygame.Rect(0, 0, kw, kh), border_radius=3)
                pygame.draw.rect(k_surf, (120, 140, 200, 180), pygame.Rect(0, 0, kw, kh), 1, border_radius=3)
            
            # Center the text
            k_surf.blit(key_txt, (kw//2 - key_txt.get_width()//2 + 1, kh//2 - key_txt.get_height()//2 + 1))
            self.screen.blit(k_surf, (x, y))
            self.screen.blit(act_txt, (x + kw + 4, y + 2))
            
            hud_buttons.append((btn_rect, action.lower()))
            
        return hud_buttons

    def _draw_pill(self, x, y, text, color):
        """Draw a small pill-shaped badge."""
        txt = self.font_tiny.render(text, True, (255, 255, 255))
        pw = txt.get_width() + 16
        ph = txt.get_height() + 6
        pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(
            pill, (*color, 140),
            pygame.Rect(0, 0, pw, ph),
            border_radius=ph // 2,
        )
        pill.blit(txt, (8, 3))
        self.screen.blit(pill, (x, y))

    def _hud_stat(self, label, value, x, y):
        """Draw a label/value pair in the HUD with styling."""
        lt = self.font_tiny.render(label, True, (120, 125, 150))
        vt = self.font_medium.render(value, True, COLORS["hud_accent"])
        self.screen.blit(lt, (x, y))
        self.screen.blit(vt, (x, y + 16))

    # ------------------------------------------------------------------
    # Win overlay — with particle burst
    # ------------------------------------------------------------------
    def draw_win_screen(self, board):
        """Semi-transparent overlay congratulating the player."""
        win_h = self.WIN_W + self.HUD_H
        overlay = pygame.Surface((self.WIN_W, win_h), pygame.SRCALPHA)
        overlay.fill(COLORS["overlay"])
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.WIN_W // 2, win_h // 2

        # Pulsing glow behind title
        pulse = 0.7 + 0.3 * math.sin(self._time * 3)
        glow_size = int(250 * pulse)
        glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(
            glow_surf, (255, 200, 50, int(25 * pulse)),
            pygame.Rect(0, 0, glow_size * 2, glow_size),
        )
        self.screen.blit(glow_surf, (cx - glow_size, cy - 90))

        # Title
        txt = self.font_large.render("Puzzle Solved!", True, COLORS["win_text"])
        # Shadow
        txt_s = self.font_large.render("Puzzle Solved!", True, (100, 80, 0))
        txt_s.set_alpha(60)
        self.screen.blit(txt_s, txt_s.get_rect(center=(cx + 2, cy - 58)))
        self.screen.blit(txt, txt.get_rect(center=(cx, cy - 60)))

        # Stats in a glass card
        card_w, card_h = 340, 50
        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(
            card, (40, 40, 70, 160),
            pygame.Rect(0, 0, card_w, card_h),
            border_radius=12,
        )
        pygame.draw.rect(
            card, (100, 140, 255, 60),
            pygame.Rect(0, 0, card_w, card_h),
            1, border_radius=12,
        )
        m, s = divmod(int(board.elapsed_time), 60)
        stat = self.font_medium.render(
            f"Moves: {board.move_count}   Time: {m:02d}:{s:02d}",
            True, COLORS["hud_text"],
        )
        card.blit(stat, stat.get_rect(center=(card_w // 2, card_h // 2)))
        self.screen.blit(card, (cx - card_w // 2, cy - 10))

        # Instructions
        inst = self.font_small.render(
            "Press [R] to play again  |  [M] for menu", True, (140, 145, 170)
        )
        self.screen.blit(inst, inst.get_rect(center=(cx, cy + 55)))

    # ------------------------------------------------------------------
    # Pause overlay
    # ------------------------------------------------------------------
    def draw_pause_overlay(self):
        """Draw a translucent overlay when the game is paused."""
        win_h = self.WIN_W + self.HUD_H
        overlay = pygame.Surface((self.WIN_W, win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.WIN_W // 2, win_h // 2

        # Pause icon (two bars)
        bar_w, bar_h = 14, 50
        gap = 12
        pygame.draw.rect(
            self.screen, COLORS["pause_text"],
            pygame.Rect(cx - gap - bar_w, cy - bar_h // 2, bar_w, bar_h),
            border_radius=4,
        )
        pygame.draw.rect(
            self.screen, COLORS["pause_text"],
            pygame.Rect(cx + gap, cy - bar_h // 2, bar_w, bar_h),
            border_radius=4,
        )

        sub = self.font_small.render(
            "Press [P] to resume", True, COLORS["hud_text"]
        )
        self.screen.blit(sub, sub.get_rect(center=(cx, cy + 50)))

    # ------------------------------------------------------------------
    # Main menu — premium styling
    # ------------------------------------------------------------------
    def draw_menu(self, selected_size=3, image_mode=False, image_name="",
                  image_count=1, image_idx=0, selected_idx=0):
        """
        Draw the main menu and return a list of ``(Rect, action_str)``
        tuples for click detection.
        """
        self.draw_background()
        cx = self.WIN_W // 2

        # Animated title glow
        glow_alpha = int(15 + 8 * math.sin(self._time * 2))
        title = self.font_large.render("Sliding Puzzle", True, COLORS["title"])
        tr = title.get_rect(center=(cx, 80))
        glow = pygame.Surface(
            (title.get_width() + 80, title.get_height() + 40), pygame.SRCALPHA
        )
        glow.fill((*COLORS["title_glow"], glow_alpha))
        self.screen.blit(glow, (tr.x - 40, tr.y - 20))
        # Title shadow
        title_s = self.font_large.render("Sliding Puzzle", True, (20, 30, 60))
        title_s.set_alpha(80)
        self.screen.blit(title_s, (tr.x + 2, tr.y + 2))
        self.screen.blit(title, tr)

        # Subtitle
        sub = self.font_small.render(
            "A Classic Logic Puzzle Game", True, (120, 125, 155)
        )
        self.screen.blit(sub, sub.get_rect(center=(cx, 130)))

        # Decorative line
        line_surf = pygame.Surface((200, 2), pygame.SRCALPHA)
        for x in range(200):
            t = x / 200
            a = int(60 * math.sin(t * math.pi))
            pygame.draw.line(line_surf, (100, 140, 255, a), (x, 0), (x, 1))
        self.screen.blit(line_surf, (cx - 100, 148))

        # Menu buttons
        img_label = image_name if image_mode and image_name else "Numbers"
        items = [
            ("New Game", "new_game"),
            (f"Grid: {selected_size}x{selected_size}", "grid_size"),
            (f"Mode: {img_label}", "tile_mode"),
        ]
        if selected_size == 3:
            items.append(("Auto Solve (3x3)", "auto_solve"))
        items.append(("Quit", "quit"))

        bw, bh, spacing = 340, 50, 60
        start_y = 175
        mouse = pygame.mouse.get_pos()
        buttons = []

        for i, (label, action) in enumerate(items):
            rect = pygame.Rect(cx - bw // 2, start_y + i * spacing, bw, bh)
            hov = rect.collidepoint(mouse) or (i == selected_idx)

            # Button with gradient border
            btn_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg_color = COLORS["button_hover"] if hov else COLORS["button"]
            pygame.draw.rect(
                btn_surf, (*bg_color, 200),
                pygame.Rect(0, 0, bw, bh),
                border_radius=12,
            )
            if hov:
                # Glow border
                pygame.draw.rect(
                    btn_surf, (*COLORS["button_border"], 180),
                    pygame.Rect(0, 0, bw, bh),
                    2, border_radius=12,
                )
                # Top highlight
                hl = pygame.Surface((bw - 8, bh // 3), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 15))
                btn_surf.blit(hl, (4, 2))
            else:
                pygame.draw.rect(
                    btn_surf, (60, 70, 120, 80),
                    pygame.Rect(0, 0, bw, bh),
                    1, border_radius=12,
                )

            txt = self.font_small.render(label, True, COLORS["button_text"])
            btn_surf.blit(txt, txt.get_rect(center=(bw // 2, bh // 2)))
            self.screen.blit(btn_surf, rect.topleft)
            buttons.append((rect, action))

        # Footer
        ft = self.font_tiny.render(
            "CSE444 - Vibe Coding Project", True, (100, 105, 130)
        )
        self.screen.blit(
            ft, ft.get_rect(center=(cx, self.WIN_W + self.HUD_H - 25))
        )
        return buttons

    # ------------------------------------------------------------------
    # Goal-state preview (small) — improved mini tiles
    # ------------------------------------------------------------------
    def draw_goal_preview(self, board, x, y, preview_size=100, image_mode=False):
        """Draw a miniature view of the goal (solved) state."""
        size = board.size
        ts = preview_size // size

        # Glass card background
        card = pygame.Surface(
            (preview_size + 8, preview_size + 28), pygame.SRCALPHA
        )
        pygame.draw.rect(
            card, (25, 25, 45, 180),
            pygame.Rect(0, 0, preview_size + 8, preview_size + 28),
            border_radius=8,
        )
        pygame.draw.rect(
            card, (60, 70, 120, 60),
            pygame.Rect(0, 0, preview_size + 8, preview_size + 28),
            1, border_radius=8,
        )
        self.screen.blit(card, (x - 4, y - 24))

        # Label
        lbl = self.font_tiny.render("GOAL", True, (100, 110, 140))
        self.screen.blit(lbl, (x, y - 18))

        total = size * size
        for r in range(size):
            for c in range(size):
                val = board.goal[r][c]
                tr = pygame.Rect(x + c * ts, y + r * ts, ts - 2, ts - 2)
                if val == 0:
                    pygame.draw.rect(
                        self.screen, COLORS["empty"], tr, border_radius=3
                    )
                else:
                    if image_mode and val in self.tile_surfaces:
                        surf = self.tile_surfaces[val]
                        scaled = pygame.transform.smoothscale(
                            surf, (int(tr.width), int(tr.height))
                        )
                        self.screen.blit(scaled, tr.topleft)
                    else:
                        clr = self._tile_color(val, total)
                        pygame.draw.rect(self.screen, clr, tr, border_radius=4)
                        if size <= 4:
                            ft = pygame.font.Font(None, max(14, 50 // size))
                            t = ft.render(str(val), True, COLORS["tile_text"])
                            self.screen.blit(t, t.get_rect(center=tr.center))
