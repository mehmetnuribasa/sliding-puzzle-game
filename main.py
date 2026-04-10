"""
Sliding Puzzle Game — Main Entry Point

A classic logic-based sliding puzzle built with Python and PyGame.
Supports 3×3 and 4×4 grids, numbered and image tile modes,
smooth animations, undo, pause, timer, and an A* auto-solver
demo for 3×3 puzzles.

CSE444 — Vibe Coding Project
"""

import sys
import os
import pygame

from game import Board
from ui import Renderer, COLORS
from solver import solve_astar

# ======================================================================
# Constants
# ======================================================================
FPS = 60
WINDOW_TITLE = "Sliding Puzzle Game — CSE444"
DEFAULT_SIZE = 3
IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets", "images", "puzzle_default.png",
)

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_WON = "won"


# ======================================================================
# Sound helpers (procedural — no external files needed)
# ======================================================================
def _make_beep(frequency=440, duration_ms=80, volume=0.15):
    """Generate a short sine-wave beep as a pygame Sound object."""
    try:
        import array
        import math as _math

        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000)
        buf = array.array("h", [0] * n_samples)
        for i in range(n_samples):
            t = i / sample_rate
            val = int(32767 * volume * _math.sin(2 * _math.pi * frequency * t))
            # Fade out last 20 %
            if i > n_samples * 0.8:
                val = int(val * (n_samples - i) / (n_samples * 0.2))
            buf[i] = val
        snd = pygame.mixer.Sound(buffer=buf)
        return snd
    except Exception:
        return None


# ======================================================================
# Main application class
# ======================================================================
class SlidingPuzzleApp:
    """Top-level application managing the game loop and state machine."""

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.display.set_caption(WINDOW_TITLE)

        self.win_w = Renderer.WIN_W
        self.win_h = Renderer.WIN_W + Renderer.HUD_H
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))
        self.clock = pygame.time.Clock()

        self.renderer = Renderer(self.screen)
        self.board = Board(DEFAULT_SIZE)
        self.state = STATE_MENU
        self.selected_size = DEFAULT_SIZE
        self.image_mode = False
        self.menu_buttons = []

        # Auto-solve state
        self.auto_solving = False
        self.auto_solve_moves = []
        self.auto_solve_timer = 0.0
        self.auto_solve_delay = 0.35  # seconds between moves

        # Sounds
        self.snd_slide = _make_beep(500, 60, 0.10)
        self.snd_win = _make_beep(880, 300, 0.18)
        self.snd_click = _make_beep(600, 40, 0.08)

        # Load image for image mode
        if os.path.exists(IMAGE_PATH):
            self.renderer.load_puzzle_image(IMAGE_PATH, self.selected_size)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _play(self, snd):
        """Play a sound if available."""
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def _start_new_game(self):
        """Initialise a new game with current settings."""
        self.board = Board(self.selected_size)
        self.state = STATE_PLAYING
        self.auto_solving = False
        self.auto_solve_moves = []
        if self.image_mode and os.path.exists(IMAGE_PATH):
            self.renderer.load_puzzle_image(IMAGE_PATH, self.selected_size)

    def _toggle_size(self):
        """Cycle grid size: 3 → 4 → 3."""
        self.selected_size = 4 if self.selected_size == 3 else 3

    def _do_tile_move(self, row, col):
        """Attempt to move tile at (row, col), triggering animation."""
        if self.renderer.is_animating():
            return
        br, bc = self.board.find_blank()
        val = self.board.get_tile_value(row, col)
        if self.board.move_tile(row, col):
            self.renderer.start_animation(
                val, row, col, br, bc, self.board.size
            )
            self._play(self.snd_slide)
            if self.board.solved:
                self._play(self.snd_win)

    def _do_direction_move(self, direction):
        """Move by keyboard direction."""
        if self.renderer.is_animating():
            return
        br, bc = self.board.find_blank()
        moved, fr, fc = self.board.move_by_direction(direction)
        if moved:
            val = self.board.get_tile_value(br, bc)  # tile is now at blank pos
            self.renderer.start_animation(
                val, fr, fc, br, bc, self.board.size
            )
            self._play(self.snd_slide)
            if self.board.solved:
                self._play(self.snd_win)

    def _do_undo(self):
        """Undo last move with animation."""
        if self.renderer.is_animating():
            return
        # Before undo, record where the blank currently is
        br, bc = self.board.find_blank()
        ok, from_r, from_c = self.board.undo()
        if ok:
            # The tile moved from (from_r, from_c) back to its old pos
            # from_r, from_c is the old blank that now holds the tile
            val = self.board.get_tile_value(from_r, from_c)
            self.renderer.start_animation(
                val, br, bc, from_r, from_c, self.board.size
            )
            self._play(self.snd_click)

    def _start_auto_solve(self):
        """Begin auto-solve demo (3×3 only)."""
        if self.board.size > 3:
            return
        solution = solve_astar(self.board.grid, self.board.size)
        if solution is not None:
            self.auto_solving = True
            self.auto_solve_moves = solution
            self.auto_solve_timer = 0.0
            self.state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Event handlers per state
    # ------------------------------------------------------------------
    def _handle_menu_events(self, event):
        """Process events while in the main menu."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.menu_buttons:
                if rect.collidepoint(event.pos):
                    self._play(self.snd_click)
                    if action == "new_game":
                        self._start_new_game()
                    elif action == "grid_size":
                        self._toggle_size()
                    elif action == "tile_mode":
                        self.image_mode = not self.image_mode
                    elif action == "auto_solve":
                        self._start_new_game()
                        self._start_auto_solve()
                    elif action == "quit":
                        pygame.quit()
                        sys.exit()
                    break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._start_new_game()
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    def _handle_playing_events(self, event):
        """Process events during active gameplay."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.board.toggle_pause()
            elif event.key == pygame.K_m:
                self.state = STATE_MENU
                self.auto_solving = False
            elif event.key == pygame.K_r:
                self._start_new_game()
            elif event.key == pygame.K_u:
                if not self.auto_solving:
                    self._do_undo()
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_MENU
                self.auto_solving = False
            elif not self.board.paused and not self.auto_solving:
                direction_map = {
                    pygame.K_UP: "up",
                    pygame.K_DOWN: "down",
                    pygame.K_LEFT: "left",
                    pygame.K_RIGHT: "right",
                    pygame.K_w: "up",
                    pygame.K_s: "down",
                    pygame.K_a: "left",
                    pygame.K_d: "right",
                }
                if event.key in direction_map:
                    self._do_direction_move(direction_map[event.key])

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.board.paused and not self.auto_solving:
                pos = self.renderer.pixel_to_grid(
                    event.pos[0], event.pos[1], self.board.size
                )
                if pos is not None:
                    self._do_tile_move(pos[0], pos[1])

        if event.type == pygame.MOUSEMOTION:
            pos = self.renderer.pixel_to_grid(
                event.pos[0], event.pos[1], self.board.size
            )
            self.renderer.hover_tile = pos

    def _handle_won_events(self, event):
        """Process events on the win screen."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._start_new_game()
            elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                self.state = STATE_MENU
                self.auto_solving = False

    # ------------------------------------------------------------------
    # Update / auto-solve tick
    # ------------------------------------------------------------------
    def _update(self, dt):
        """Per-frame update logic (animations, auto-solve)."""
        self.renderer.update_animations(dt)

        # Auto-solve step
        if self.auto_solving and self.state == STATE_PLAYING:
            if not self.renderer.is_animating():
                self.auto_solve_timer += dt
                if self.auto_solve_timer >= self.auto_solve_delay:
                    self.auto_solve_timer = 0.0
                    if self.auto_solve_moves:
                        direction = self.auto_solve_moves.pop(0)
                        self._do_direction_move(direction)
                    else:
                        self.auto_solving = False

        # Transition to WON state after last animation finishes
        if (
            self.state == STATE_PLAYING
            and self.board.solved
            and not self.renderer.is_animating()
        ):
            self.state = STATE_WON

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self):
        """Draw everything for the current frame."""
        self.screen.fill(COLORS["bg"])

        if self.state == STATE_MENU:
            self.menu_buttons = self.renderer.draw_menu(
                self.selected_size, self.image_mode
            )
        elif self.state in (STATE_PLAYING, STATE_WON):
            self.renderer.draw_hud(self.board, self.image_mode)
            self.renderer.draw_board(self.board, self.image_mode)

            # Goal preview in top-right
            self.renderer.draw_goal_preview(
                self.board,
                self.win_w - 115,
                self.renderer.HUD_H - 102,
                preview_size=90,
            )

            if self.board.paused:
                self.renderer.draw_pause_overlay()
            elif self.state == STATE_WON:
                self.renderer.draw_win_screen(self.board)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """Run the application until the user quits."""
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == STATE_MENU:
                    self._handle_menu_events(event)
                elif self.state == STATE_PLAYING:
                    self._handle_playing_events(event)
                elif self.state == STATE_WON:
                    self._handle_won_events(event)

            self._update(dt)
            self._render()


# ======================================================================
# Script entry point
# ======================================================================
if __name__ == "__main__":
    app = SlidingPuzzleApp()
    app.run()
