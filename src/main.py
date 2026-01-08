import time
import random
from typing import Callable, List, Tuple

from game import (
    GameState,
    initial_state,
    generate_legal_moves,
    apply_move,
    terminal_status,
    print_board,
)
from ai import choose_move
from evals import eval_v1, eval_v2, eval_v3_positional
from learning import ExperienceDB
from utils import position_key


EvalFn = Callable[[GameState], float]


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


def ask_float(msg, lo, hi, default):
    try:
        x = input(f"{msg} [{lo}-{hi}] (default {default}): ").strip()
        if x == "":
            return default
        x = float(x)
        if lo <= x <= hi:
            return x
    except:
        pass
    return default


def pick_eval(which: int):
    if which == 1:
        return eval_v1
    if which == 2:
        return eval_v2
    return eval_v3_positional


def human_choose(moves):
    print("Available moves:")
    for i, mv in enumerate(moves):
        print(f"{i}: {mv}")
    idx = ask_int("Choose move index", 0, len(moves) - 1, 0)
    return moves[idx]


def random_choose(moves):
    return random.choice(moves)


def greedy_choose(state: GameState, eval_fn: EvalFn):
    """One-ply greedy: pick the move that looks best by eval_fn."""
    moves = generate_legal_moves(state.board, state.turn)
    maximizing = (state.turn == 1)
    best_mv = moves[0]
    best_val = float("-inf") if maximizing else float("inf")
    for mv in moves:
        nxt = apply_move(state, mv)
        val = eval_fn(nxt)
        if maximizing:
            if val > best_val:
                best_val = val
                best_mv = mv
        else:
            if val < best_val:
                best_val = val
                best_mv = mv
    return best_mv


def print_result(term):
    if term == 1:
        print("Result: Black wins")
    elif term == -1:
        print("Result: White wins")
    else:
        print("Result: Draw")


def play_one_game(
    mode: int,
    depth: int,
    eval_fn: EvalFn,
    use_ab: bool,
    compare_nodes: bool,
    verbose: bool = True,
):
    """Plays a single game and returns (term, visited_position_keys)."""

    state = initial_state()
    visited: List[Tuple[int, ...]] = []

    # Which sides are controlled by what?
    human_player = 0
    random_player = 0
    greedy_player = 0
    if mode == 1:
        human_player = 2  # human plays White
    elif mode == 3:
        random_player = 2  # Random is White
    elif mode == 4:
        greedy_player = 2  # Greedy is White

    while True:
        visited.append(position_key(state.board, state.turn))

        if verbose:
            print("\n----------------------------")
            print(f"Turn: {'Black' if state.turn == 1 else 'White'}")
            print_board(state.board)

        term = terminal_status(state)
        if term is not None:
            if verbose:
                print_result(term)
            return term, visited

        moves = generate_legal_moves(state.board, state.turn)

        if human_player == state.turn:
            mv = human_choose(moves)
            state = apply_move(state, mv)
            continue

        if random_player == state.turn:
            mv = random_choose(moves)
            if verbose:
                print(f"Random move: {mv}")
            state = apply_move(state, mv)
            continue

        if greedy_player == state.turn:
            mv = greedy_choose(state, eval_fn)
            if verbose:
                print(f"Greedy move: {mv}")
            state = apply_move(state, mv)
            continue

        # Agent
        if compare_nodes:
            mv_mm, st_mm, val_mm = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=False)
            mv_ab, st_ab, val_ab = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=True)

            if verbose:
                print(f"Minimax:    move={mv_mm} | value={val_mm:.2f} | nodes={st_mm.nodes}")
                print(f"AlphaBeta:  move={mv_ab} | value={val_ab:.2f} | nodes={st_ab.nodes}")
                if mv_mm != mv_ab:
                    print("WARNING: Different best moves found (check ordering/implementation).")

            mv = mv_ab if use_ab else mv_mm

            if verbose:
                t0 = time.perf_counter()
                _mv, _st, _val = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=use_ab)
                t1 = time.perf_counter()
                print(f"Chosen ({'AlphaBeta' if use_ab else 'Minimax'}) time: {(t1 - t0):.4f}s")
        else:
            t0 = time.perf_counter()
            mv, stats, val = choose_move(state, depth=depth, eval_fn=eval_fn, use_ab=use_ab)
            t1 = time.perf_counter()
            if verbose:
                print(f"Agent move: {mv}")
                print(f"Value: {val:.2f} | Nodes: {stats.nodes} | Time: {(t1 - t0):.4f}s")

        state = apply_move(state, mv)


def main():
    print("6x6 Checkers")
    print("1) Human vs Agent")
    print("2) Agent vs Agent")
    print("3) Agent vs Random (Random is White)")
    print("4) Agent vs Greedy (Greedy is White)")
    print("5) Self-play training (Agent vs Agent, many games, saves experience)")

    mode = ask_int("Choose mode", 1, 5, 2)
    depth = ask_int("Search depth", 3, 7, 4)
    eval_id = ask_int("Eval function (1=Material, 2=+Mobility, 3=Positional)", 1, 3, 3)
    use_ab = ask_int("Use Alpha-Beta? (1=Yes, 2=No)", 1, 2, 1) == 1
    compare_nodes = ask_int("Compare Minimax vs Alpha-Beta nodes? (1=Yes, 2=No)", 1, 2, 1) == 1

    base_eval = pick_eval(eval_id)

    # --- Bonus part: learning from experience ---
    use_learning = ask_int("Enable experience learning? (1=Yes, 2=No)", 1, 2, 1) == 1
    db = ExperienceDB("experience.json") if use_learning else None
    learn_weight = 0.0
    if db is not None:
        learn_weight = ask_float("Learning weight (suggest 0.2)", 0.0, 2.0, 0.2)

    def eval_fn(state: GameState) -> float:
        s = base_eval(state)
        if db is None or learn_weight <= 0.0:
            return s
        bonus = db.get_value(position_key(state.board, state.turn))
        return s + learn_weight * bonus

    if mode == 5:
        games = ask_int("Training games", 1, 2000, 200)
        if db is None:
            db = ExperienceDB("experience.json")
            learn_weight = 0.2

        w = l = d = 0
        for i in range(games):
            term, visited = play_one_game(
                mode=2,
                depth=depth,
                eval_fn=eval_fn,
                use_ab=use_ab,
                compare_nodes=False,
                verbose=False,
            )
            if term == 1:
                w += 1
            elif term == -1:
                l += 1
            else:
                d += 1
            db.update_game(visited, term)
            if (i + 1) % max(1, games // 10) == 0:
                print(f"... {i+1}/{games} games | W/L/D = {w}/{l}/{d}")

        db.save()
        print("\nTraining finished.")
        print(f"Saved experience to experience.json | W/L/D = {w}/{l}/{d}")
        return

    # single interactive game
    term, visited = play_one_game(
        mode=mode,
        depth=depth,
        eval_fn=eval_fn,
        use_ab=use_ab,
        compare_nodes=compare_nodes,
        verbose=True,
    )

    if db is not None:
        db.update_game(visited, term)
        db.save()
        print("Saved experience to experience.json")


if __name__ == "__main__":
    main()
