import time
import random
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


def random_choose(moves):
    return random.choice(moves)


def print_result(term):
    if term == 1:
        print("Result: Black wins")
    elif term == -1:
        print("Result: White wins")
    else:
        print("Result: Draw")


def main():
    print("6x6 Checkers")
    print("1) Human vs Agent")
    print("2) Agent vs Agent")
    print("3) Agent vs Random (Random is White)")

    mode = ask_int("Choose mode", 1, 3, 2)
    depth = ask_int("Search depth", 3, 6, 3)
    eval_id = ask_int("Eval function (1 or 2)", 1, 2, 2)
    use_ab = ask_int("Use Alpha-Beta? (1=Yes, 2=No)", 1, 2, 1) == 1

    compare_nodes = ask_int("Compare Minimax vs Alpha-Beta nodes? (1=Yes, 2=No)", 1, 2, 1) == 1

    eval_fn = pick_eval(eval_id)

    state = GameState(board=initial_board(), turn=1) 
    max_moves = 30
    move_count = 0

    human_player = 0
    random_player = 0
    if mode == 1:
        human_player = 2         
    elif mode == 3:
        random_player = 2         
    while True:
        print("\n----------------------------")
        print(f"Turn: {'Black' if state.turn == 1 else 'White'}")
        print_board(state.board)

        term = terminal_status(state.board, state.turn)
        if term is not None:
            print_result(term)
            break

        moves = generate_legal_moves(state.board, state.turn)

        
        if human_player == state.turn:
            mv = human_choose(moves)
            state = apply_move(state, mv)

       
        elif random_player == state.turn:
            mv = random_choose(moves)
            print(f"Random move: {mv}")
            state = apply_move(state, mv)

      
        else:
            if compare_nodes:
               
                mv_mm, st_mm, val_mm = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=False)
                mv_ab, st_ab, val_ab = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=True)

                print(f"Minimax:    move={mv_mm} | value={val_mm:.2f} | nodes={st_mm.nodes}")
                print(f"AlphaBeta:  move={mv_ab} | value={val_ab:.2f} | nodes={st_ab.nodes}")

                if mv_mm != mv_ab:
                    print("WARNING: Different best moves found (check implementation/order).")

                
                mv = mv_ab if use_ab else mv_mm
                
                t0 = time.perf_counter()
                _mv, _st, _val = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=use_ab)
                t1 = time.perf_counter()
                print(f"Chosen ({'AlphaBeta' if use_ab else 'Minimax'}) time: {(t1 - t0):.4f}s")

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
