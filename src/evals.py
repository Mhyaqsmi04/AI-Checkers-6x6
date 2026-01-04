from __future__ import annotations
from typing import List
from utils import BOARD_SIZE, B_MAN, W_MAN, B_KING, W_KING, EMPTY, WHITE_CELL
from game import generate_legal_moves

def eval_v1(board: List[List[int]]) -> float:
    # simple material count
    b_m = b_k = w_m = w_k = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == B_MAN: b_m += 1
            elif p == B_KING: b_k += 1
            elif p == W_MAN: w_m += 1
            elif p == W_KING: w_k += 1
    return (b_m + 3*b_k) - (w_m + 3*w_k)

def eval_v2(board: List[List[int]]) -> float:
    # material + mobility + advancement (very simple but good)
    b_m = b_k = w_m = w_k = 0
    advance_b = advance_w = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == B_MAN:
                b_m += 1
                # black advances toward row 0 => more advanced if smaller r
                advance_b += (BOARD_SIZE - 1 - r)
            elif p == B_KING:
                b_k += 1
            elif p == W_MAN:
                w_m += 1
                # white advances toward row 5 => more advanced if larger r
                advance_w += r
            elif p == W_KING:
                w_k += 1

    # mobility: number of legal moves for each side
    mob_b = len(generate_legal_moves(board, 1))
    mob_w = len(generate_legal_moves(board, 2))

    score = 1*(b_m - w_m) + 3*(b_k - w_k) + 0.1*(mob_b - mob_w) + 0.05*(advance_b - advance_w)
    return score
