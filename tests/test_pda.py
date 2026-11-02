"""Tests des automates à pile."""

from itertools import product

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from automata_extensions.cfg import ContextFreeGrammar
from automata_extensions.pda import PDA, cfg_to_pda


def words(alphabet, max_length):
    for size in range(max_length + 1):
        for letters in product(alphabet, repeat=size):
            yield "".join(letters)


def anbn_pda() -> PDA:
    """a^n b^n (n >= 0), acceptation par pile vide, déterministe."""
    return PDA(
        {"q0", "q1"},
        {"a", "b"},
        {"Z", "A"},
        {
            ("q0", "a", "Z"): {("q0", ("A", "Z"))},
            ("q0", "a", "A"): {("q0", ("A", "A"))},
            ("q0", "b", "A"): {("q1", ())},
            ("q1", "b", "A"): {("q1", ())},
            ("q0", "", "Z"): {("q1", ())},
            ("q1", "", "Z"): {("q1", ())},
        },
        "q0",
        "Z",
        acceptance="empty_stack",
    )


def palindrome_pda() -> PDA:
    """Palindromes de longueur paire, par état final, non déterministe."""
    transitions = {}
    for letter in "ab":
        for top in ("Z", "a", "b"):
            transitions[("p", letter, top)] = {("p", (letter, top))}
        transitions[("r", letter, letter)] = {("r", ())}
    transitions[("p", "", "Z")] = {("r", ("Z",))}
    transitions[("p", "", "a")] = {("r", ("a",))}
    transitions[("p", "", "b")] = {("r", ("b",))}
    transitions[("r", "", "Z")] = {("f", ("Z",))}
    return PDA(
        {"p", "r", "f"},
        {"a", "b"},
        {"Z", "a", "b"},
        transitions,
        "p",
        "Z",
        final_states={"f"},
    )


def test_anbn_by_empty_stack():
    pda = anbn_pda()
    for word in words("ab", 8):
        n = len(word) // 2
        expected = len(word) % 2 == 0 and word == "a" * n + "b" * n
        assert pda.accepts(word) == expected, word


def test_even_palindromes_by_final_state():
    pda = palindrome_pda()
    for word in words("ab", 8):
        expected = len(word) % 2 == 0 and word == word[::-1]
        assert pda.accepts(word) == expected, word


def test_find_run_is_a_valid_run():
    pda = anbn_pda()
    run = pda.find_run("aabb")
    assert run is not None
    assert run[0] == pda.initial_config()
    state, position, stack = run[-1]
    assert position == 4 and stack == ()
    assert pda.find_run("aab") is None
    for before, after in zip(run, run[1:]):
        assert after in set(pda._next_configs(before, "aabb"))


def test_find_run_is_shortest():
    run = anbn_pda().find_run("ab")
    assert run is not None
    # (q0,0,Z) -a-> (q0,1,AZ) -b-> (q1,2,Z) -eps-> (q1,2,)
    assert len(run) == 4


def test_determinism():
    assert anbn_pda().is_deterministic() is False  # q0: eps sur Z et a sur Z
    assert palindrome_pda().is_deterministic() is False
    deterministic = PDA(
        {"q"},
        {"a"},
        {"Z"},
        {("q", "a", "Z"): {("q", ("Z",))}},
        "q",
        "Z",
        final_states={"q"},
    )
    assert deterministic.is_deterministic()
    nondeterministic = PDA(
        {"q"},
        {"a"},
        {"Z"},
        {("q", "a", "Z"): {("q", ("Z",)), ("q", ())}},
        "q",
        "Z",
    )
    assert not nondeterministic.is_deterministic()
    only_epsilon = PDA(
        {"q"},
        {"a"},
        {"Z"},
        {("q", "", "Z"): {("q", ())}},
        "q",
        "Z",
    )
    assert only_epsilon.is_deterministic()


def test_epsilon_push_loop_terminates():
    loop = PDA(
        {"q"},
        {"a"},
        {"Z", "X"},
        {
            ("q", "", "Z"): {("q", ("X", "Z"))},
            ("q", "", "X"): {("q", ("X", "X"))},
        },
        "q",
        "Z",
        final_states={"q"},
    )
    assert not loop.accepts("a")
    assert loop.accepts("")  # état final dès le départ
    assert not loop.accepts("a", max_stack_height=3)


def test_push_as_string_and_defaults():
    pda = PDA(
        {"q"},
        {"a"},
        {"Z", "A"},
        {("q", "a", "Z"): {("q", "AZ")}, ("q", "a", "A"): {("q", "")}},
        "q",
        "Z",
        final_states={"q"},
    )
    assert pda.accepts("a")
    assert pda.accepts("aa")
    assert "PDA(" in repr(pda)


def test_validation_errors():
    base = dict(
        states={"q"},
        input_symbols={"a"},
        stack_symbols={"Z"},
        transitions={},
        initial_state="q",
        initial_stack_symbol="Z",
    )
    PDA(**base)
    for change in [
        {"acceptance": "autre"},
        {"initial_state": "x"},
        {"initial_stack_symbol": "Y"},
        {"final_states": {"x"}},
        {"transitions": {("x", "a", "Z"): {("q", ())}}},
        {"transitions": {("q", "b", "Z"): {("q", ())}}},
        {"transitions": {("q", "a", "Y"): {("q", ())}}},
        {"transitions": {("q", "a", "Z"): {("x", ())}}},
        {"transitions": {("q", "a", "Z"): {("q", ("Y",))}}},
    ]:
        with pytest.raises(ValueError):
            PDA(**{**base, **change})


GRAMMARS = [
    ContextFreeGrammar.from_text("S -> a S b | ε"),
    ContextFreeGrammar.from_text("S -> S S | ( S ) | ε"),
    ContextFreeGrammar.from_text("S -> a S a | b S b | a | b | ε"),
    ContextFreeGrammar.from_text(
        "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | x"
    ),
]


@pytest.mark.parametrize("grammar", GRAMMARS)
def test_cfg_to_pda_matches_cyk(grammar):
    pda = cfg_to_pda(grammar)
    assert pda.acceptance == "empty_stack"
    alphabet = "".join(sorted(grammar.terminals))
    for word in words(alphabet, 5 if len(alphabet) > 2 else 6):
        assert pda.accepts(word) == grammar.cyk(word), word


def test_to_pda_method_and_empty_language():
    grammar = ContextFreeGrammar.from_text("S -> a S b | ε")
    assert grammar.to_pda().accepts("aabb")
    empty = ContextFreeGrammar.from_text("S -> S a")
    assert not empty.to_pda().accepts("")
    assert not empty.to_pda().accepts("a")


@st.composite
def random_grammars(draw):
    variables = ["S", "A", "B"]
    symbols = variables + ["a", "b"]
    rules = []
    for _ in range(draw(st.integers(min_value=1, max_value=5))):
        lhs = draw(st.sampled_from(variables))
        rhs = tuple(
            draw(st.lists(st.sampled_from(symbols), min_size=0, max_size=3))
        )
        rules.append((lhs, rhs))
    return ContextFreeGrammar(variables, ["a", "b"], rules, "S")


@settings(max_examples=60)
@given(random_grammars())
def test_pda_equals_cyk_on_random_grammars(grammar):
    pda = grammar.to_pda()
    for word in words("ab", 4):
        assert pda.accepts(word) == grammar.cyk(word)
