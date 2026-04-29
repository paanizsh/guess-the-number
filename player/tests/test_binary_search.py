import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'player'))

from app.binary_search import binary_search


def fake_ask(secret):
    def ask(n):
        if n == secret:
            return "correct"
        elif n < secret:
            return "higher"
        else:
            return "lower"
    return ask

def test_finds_correct_number():
    secret, attempts, history = binary_search(ask=fake_ask(7342))
    assert secret == 7342


def test_always_within_14_guesses():
    for secret in [1, 100, 5000, 9999, 10000]:
        _, attempts, _ = binary_search(ask=fake_ask(secret))
        assert attempts <= 14


def test_last_history_item_is_correct():
    _, _, history = binary_search(ask=fake_ask(3333))
    assert history[-1]["result"] == "correct"