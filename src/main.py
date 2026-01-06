from __future__ import annotations
import time

from game import GameState, initial_board, print_board, generate_legal_moves, apply_move, terminal_status
from ai import choose_move
from evals import eval_v1, eval_v2

def pick_eval(which: int):
    return eval_v1 if which == 1 else eval_v2

def ask_int(prompt: str, lo: int, hi: int, default: int) -> int:
    s = input(f"{prompt} [{lo}-{hi}] (default {default}): ").strip()
    if not s:
        return default
    try:
        v = int(s)
        return max(lo, min(hi, v))
    except:
        return default
#نمایش تمامی حرکات مجاز کاربر
def human_choose(moves):
    print("حرکت‌های مجاز:")
    for i, mv in enumerate(moves):
        print(f"{i}: {mv}")
    idx = ask_int("شماره حرکت را وارد کنید", 0, len(moves)-1, 0)
    return moves[idx]

# انتخاب هایی که توسط کاربر مشخص میشوند.
def main():
    print("6x6 Checkers")
    print("1) Human vs Agent")
    print("2) Agent vs Agent")
    mode = ask_int("انتخاب", 1, 2, 1)

    depth = ask_int("عمق جستجو", 3, 8, 3)
    eval_id = ask_int("تابع ارزیابی (1 یا 2)", 1, 2, 1)
    use_ab = ask_int("Use Alpha-Beta? (1=Yes,2=No)", 1, 2, 1) == 1

    eval_fn = pick_eval(eval_id)

    state = GameState(board=initial_board(), turn=1)  # black starts

    # In HvA: human plays White by default (so agent is Black maximizer)
    human_player = 2 if mode == 1 else 0

    while True:
        print("\n-------------------------------")
        print(f"نوبت: {'Black' if state.turn == 1 else 'White'}")
        print_board(state.board)

        term = terminal_status(state.board, state.turn)
        if term is not None: #نمایش نتایج
            if term == 1:
                print("نتیجه: برد سیاه (Black wins)")
            elif term == -1:
                print("نتیجه: برد سفید (White wins)")
            else:
                print("نتیجه: مساوی (Draw)")
            break

        moves = generate_legal_moves(state.board, state.turn)

        if human_player == state.turn:
            mv = human_choose(moves)
            state = apply_move(state, mv)
        else:
            t0 = time.perf_counter()
            mv, stats, val = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=use_ab)
            t1 = time.perf_counter()
            print(f"Agent chose: {mv}")
            print(f"Value: {val:.2f} | Nodes: {stats.nodes} | Time: {(t1-t0):.4f}s")
            state = apply_move(state, mv)


if __name__ == "__main__":
    main()
