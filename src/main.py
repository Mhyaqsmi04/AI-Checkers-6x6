import time
from game import (
    GameState,
    initial_board,
    generate_legal_moves,
    apply_move,
    terminal_status,
    print_board
)

from ai import choose_move
from evals import eval_v1, eval_v2


def ask_int(msg, lo, hi, default):
    try:
        x = input(f"{msg} [{lo}-{hi}] (default {default}): ").strip()
        if x == "":
            return default
        x = int(x)
        if lo <= x <= hi:
            return x
    except:
        pass
    return default


def pick_eval(which: int):
    return eval_v1 if which == 1 else eval_v2


def human_choose(moves):
    print("Available moves:")
    for i, mv in enumerate(moves):
        print(f"{i}: {mv}")
    idx = ask_int("Choose move index", 0, len(moves) - 1, 0)
    return moves[idx]


def main():
    print("6x6 Checkers")
    print("1) Human vs Agent")
    print("2) Agent vs Agent")

    mode = ask_int("Choose mode", 1, 2, 1)
    depth = ask_int("Search depth", 3, 6, 3)
    eval_id = ask_int("Eval function (1 or 2)", 1, 2, 1)
    use_ab = ask_int("Use Alpha-Beta? (1=Yes, 2=No)", 1, 2, 1) == 1

    eval_fn = pick_eval(eval_id)

    # IMPORTANT: build GameState (board + turn)
    state = GameState(board=initial_board(), turn=1)  # Black starts

    # Demo limit so it doesn't print forever
    max_moves = 30
    move_count = 0

    # In Human vs Agent: human plays White (2) by default, agent is Black (1)
    human_player = 2 if mode == 1 else 0

    while True:
        print("\n----------------------------")
        print(f"Turn: {'Black' if state.turn == 1 else 'White'}")
        print_board(state.board)

        term = terminal_status(state.board, state.turn)
        if term is not None:
            if term == 1:
                print("Result: Black wins")
            elif term == -1:
                print("Result: White wins")
            else:
                print("Result: Draw")
            break

        moves = generate_legal_moves(state.board, state.turn)

        if human_player == state.turn:
            mv = human_choose(moves)
            state = apply_move(state, mv)
        else:
            t0 = time.perf_counter()
            mv, stats, val = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=use_ab)
            t1 = time.perf_counter()

            print(f"Agent move: {mv}")
            print(f"Value: {val:.2f} | Nodes: {stats.nodes} | Time: {(t1 - t0):.4f}s")
            state = apply_move(state, mv)

        move_count += 1
        if move_count >= max_moves:
            print("\nStopped: max moves reached (demo limit).")
            break


if __name__ == "__main__":
    main()
