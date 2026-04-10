# Sliding Puzzle Game

A classic logic-based sliding puzzle game built with **Python** and **PyGame**.
Players rearrange shuffled tiles on a grid to restore the correct numerical
(or image-based) order. The project was developed as part of the **CSE444 Vibe
Coding** take-home exam.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyGame](https://img.shields.io/badge/PyGame-2.5%2B-green)

---

## Features

| Category       | Feature                                                     |
|---------------|-------------------------------------------------------------|
| **Core**       | 3×3 and 4×4 grid sizes                                     |
| **Core**       | Random shuffle with guaranteed solvability                  |
| **Core**       | Mouse click **and** keyboard (arrows / WASD) controls       |
| **Core**       | Illegal move prevention                                     |
| **Core**       | Real-time move counter and timer                            |
| **Core**       | Win detection with congratulations screen                   |
| **Modes**      | Numbered tiles mode                                         |
| **Modes**      | Image tiles mode (landscape photo sliced into tiles)        |
| **UX**         | Smooth ease-out slide animations                            |
| **UX**         | Tile hover highlighting                                     |
| **UX**         | Correct-position visual feedback (green tint)               |
| **UX**         | Procedural sound effects (no external audio files)          |
| **UX**         | Goal-state preview in the top-right corner                  |
| **Controls**   | Undo last move (`U`)                                        |
| **Controls**   | Pause / resume (`P`)                                        |
| **Controls**   | Restart / reshuffle (`R`)                                   |
| **Controls**   | Return to menu (`M` or `Esc`)                               |
| **Advanced**   | A* auto-solve demo for 3×3 puzzles                          |
| **Advanced**   | Best score tracking (in-memory, per session)                |
| **Advanced**   | FPS-independent game loop (60 FPS)                          |

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

| Key / Action          | Effect                                   |
|-----------------------|------------------------------------------|
| **Mouse click**       | Slide an adjacent tile into the gap      |
| **Arrow keys / WASD** | Slide tile in the corresponding direction|
| **R**                 | Restart (reshuffle) the current puzzle   |
| **U**                 | Undo the last move                       |
| **P**                 | Pause / resume the timer                 |
| **M** or **Esc**      | Return to the main menu                  |
| **Enter** (menu)      | Quick-start a new game                   |
| **Q** (menu)          | Quit the application                     |

---

## Project Structure

```
sliding-puzzle-game/
├── main.py              # Entry point — game loop & state machine
├── game.py              # Board class — state, moves, undo, timer
├── ui.py                # Renderer — drawing, animations, menus
├── solver.py            # Solvability check & A* solver
├── assets/
│   └── images/
│       └── puzzle_default.png   # Default image for image mode
├── requirements.txt
├── README.md            # ← You are here
├── CSE444 Take-home Exam.pdf
├── Sliding Puzzle Game.pdf
└── Project_Report.pdf
```

---

## How It Works

1. **Shuffle & Solvability** — Tiles are shuffled randomly; an inversion-count
   algorithm guarantees every generated puzzle is solvable (odd-width parity
   for 3×3, even-width blank-row adjustment for 4×4).

2. **State Machine** — The app cycles through three states:
   `MENU → PLAYING → WON`, each with its own event handling and rendering.

3. **Animations** — Tile movements use ease-out cubic interpolation for a
   polished feel. The renderer keeps a queue of `TileAnimation` objects and
   draws animated tiles on top of the static grid.

4. **Auto-Solve** — For 3×3 puzzles, an A* search with the Manhattan-distance
   heuristic finds an optimal (or near-optimal) solution and replays it
   step-by-step on screen.

---

## Acknowledgements

- **PyGame** — [pygame.org](https://www.pygame.org/)
- Solvability algorithm based on the well-known inversion-count method
  described in various puzzle theory references.
- Developed with AI-assisted *vibe coding* methodology as part of CSE444.

---

## License

This project is submitted for academic purposes (CSE444 Take-Home Exam).
