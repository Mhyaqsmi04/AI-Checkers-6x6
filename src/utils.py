from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

BOARD_SIZE = 6

# Cell values (suggested by project)
WHITE_CELL = -1   # non-playable
EMPTY = 0

B_MAN = 1
W_MAN = 2
B_KING = 3
W_KING = 4

Player = int  # 1 for Black, 2 for White


def board_key(board: List[List[int]]) -> Tuple[int, ...]:
    """Immutable key for a board position (useful for repetition/learning)."""
    return tuple(cell for row in board for cell in row)


def position_key(board: List[List[int]], turn: Player) -> Tuple[int, ...]:
    """Position key including side-to-move."""
    return board_key(board) + (turn,)

def opponent(player: Player) -> Player:
    return 2 if player == 1 else 1

def is_black(piece: int) -> bool:
    return piece in (B_MAN, B_KING)

def is_white(piece: int) -> bool:
    return piece in (W_MAN, W_KING)

def is_king(piece: int) -> bool:
    return piece in (B_KING, W_KING)

def piece_owner(piece: int) -> Optional[Player]:
    if is_black(piece):
        return 1
    if is_white(piece):
        return 2
    return None

def promote_if_needed(piece: int, r: int) -> int:
    # row 0 is top, row 5 is bottom (standard array indexing)
    # Black starts at bottom and moves upward (r decreasing).
    # White starts at top and moves downward (r increasing).
    if piece == B_MAN and r == 0:
        return B_KING
    if piece == W_MAN and r == BOARD_SIZE - 1:
        return W_KING
    return piece

def playable_cell(r: int, c: int) -> bool:
    # on 6x6, playable (black) cells are alternating.
    # We'll define playable cells as those with (r+c) % 2 == 1 (common convention).
    return (r + c) % 2 == 1

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def clone_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]

@dataclass(frozen=True)
class Move:
    path: Tuple[Tuple[int, int], ...]          # sequence of squares visited
    captures: Tuple[Tuple[int, int], ...]      # captured piece positions in order

    @property
    def is_capture(self) -> bool:
        return len(self.captures) > 0

    def __str__(self) -> str:
        p = " -> ".join([f"({r},{c})" for (r,c) in self.path])
        if self.is_capture:
            cap = ", ".join([f"({r},{c})" for (r,c) in self.captures])
            return f"{p} | captures: {cap}"
        return p
