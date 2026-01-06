# 6x6 Checkers – Intelligent Agent (Minimax / Alpha-Beta)

This project implements a 6x6 Checkers environment and an intelligent agent using Minimax and Alpha-Beta Pruning.

## Features
- Full 6x6 board environment (only playable dark squares)
- Legal move generation
  - Forced captures (mandatory)
  - Multi-jump captures (chain capture in one turn)
  - Maximum-capture rule (only moves with maximum number of captures are allowed)
- King promotion and king movement (both directions)
- Terminal state detection:
  - No pieces
  - No legal moves
- AI:
  - Minimax (depth configurable, minimum depth = 3)
  - Alpha-Beta pruning (same best move as Minimax, fewer expanded nodes)
  - Node counting for comparison
- Modes:
  - Human vs Agent
  - Agent vs Agent

## Project Structure
- `src/game.py` : game rules, move generation, apply moves, terminal checks
- `src/ai.py` : minimax + alpha-beta + node counting
- `src/evals.py` : evaluation functions
- `src/utils.py` : constants, Move structure, helpers
- `src/main.py` : CLI menu and running modes

## How to Run
From the project root:

```bash
python ./src/main.py
