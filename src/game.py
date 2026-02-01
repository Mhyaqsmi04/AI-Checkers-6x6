from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

from utils import (
    BOARD_SIZE, WHITE_CELL, EMPTY,
    B_MAN, W_MAN, B_KING, W_KING,
    Player, Move,
    opponent, playable_cell, in_bounds, clone_board,
    piece_owner, is_king, is_black, is_white, promote_if_needed,
    position_key,
)


BLACK_FORWARD = [(-1, -1), (-1, +1)]
WHITE_FORWARD = [(+1, -1), (+1, +1)]
KING_DIRS = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

@dataclass
class GameState:
    board: List[List[int]]
    turn: Player
    ply_since_progress: int = 0
    repetition: Dict[Tuple[int, ...], int] = field(default_factory=dict)
    ply_count: int = 0


def initial_state() -> GameState:
    b = initial_board()
    s = GameState(board=b, turn=1)
    k = position_key(b, s.turn)
    s.repetition[k] = 1
    return s

def initial_board() -> List[List[int]]:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not playable_cell(r, c):
                board[r][c] = WHITE_CELL

    for r in (BOARD_SIZE - 2, BOARD_SIZE - 1):  # 4,5
        for c in range(BOARD_SIZE):
            if playable_cell(r, c):
                board[r][c] = B_MAN

    for r in (0, 1):
        for c in range(BOARD_SIZE):
            if playable_cell(r, c):
                board[r][c] = W_MAN

    return board

def print_board(board: List[List[int]]) -> None:
    mapping = {
        WHITE_CELL: ".",
        EMPTY: "_",
        B_MAN: "b",
        W_MAN: "w",
        B_KING: "B",
        W_KING: "W",
    }
    print("   " + " ".join(str(c) for c in range(BOARD_SIZE)))
    for r in range(BOARD_SIZE):
        row_str = " ".join(mapping[board[r][c]] for c in range(BOARD_SIZE))
        print(f"{r}  {row_str}")

def list_pieces(board: List[List[int]], player: Player) -> List[Tuple[int, int]]:
    res = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == WHITE_CELL or p == EMPTY:
                continue
            own = piece_owner(p)
            if own == player:
                res.append((r, c))
    return res

def piece_dirs(piece: int, player: Player) -> List[Tuple[int, int]]:
    if is_king(piece):
        return KING_DIRS
    return BLACK_FORWARD if player == 1 else WHITE_FORWARD

def generate_simple_moves(board: List[List[int]], player: Player) -> List[Move]:
    moves: List[Move] = []
    for (r, c) in list_pieces(board, player):
        piece = board[r][c]
        for dr, dc in piece_dirs(piece, player):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] == EMPTY:
                moves.append(Move(path=((r, c), (nr, nc)), captures=()))
    return moves

def _single_captures_from(board: List[List[int]], r: int, c: int, player: Player) -> List[Tuple[int,int,int,int,int,int]]:
   
    piece = board[r][c]
    dirs = piece_dirs(piece, player)
    res = []
    for dr, dc in dirs:
        over_r, over_c = r + dr, c + dc
        to_r, to_c = r + 2*dr, c + 2*dc
        if not (in_bounds(over_r, over_c) and in_bounds(to_r, to_c)):
            continue
        over_piece = board[over_r][over_c]
        if over_piece in (WHITE_CELL, EMPTY):
            continue
        if piece_owner(over_piece) == player:
            continue
        if board[to_r][to_c] != EMPTY:
            continue
        res.append((r, c, over_r, over_c, to_r, to_c))
    return res

def _dfs_capture_chains(board: List[List[int]], start: Tuple[int,int], player: Player) -> List[Move]:
    
    sr, sc = start
    piece = board[sr][sc]
    if piece == EMPTY or piece == WHITE_CELL:
        return []

    chains: List[Move] = []

    def dfs(cur_board: List[List[int]], cur_pos: Tuple[int,int],
            cur_path: List[Tuple[int,int]], cur_caps: List[Tuple[int,int]]):
        cr, cc = cur_pos
        jumps = _single_captures_from(cur_board, cr, cc, player)
        if not jumps:
            if cur_caps:
                chains.append(Move(path=tuple(cur_path), captures=tuple(cur_caps)))
            return

        for fr, fc, over_r, over_c, tr, tc in jumps:
            nb = clone_board(cur_board)
            moving_piece = nb[fr][fc]
            nb[fr][fc] = EMPTY
            nb[over_r][over_c] = EMPTY
            nb[tr][tc] = moving_piece

            dfs(nb, (tr, tc), cur_path + [(tr, tc)], cur_caps + [(over_r, over_c)])

    dfs(board, (sr, sc), [(sr, sc)], [])
    return chains

def generate_capture_moves(board: List[List[int]], player: Player) -> List[Move]:
    ture chains exist, keep those with maximum number of captures.
    
    Rule: captures are mandatory.
    Also enforce 'maximum capture' across chains (already done in capture generator).
    
    Apply a move and return the next state.
    Captured pieces are removed, then promotion is checked at end.
 
    Returns:
      None -> not terminal
      +1  -> black wins
      -1  -> white wins
       0  -> draw (optional, not implemented here)
    Terminal if:
      - a player has no pieces
      - a player has no legal moves
    