from __future__ import annotations

from typing import List, Tuple

from game import GameState, generate_legal_moves
from utils import BOARD_SIZE, B_MAN, W_MAN, B_KING, W_KING


# All evaluation functions return a score from Black's point of view:
#   higher => better for Black (Maximizer)


def _material(board: List[List[int]]) -> Tuple[int, int, int, int]:
    b_m = b_k = w_m = w_k = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == B_MAN:
                b_m += 1
            elif p == B_KING:
                b_k += 1
            elif p == W_MAN:
                w_m += 1
            elif p == W_KING:
                w_k += 1
    return b_m, b_k, w_m, w_k


def eval_v1(state: GameState) -> float:
    """Very simple: material only."""
    board = state.board
    b_m, b_k, w_m, w_k = _material(board)
    return (b_m + 3 * b_k) - (w_m + 3 * w_k)


def eval_v2(state: GameState) -> float:
    """Material + mobility + advancement (simple but decent)."""
    board = state.board

    b_m, b_k, w_m, w_k = _material(board)

    advance_b = advance_w = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == B_MAN:
                # black advances toward row 0 => more advanced if smaller r
                advance_b += (BOARD_SIZE - 1 - r)
            elif p == W_MAN:
                # white advances toward row 5 => more advanced if larger r
                advance_w += r

    # mobility: number of legal moves for each side
    mob_b = len(generate_legal_moves(board, 1))
    mob_w = len(generate_legal_moves(board, 2))

    return (
        1.0 * (b_m - w_m)
        + 3.0 * (b_k - w_k)
        + 0.10 * (mob_b - mob_w)
        + 0.05 * (advance_b - advance_w)
    )


def eval_v3_positional(state: GameState) -> float:
    """A stronger handcrafted eval: material + center + mobility + threat.

    Features:
      - material (kings valued more)
      - center control (pieces closer to center are better)
      - mobility
      - immediate vulnerability: penalize pieces that can be captured next move
    """
    board = state.board
    b_m, b_k, w_m, w_k = _material(board)

    # center bonus
    center_squares = {(2, 1), (2, 3), (3, 2), (3, 4)}  # playable-ish near center on 6x6
    center = 0.0
    for (r, c) in center_squares:
        p = board[r][c]
        if p in (B_MAN, B_KING):
            center += 1.0
        elif p in (W_MAN, W_KING):
            center -= 1.0

    mob_b = len(generate_legal_moves(board, 1))
    mob_w = len(generate_legal_moves(board, 2))

    # vulnerability: if opponent has capture moves, pieces are "in danger".
    # We approximate using: number of opponent capture moves available.
    # More opponent captures => worse.
    # (generate_legal_moves already enforces mandatory captures, so if any capture exists,
    # it returns only captures.)
    opp_caps_against_black = 0
    opp_moves_w = generate_legal_moves(board, 2)
    if opp_moves_w and opp_moves_w[0].is_capture:
        opp_caps_against_black = max(len(m.captures) for m in opp_moves_w)

    opp_caps_against_white = 0
    opp_moves_b = generate_legal_moves(board, 1)
    if opp_moves_b and opp_moves_b[0].is_capture:
        opp_caps_against_white = max(len(m.captures) for m in opp_moves_b)

    threat = -0.25 * opp_caps_against_black + 0.25 * opp_caps_against_white

    return (
        1.0 * (b_m - w_m)
        + 3.0 * (b_k - w_k)
        + 0.15 * (mob_b - mob_w)
        + 0.20 * center
        + threat
    )
