"""
UI module for the Sliding Puzzle Game.

Handles all rendering: board, tiles, HUD, menus, animations, and
win screen.  Uses a modern dark colour palette with smooth gradient
tiles and slide animations.
"""

import os
import math
import pygame

# ======================================================================
# Colour palette — modern dark theme
# ======================================================================
COLORS = {
    "bg": (18, 18, 28),
    "board_bg": (28, 28, 42),
    "tile_text": (255, 255, 255),
    "tile_correct": (40, 170, 80),
    "tile_hover": (100, 130, 220),
    "empty": (22, 22, 32),
    "hud_bg": (22, 22, 34),
    "hud_text": (180, 185, 200),
    "hud_accent": (120, 150, 255),
    "button": (50, 60, 110),
    "button_hover": (70, 85, 150),
    "button_text": (240, 240, 255),
    "title": (120, 150, 255),
    "win_text": (255, 215, 0),
    "overlay": (0, 0, 0, 170),
    "pause_text": (255, 200, 60),
}

# Gradient endpoints for numbered tiles
TILE_GRAD_A = (60, 85, 165)
TILE_GRAD_B = (130, 80, 200)


# ======================================================================
# Animation helper
# ======================================================================
class TileAnimation:
    """Smooth ease-out slide animation for a single tile."""

    def __init__(self, tile_value, from_px, to_px, duration=0.12):
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
    """Main renderer for the sliding puzzle game."""

    # Layout constants
    WIN_W = 620
    HUD_H = 120
    PAD = 10
    GAP = 4
    RADIUS = 10

    def __init__(self, screen):
        self.screen = screen
        self.animations: list[TileAnimation] = []
        self.hover_tile = None          # (row, col) under mouse
        self.puzzle_image = None        # loaded pygame.Surface
        self.tile_surfaces: dict = {}   # {tile_value: Surface}
        self._init_fonts()

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

        # Attempt to use Segoe UI (Windows) for a modern look
        for path in (
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ):
            if os.path.exists(path):
                try:
                    self.font_large = pygame.font.Font(path, 56)
                    self.font_medium = pygame.font.Font(path, 36)
                    self.font_small = pygame.font.Font(path, 24)
                    self.font_hud = pygame.font.Font(path, 21)
                    bold = path.replace("segoeui", "segoeuib").replace(
                        "arial", "arialbd"
                    )
                    tf = bold if os.path.exists(bold) else path
                    self.font_tile = pygame.font.Font(tf, 50)
                    self.font_tile_sm = pygame.font.Font(tf, 36)
                except Exception:
                    pass
                break

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
        """Convert pixel (px, py) → grid (row, col) or ``None``."""
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
        """Queue a slide animation from grid (fr,fc) → (tr,tc)."""
        src = self.tile_rect(fr, fc, size)
        dst = self.tile_rect(tr, tc, size)
        self.animations.append(
            TileAnimation(value, (src.x, src.y), (dst.x, dst.y))
        )

    def update_animations(self, dt):
        """Tick all animations, removing finished ones."""
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
        """Gradient colour based on tile number."""
        t = value / max(total - 1, 1)
        return tuple(
            int(TILE_GRAD_A[i] + (TILE_GRAD_B[i] - TILE_GRAD_A[i]) * t)
            for i in range(3)
        )

    def _draw_tile(self, rect, value, size, correct, hover, image_mode):
        """Render a single tile (numbered or image)."""
        if value == 0:
            # Empty cell — faint indication
            pygame.draw.rect(
                self.screen, COLORS["empty"], rect, border_radius=self.RADIUS
            )
            return

        if image_mode and value in self.tile_surfaces:
            surf = self.tile_surfaces[value]
            scaled = pygame.transform.smoothscale(
                surf, (int(rect.width), int(rect.height))
            )
            self.screen.blit(scaled, rect.topleft)
            # Correct-position tint
            if correct:
                ov = pygame.Surface(
                    (int(rect.width), int(rect.height)), pygame.SRCALPHA
                )
                ov.fill((40, 200, 80, 50))
                self.screen.blit(ov, rect.topleft)
            # Hover border
            if hover:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    rect,
                    3,
                    border_radius=self.RADIUS,
                )
            return

        # --- Numbered tile ---
        total = size * size
        base = (
            COLORS["tile_correct"]
            if correct
            else (COLORS["tile_hover"] if hover else self._tile_color(value, total))
        )

        # Shadow
        shadow = pygame.Rect(rect.x, rect.y + 3, rect.width, rect.height)
        shadow_c = tuple(max(0, c - 40) for c in base)
        pygame.draw.rect(
            self.screen, shadow_c, shadow, border_radius=self.RADIUS
        )

        # Main body
        pygame.draw.rect(
            self.screen, base, rect, border_radius=self.RADIUS
        )

        # Top highlight band
        hl = pygame.Surface((rect.width - 4, rect.height // 3), pygame.SRCALPHA)
        hl.fill((*[min(255, c + 35) for c in base], 45))
        self.screen.blit(hl, (rect.x + 2, rect.y + 2))

        # Number label
        font = self.font_tile if size <= 3 else self.font_tile_sm
        txt = font.render(str(value), True, COLORS["tile_text"])
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # Full board drawing
    # ------------------------------------------------------------------
    def draw_board(self, board, image_mode=False):
        """Draw the grid background and all tiles (including animations)."""
        size = board.size
        br = self.board_rect(size)
        pygame.draw.rect(
            self.screen, COLORS["board_bg"], br, border_radius=12
        )

        animating = {a.tile_value for a in self.animations}

        for r in range(size):
            for c in range(size):
                val = board.get_tile_value(r, c)
                if val in animating:
                    # Placeholder empty cell while tile animates
                    tr = self.tile_rect(r, c, size)
                    pygame.draw.rect(
                        self.screen,
                        COLORS["empty"],
                        tr,
                        border_radius=self.RADIUS,
                    )
                    continue
                tr = self.tile_rect(r, c, size)
                self._draw_tile(
                    tr,
                    val,
                    size,
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
    # HUD (heads-up display)
    # ------------------------------------------------------------------
    def draw_hud(self, board, image_mode=False):
        """Draw the top bar: title, move counter, timer, control hints."""
        hud = pygame.Rect(0, 0, self.WIN_W, self.HUD_H)
        pygame.draw.rect(self.screen, COLORS["hud_bg"], hud)
        pygame.draw.line(
            self.screen,
            COLORS["hud_accent"],
            (0, self.HUD_H - 1),
            (self.WIN_W, self.HUD_H - 1),
            2,
        )

        # Title
        title = self.font_medium.render("Sliding Puzzle", True, COLORS["title"])
        self.screen.blit(title, (20, 10))

        # Size & mode badges
        badge = self.font_hud.render(
            f"{board.size}×{board.size}  •  {'Image' if image_mode else 'Numbers'}",
            True,
            COLORS["hud_text"],
        )
        self.screen.blit(badge, (20 + title.get_width() + 12, 18))

        # Moves
        self._hud_stat("Moves", str(board.move_count), 20, 55)

        # Timer
        elapsed = board.get_elapsed_time()
        m, s = divmod(int(elapsed), 60)
        self._hud_stat("Time", f"{m:02d}:{s:02d}", 150, 55)

        # Best score
        if board.best_moves is not None:
            bm, bs = board.best_moves, int(board.best_time or 0)
            bmin, bsec = divmod(bs, 60)
            self._hud_stat("Best", f"{bm} / {bmin:02d}:{bsec:02d}", 280, 55)

        # Control hints
        hints = "[R] Restart  [U] Undo  [P] Pause  [M] Menu"
        ht = self.font_hud.render(hints, True, (80, 80, 100))
        self.screen.blit(ht, (self.WIN_W - ht.get_width() - 12, 92))

        # Pause indicator
        if board.paused:
            pt = self.font_medium.render(
                "⏸  PAUSED", True, COLORS["pause_text"]
            )
            self.screen.blit(
                pt, (self.WIN_W - pt.get_width() - 12, 50)
            )

    def _hud_stat(self, label, value, x, y):
        """Draw a label/value pair in the HUD."""
        lt = self.font_hud.render(label, True, COLORS["hud_text"])
        vt = self.font_medium.render(value, True, COLORS["hud_accent"])
        self.screen.blit(lt, (x, y))
        self.screen.blit(vt, (x, y + 18))

    # ------------------------------------------------------------------
    # Win overlay
    # ------------------------------------------------------------------
    def draw_win_screen(self, board):
        """Semi-transparent overlay congratulating the player."""
        win_h = self.WIN_W + self.HUD_H
        overlay = pygame.Surface((self.WIN_W, win_h), pygame.SRCALPHA)
        overlay.fill(COLORS["overlay"])
        self.screen.blit(overlay, (0, 0))

        cx, cy = self.WIN_W // 2, win_h // 2

        # Title
        txt = self.font_large.render("Puzzle Solved!", True, COLORS["win_text"])
        self.screen.blit(txt, txt.get_rect(center=(cx, cy - 60)))

        # Stats
        m, s = divmod(int(board.elapsed_time), 60)
        stat = self.font_medium.render(
            f"Moves: {board.move_count}   Time: {m:02d}:{s:02d}",
            True,
            COLORS["hud_text"],
        )
        self.screen.blit(stat, stat.get_rect(center=(cx, cy)))

        # Instructions
        inst = self.font_small.render(
            "Press [R] to play again  •  [M] for menu", True, COLORS["hud_text"]
        )
        self.screen.blit(inst, inst.get_rect(center=(cx, cy + 50)))

    # ------------------------------------------------------------------
    # Pause overlay
    # ------------------------------------------------------------------
    def draw_pause_overlay(self):
        """Draw a translucent overlay when the game is paused."""
        win_h = self.WIN_W + self.HUD_H
        overlay = pygame.Surface((self.WIN_W, win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        txt = self.font_large.render("PAUSED", True, COLORS["pause_text"])
        cx, cy = self.WIN_W // 2, win_h // 2
        self.screen.blit(txt, txt.get_rect(center=(cx, cy)))

        sub = self.font_small.render(
            "Press [P] to resume", True, COLORS["hud_text"]
        )
        self.screen.blit(sub, sub.get_rect(center=(cx, cy + 50)))

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------
    def draw_menu(self, selected_size=3, image_mode=False):
        """
        Draw the main menu and return a list of ``(Rect, action_str)``
        tuples for click detection.
        """
        self.screen.fill(COLORS["bg"])
        cx = self.WIN_W // 2

        # Title
        title = self.font_large.render("Sliding Puzzle", True, COLORS["title"])
        tr = title.get_rect(center=(cx, 90))
        # Glow
        glow = pygame.Surface(
            (title.get_width() + 60, title.get_height() + 30), pygame.SRCALPHA
        )
        glow.fill((*COLORS["title"], 18))
        self.screen.blit(glow, (tr.x - 30, tr.y - 15))
        self.screen.blit(title, tr)

        sub = self.font_small.render(
            "A Classic Logic Puzzle Game", True, COLORS["hud_text"]
        )
        self.screen.blit(sub, sub.get_rect(center=(cx, 145)))

        # Buttons
        items = [
            ("New Game", "new_game"),
            (f"Grid Size: {selected_size}×{selected_size}", "grid_size"),
            (f"Mode: {'Image' if image_mode else 'Numbers'}", "tile_mode"),
            ("Auto Solve (3×3 only)", "auto_solve"),
            ("Quit", "quit"),
        ]
        bw, bh, spacing = 320, 55, 68
        start_y = 210
        mouse = pygame.mouse.get_pos()
        buttons = []

        for i, (label, action) in enumerate(items):
            rect = pygame.Rect(cx - bw // 2, start_y + i * spacing, bw, bh)
            hov = rect.collidepoint(mouse)
            col = COLORS["button_hover"] if hov else COLORS["button"]
            pygame.draw.rect(self.screen, col, rect, border_radius=10)
            if hov:
                pygame.draw.rect(
                    self.screen, COLORS["hud_accent"], rect, 2, border_radius=10
                )
            txt = self.font_small.render(label, True, COLORS["button_text"])
            self.screen.blit(txt, txt.get_rect(center=rect.center))
            buttons.append((rect, action))

        # Footer
        ft = self.font_hud.render(
            "CSE444 — Vibe Coding Project", True, (60, 60, 80)
        )
        self.screen.blit(
            ft, ft.get_rect(center=(cx, self.WIN_W + self.HUD_H - 28))
        )
        return buttons

    # ------------------------------------------------------------------
    # Goal-state preview (small)
    # ------------------------------------------------------------------
    def draw_goal_preview(self, board, x, y, preview_size=100):
        """Draw a miniature view of the goal (solved) state."""
        size = board.size
        ts = preview_size // size

        bg = pygame.Rect(x - 2, y - 2, preview_size + 4, preview_size + 4)
        pygame.draw.rect(self.screen, COLORS["board_bg"], bg, border_radius=6)

        lbl = self.font_hud.render("Goal", True, COLORS["hud_text"])
        self.screen.blit(lbl, (x, y - 20))

        total = size * size
        for r in range(size):
            for c in range(size):
                val = board.goal[r][c]
                tr = pygame.Rect(x + c * ts, y + r * ts, ts - 1, ts - 1)
                if val == 0:
                    pygame.draw.rect(
                        self.screen, COLORS["empty"], tr, border_radius=3
                    )
                else:
                    clr = self._tile_color(val, total)
                    pygame.draw.rect(self.screen, clr, tr, border_radius=3)
                    if size <= 4:
                        ft = pygame.font.Font(None, max(14, 54 // size))
                        t = ft.render(str(val), True, COLORS["tile_text"])
                        self.screen.blit(t, t.get_rect(center=tr.center))
