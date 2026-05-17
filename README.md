# Sliding Puzzle Game

A classic logic-based sliding puzzle game built with **Python** and **PyGame**.
Players rearrange shuffled tiles on a grid to restore the correct numerical
(or image-based) order. Originally developed as part of the **CSE444 Vibe
Coding** take-home exam and subsequently enhanced through a **software
maintenance and evolution** assignment.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyGame](https://img.shields.io/badge/PyGame-2.5%2B-green)

---

## Features

| Category        | Feature                                                        |
|-----------------|----------------------------------------------------------------|
| **Core**        | 3×3 and 4×4 grid sizes                                        |
| **Core**        | Random shuffle with guaranteed solvability                     |
| **Core**        | Mouse click **and** keyboard (arrows / WASD) controls          |
| **Core**        | Illegal move prevention                                        |
| **Core**        | Real-time move counter and timer                               |
| **Core**        | Win detection with congratulations screen                      |
| **Modes**       | Numbered tiles mode                                            |
| **Modes**       | Multi-image support (cycles through multiple photo options)    |
| **UX**          | Premium glassmorphism UI with shadow and glow effects          |
| **UX**          | Smooth ease-out slide animations                               |
| **UX**          | Tile hover highlighting                                        |
| **UX**          | Correct-position visual feedback (green tint)                  |
| **UX**          | Procedural sound effects (no external audio files)             |
| **UX**          | Goal-state preview (thumbnail) in the top-right corner         |
| **Controls**    | Undo last move (`U`)                                           |
| **Controls**    | Pause / resume (`P`)                                           |
| **Controls**    | Restart / reshuffle (`R`)                                      |
| **Controls**    | Return to menu (`M` or `Esc`)                                  |
| **Advanced**    | A* auto-solve demo for 3×3 puzzles                             |
| **Advanced**    | Persistent Auto-Solve mode for screen-saver loops              |
| **Advanced**    | Best score tracking (in-memory, per session)                   |
| **Advanced**    | FPS-independent game loop (60 FPS)                             |

### Maintenance Additions (CSE444 Homework)

| Feature                     | Description                                                                                       |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| **Difficulty Modes**        | Three levels — Easy (3×3, limited shuffle), Medium (3×3, full shuffle), Hard (4×4, full shuffle). Selectable from the menu with color-coded indicators. |
| **Custom Image Selection**  | Users can load any image from their computer via a native file-picker dialog. The image is automatically sliced into tiles and a thumbnail preview is shown for guidance. |
| **Multi-Tile Sliding**      | Clicking a tile that is in the same row or column as the blank slides **all tiles in between** towards the gap in a single move, with smooth animations.  |
| **Auto-Solve (Preserved)**  | The original A* auto-solver for 3×3 puzzles continues to work correctly with the new movement system. |

---

## Requirements

- **Python 3.10** or newer
- **PyGame 2.5** or newer

---

## Installation & Running

```bash
# 1. Clone or download the project
git clone https://github.com/your-username/sliding-puzzle-game.git
cd sliding-puzzle-game

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the game
python main.py
```

---

## Controls

| Key / Action          | Effect                                                    |
|-----------------------|-----------------------------------------------------------|
| **Mouse click**       | Slide tile(s) towards the blank (supports multi-tile)     |
| **Arrow keys / WASD** | Slide the adjacent tile in the corresponding direction    |
| **R**                 | Restart (reshuffle) the current puzzle                    |
| **U**                 | Undo the last move (including multi-tile moves)           |
| **P**                 | Pause / resume the timer                                  |
| **M** or **Esc**      | Return to the main menu                                   |
| **Mouse click (HUD)** | HUD shortcuts (R, U, P, M) are fully clickable           |
| **Up/Down/Enter**     | Navigate and select buttons in the main menu              |
| **Q** (menu)          | Quit the application                                      |

---

## Project Structure

```
sliding-puzzle-game/
├── main.py              # Entry point — game loop, state machine, custom image loading
├── game.py              # Board class — state, moves, multi-tile slide, undo, timer
├── ui.py                # Renderer — drawing, animations, menus, HUD
├── solver.py            # Solvability check & A* solver
├── assets/
│   └── images/
│       └── puzzle_default.png   # Default image for image mode
├── requirements.txt
├── README.md            # ← You are here
├── Maintenance_Report.pdf
├── CSE444 Homework - Take-home Maintenance.pdf
├── Project Requirements Updates.pdf
├── CSE444 Take-home Exam.pdf
├── Sliding Puzzle Game.pdf
└── Project_Report.pdf
```

---

## How It Works

1. **Shuffle & Solvability** — Tiles are shuffled randomly; an inversion-count
   algorithm guarantees every generated puzzle is solvable (odd-width parity
   for 3×3, even-width blank-row adjustment for 4×4). Easy mode uses a
   controlled limited-move shuffle for reduced complexity.

2. **State Machine** — The app cycles through three states:
   `MENU → PLAYING → WON`, each with its own event handling and rendering.

3. **Animations** — Tile movements use ease-out cubic interpolation for a
   polished feel. The renderer keeps a queue of `TileAnimation` objects and
   draws animated tiles on top of the static grid. Multi-tile slides spawn
   concurrent animations for all affected tiles.

4. **Auto-Solve** — For 3×3 puzzles, an A* search with the Manhattan-distance
   heuristic finds an optimal (or near-optimal) solution and replays it
   step-by-step on screen.

5. **Multi-Tile Sliding** — When a user clicks a tile that shares a row or
   column with the blank, all tiles between the clicked tile and the blank
   shift towards the gap simultaneously. This counts as a single move.

6. **Custom Image Loading** — A `tkinter` file-dialog lets users pick any
   image from their computer. The image is scaled, sliced per-tile, and
   immediately applied. A goal-state thumbnail is always visible.

---

## Maintenance Tasks Summary

This project was enhanced as part of the CSE444 Software Maintenance homework.
The following modifications were made to the original codebase:

- **Difficulty System**: Introduced `DIFFICULTY_PRESETS` in `game.py` and a
  `_cycle_difficulty` method in `main.py`. The menu dynamically reflects the
  selected difficulty with color-coded indicators.
- **Custom Image Selection**: Added `tkinter.filedialog` integration in
  `main.py` (`_load_custom_image`) to let users load external images at
  runtime. The menu includes a dedicated "Load Custom Image" sub-button.
- **Multi-Tile Sliding**: Refactored `move_tile()` in `game.py` to detect
  same-row/column alignment with the blank and shift all intermediate tiles.
  Updated `main.py` to handle lists of animated tiles. Undo correctly
  reverses multi-tile moves.
- **UI/UX Overhaul**: Redesigned the main menu with visual grouping (PLAY /
  SETTINGS sections), unicode icons, a gradient hero button for "New Game",
  and an outline-only "Quit" button.
- **Preserved Functionality**: Auto-solve, undo, pause, timer, win detection,
  and all original features remain fully functional.

---

## Acknowledgements

- **PyGame** — [pygame.org](https://www.pygame.org/)
- Solvability algorithm based on the well-known inversion-count method
  described in various puzzle theory references.
- Developed with AI-assisted *vibe coding* methodology as part of CSE444.

---

## License

This project is submitted for academic purposes (CSE444 Take-Home Exam &
Maintenance Homework).
