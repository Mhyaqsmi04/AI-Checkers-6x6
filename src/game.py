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

# Directions:
# With our coordinate system: row 0 top, row 5 bottom.
# Black starts at bottom rows (4,5) and moves UP (row-1).
# White starts at top rows (0,1) and moves DOWN (row+1).
BLACK_FORWARD = [(-1, -1), (-1, +1)]
WHITE_FORWARD = [(+1, -1), (+1, +1)]
KING_DIRS = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]

@dataclass
class GameState:
    board: List[List[int]]
    turn: Player  # 1 black, 2 white

    # --- draw helpers (optional in spec, implemented to prevent infinite loops) ---
    # counts plies since a capture or promotion (a "progress" event)
    ply_since_progress: int = 0
    # repetition count for (board, side_to_move)
    repetition: Dict[Tuple[int, ...], int] = field(default_factory=dict)
    ply_count: int = 0


def initial_state() -> GameState:
    """Initial game state with repetition table seeded."""
    b = initial_board()
    s = GameState(board=b, turn=1)
    k = position_key(b, s.turn)
    s.repetition[k] = 1
    return s

def initial_board() -> List[List[int]]:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    # mark non-playable cells as -1
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not playable_cell(r, c):
                board[r][c] = WHITE_CELL

    # place pieces: each player has 6 pieces in two rows
    # Black on bottom two rows (rows 4 and 5) on playable cells
    for r in (BOARD_SIZE - 2, BOARD_SIZE - 1):  # 4,5
        for c in range(BOARD_SIZE):
            if playable_cell(r, c):
                board[r][c] = B_MAN

    # White on top two rows (rows 0 and 1)
    for r in (0, 1):
        for c in range(BOARD_SIZE):
            if playable_cell(r, c):
                board[r][c] = W_MAN

    return board

def print_board(board: List[List[int]]) -> None:
    # simple CLI view
    # . = non-playable, _ = empty playable
    # b/w for men, B/W for kings
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
    """
    Returns list of possible single jumps:
    (from_r, from_c, over_r, over_c, to_r, to_c)
    """
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
    """
    Build ALL capture chains starting from start using DFS.
    Rule: men only capture forward; kings capture both (handled by piece_dirs).
    Also: during chain, we remove captured pieces.
    """
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
            # no more captures -> terminal chain
            if cur_caps:
                chains.append(Move(path=tuple(cur_path), captures=tuple(cur_caps)))
            return

        for fr, fc, over_r, over_c, tr, tc in jumps:
            # apply jump on a copied board
            nb = clone_board(cur_board)
            moving_piece = nb[fr][fc]
            nb[fr][fc] = EMPTY
            nb[over_r][over_c] = EMPTY
            nb[tr][tc] = moving_piece

            dfs(nb, (tr, tc), cur_path + [(tr, tc)], cur_caps + [(over_r, over_c)])

    dfs(board, (sr, sc), [(sr, sc)], [])
    return chains

def generate_capture_moves(board: List[List[int]], player: Player) -> List[Move]:
    """
    Returns ONLY capture moves, but respecting 'maximum capture' rule:
    if multiple capture chains exist, keep those with maximum number of captures.
    """
    all_chains: List[Move] = []
    for pos in list_pieces(board, player):
        all_chains.extend(_dfs_capture_chains(board, pos, player))

    if not all_chains:
        return []

    max_caps = max(len(m.captures) for m in all_chains)
    best = [m for m in all_chains if len(m.captures) == max_caps]
    return best

def generate_legal_moves(board: List[List[int]], player: Player) -> List[Move]:
    """
    Rule: captures are mandatory.
    Also enforce 'maximum capture' across chains (already done in capture generator).
    """
    caps = generate_capture_moves(board, player)
    if caps:
        return caps
    return generate_simple_moves(board, player)

def apply_move(state: GameState, move: Move) -> GameState:
    """
    Apply a move and return the next state.
    Captured pieces are removed, then promotion is checked at end.
    """
    board = clone_board(state.board)
    (sr, sc) = move.path[0]
    piece_before = board[sr][sc]
    board[sr][sc] = EMPTY

    # remove captured pieces
    for (cr, cc) in move.captures:
        board[cr][cc] = EMPTY

    # land on final square
    (er, ec) = move.path[-1]
    piece_after = promote_if_needed(piece_before, er)
    board[er][ec] = piece_after

    next_turn = opponent(state.turn)

    # --- update draw bookkeeping ---
    progress = move.is_capture or (piece_after != piece_before)
    ply_since_progress = 0 if progress else (state.ply_since_progress + 1)

    repetition = dict(state.repetition)
    key = position_key(board, next_turn)
    repetition[key] = repetition.get(key, 0) + 1

    return GameState(
        board=board,
        turn=next_turn,
        ply_since_progress=ply_since_progress,
        repetition=repetition,
        ply_count=state.ply_count + 1,
    )

def count_pieces(board: List[List[int]]) -> Dict[str, int]:
    res = {"b_man":0, "b_king":0, "w_man":0, "w_king":0}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p == B_MAN: res["b_man"] += 1
            elif p == B_KING: res["b_king"] += 1
            elif p == W_MAN: res["w_man"] += 1
            elif p == W_KING: res["w_king"] += 1
    return res

def terminal_status(state: GameState, repetition_limit: int = 3, no_progress_plies: int = 80) -> Optional[int]:
    """
    Returns:
      None -> not terminal
      +1  -> black wins
      -1  -> white wins
       0  -> draw (optional, not implemented here)
    Terminal if:
      - a player has no pieces
      - a player has no legal moves
    """
    board = state.board
    player_to_move = state.turn

    # draw by repetition
    if repetition_limit > 0:
        k = position_key(board, player_to_move)
        if state.repetition.get(k, 0) >= repetition_limit:
            return 0

    # draw by no progress
    if no_progress_plies > 0 and state.ply_since_progress >= no_progress_plies:
        return 0

    counts = count_pieces(board)
    black_total = counts["b_man"] + counts["b_king"]
    white_total = counts["w_man"] + counts["w_king"]
    if black_total == 0:
        return -1
    if white_total == 0:
        return +1

    moves = generate_legal_moves(board, player_to_move)
    if not moves:
        # player to move is stuck -> loses
        return -1 if player_to_move == 1 else +1

    return None
