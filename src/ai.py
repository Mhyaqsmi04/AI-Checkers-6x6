from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Tuple

from game import GameState, generate_legal_moves, apply_move, terminal_status
from utils import Move

EvalFn = Callable[[GameState], float]  # state -> score (positive good for black)

@dataclass
class SearchStats:
    nodes: int = 0

def minimax(state: GameState, depth: int, maximizing: bool, eval_fn: EvalFn, stats: SearchStats) -> float:
    stats.nodes += 1

    term = terminal_status(state)
    if term is not None:
        # terminal: big values
        if term == 1:   # black win
            return 10_000
        if term == -1:  # white win
            return -10_000
        return 0

    if depth == 0:
        return eval_fn(state)

    moves = generate_legal_moves(state.board, state.turn)
    if not moves:
        # no moves -> terminal already handled, but safe:
        return -10_000 if state.turn == 1 else 10_000

    if maximizing:
        best = float("-inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            val = minimax(nxt, depth - 1, False, eval_fn, stats)
            best = max(best, val)
        return best
    else:
        best = float("inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            val = minimax(nxt, depth - 1, True, eval_fn, stats)
            best = min(best, val)
        return best

def alphabeta(state: GameState, depth: int, alpha: float, beta: float, maximizing: bool, eval_fn: EvalFn, stats: SearchStats) -> float:
    stats.nodes += 1

    term = terminal_status(state)
    if term is not None:
        if term == 1:
            return 10_000
        if term == -1:
            return -10_000
        return 0

    if depth == 0:
        return eval_fn(state)

    moves = generate_legal_moves(state.board, state.turn)
    if not moves:
        return -10_000 if state.turn == 1 else 10_000

    if maximizing:
        value = float("-inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            value = max(value, alphabeta(nxt, depth - 1, alpha, beta, False, eval_fn, stats))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float("inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            value = min(value, alphabeta(nxt, depth - 1, alpha, beta, True, eval_fn, stats))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def choose_move(state: GameState, depth: int, eval_fn: EvalFn, use_ab: bool) -> Tuple[Move, SearchStats, float]:
    """
    Black is maximizing, white is minimizing. We decide based on whose turn it is.
    Returns: best_move, stats, best_value
    """
    moves = generate_legal_moves(state.board, state.turn)
    if not moves:
        raise RuntimeError("No legal moves to choose from")

    stats = SearchStats()
    best_move = moves[0]

    maximizing = (state.turn == 1)

    # Simple move ordering (helps AlphaBeta prune better without changing correctness):
    # evaluate children at depth-1 with eval_fn and sort.
    def ordered(mvs):
        if not use_ab or depth <= 1:
            return mvs
        scored = []
        for m in mvs:
            nxt = apply_move(state, m)
            scored.append((eval_fn(nxt), m))
        scored.sort(reverse=maximizing, key=lambda x: x[0])
        return [m for _, m in scored]

    moves = ordered(moves)
    if maximizing:
        best_val = float("-inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            if use_ab:
                val = alphabeta(nxt, depth - 1, float("-inf"), float("inf"), False, eval_fn, stats)
            else:
                val = minimax(nxt, depth - 1, False, eval_fn, stats)
            if val > best_val:
                best_val = val
                best_move = mv
    else:
        best_val = float("inf")
        for mv in moves:
            nxt = apply_move(state, mv)
            if use_ab:
                val = alphabeta(nxt, depth - 1, float("-inf"), float("inf"), True, eval_fn, stats)
            else:
                val = minimax(nxt, depth - 1, True, eval_fn, stats)
            if val < best_val:
                best_val = val
                best_move = mv

    return best_move, stats, best_val
