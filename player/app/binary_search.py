# binary_search(ask, low=1, high=10_000) -> (secret, attempts, history)
from typing import Callable


def binary_search(
    ask: Callable[[int], str],
    low: int = 1,
    high: int = 10_000,
) -> tuple[int, int, list]:
    """Find the secret number using binary search.

    ask(n) must return 'lower', 'higher', or 'correct'.
    Returns (secret_number, total_attempts, guess_history).

    """
    history = []

    while low <= high:
        mid = (low + high) // 2     # always guess the midpoint
        result = ask(mid)
        history.append({"guess": mid, "result": result})

        if result == "correct":
            return mid, len(history), history
        elif result == "higher":
            low = mid + 1            # secret is above mid, discard lower half
        else:
            high = mid - 1           # secret is below mid, discard upper half

    raise RuntimeError("Search exhausted — host returned inconsistent results.")
