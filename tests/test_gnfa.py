"""Tests d'ExtendedGNFA : élimination d'états pas à pas."""

from itertools import permutations, product

import pytest

from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.fa.gnfa import ExtendedGNFA
from automata_extensions.fa.nfa import ExtendedNFA

ALPHABET = {"a", "b"}
WORDS = [
    "".join(letters) for n in range(6) for letters in product("ab", repeat=n)
]


def even_a():
    """Nombre pair de 'a'."""
    return ExtendedDFA(
        states={"p", "i"},
        input_symbols=ALPHABET,
        transitions={
            "p": {"a": "i", "b": "p"},
            "i": {"a": "p", "b": "i"},
        },
        initial_state="p",
        final_states={"p"},
    )


def a_plus():
    """a+ avec un état puits."""
    return ExtendedDFA(
        states={"1", "2", "3"},
        input_symbols=ALPHABET,
        transitions={
            "1": {"a": "2", "b": "3"},
            "2": {"a": "2", "b": "3"},
            "3": {"a": "3", "b": "3"},
        },
        initial_state="1",
        final_states={"2"},
    )


def a_star_b_with_epsilon():
    """a*b, avec une transition epsilon."""
    return ExtendedNFA(
        states={"q0", "q1", "q2"},
        input_symbols=ALPHABET,
        transitions={
            "q0": {"a": {"q0"}, "": {"q1"}},
            "q1": {"b": {"q2"}},
            "q2": {},
        },
        initial_state="q0",
        final_states={"q2"},
    )


FACTORIES = [even_a, a_plus, a_star_b_with_epsilon]


def test_to_gnfa_returns_extended_gnfa():
    assert isinstance(even_a().to_gnfa(), ExtendedGNFA)
    assert isinstance(a_star_b_with_epsilon().to_gnfa(), ExtendedGNFA)


def test_eliminable_states_exclude_initial_and_final():
    gnfa = even_a().to_gnfa()
    assert gnfa.eliminable_states() == ["i", "p"]
    assert len(gnfa.states) == 4


def test_eliminate_state_is_immutable():
    gnfa = even_a().to_gnfa()
    smaller = gnfa.eliminate_state("i")
    assert "i" in gnfa.states
    assert "i" not in smaller.states
    assert len(smaller.states) == len(gnfa.states) - 1


def test_eliminate_state_rejects_special_and_unknown_states():
    gnfa = even_a().to_gnfa()
    with pytest.raises(ValueError):
        gnfa.eliminate_state(gnfa.initial_state)
    with pytest.raises(ValueError):
        gnfa.eliminate_state(gnfa.final_state)
    with pytest.raises(ValueError):
        gnfa.eliminate_state("zzz")


def test_elimination_steps_shrink_down_to_two_states():
    gnfa = a_plus().to_gnfa()
    steps = gnfa.elimination_steps()
    assert len(steps) == len(gnfa.eliminable_states()) + 1
    assert len(steps[-1].states) == 2


def test_invalid_order_is_rejected():
    gnfa = even_a().to_gnfa()
    with pytest.raises(ValueError):
        gnfa.to_regex_with_order(["p"])
    with pytest.raises(ValueError):
        gnfa.to_regex_with_order(["p", "p"])


@pytest.mark.parametrize("factory", FACTORIES)
def test_every_elimination_order_preserves_the_language(factory):
    automaton = factory()
    gnfa = automaton.to_gnfa()
    for order in permutations(gnfa.eliminable_states()):
        regex = gnfa.to_regex_with_order(order)
        assert regex is not None
        nfa = ExtendedNFA.regex_to_nfa(regex, input_symbols=ALPHABET)
        for word in WORDS:
            assert nfa.accepts_input(word) == automaton.accepts_input(word), (
                order,
                regex,
                word,
            )


@pytest.mark.parametrize("factory", FACTORIES)
def test_default_order_agrees_with_native_to_regex(factory):
    automaton = factory()
    gnfa = automaton.to_gnfa()
    ours = ExtendedNFA.regex_to_nfa(
        gnfa.to_regex_with_order(), input_symbols=ALPHABET
    )
    native = ExtendedNFA.regex_to_nfa(gnfa.to_regex(), input_symbols=ALPHABET)
    for word in WORDS:
        assert ours.accepts_input(word) == native.accepts_input(word)


def test_bypass_label_epsilon_everywhere_stays_epsilon():
    gnfa = even_a().to_gnfa()
    assert gnfa._bypass_label("", None, "", "") == ""


def test_bypass_label_optional_path():
    gnfa = even_a().to_gnfa()
    assert gnfa._bypass_label("a", "b", "c", "") == "(ab*c)?"


def test_bypass_label_parallel_union_edge_is_parenthesised():
    gnfa = even_a().to_gnfa()
    assert gnfa._bypass_label("c", None, "d", "a|b") == "cd|(a|b)"


def test_bypass_label_union_prefix_is_parenthesised():
    gnfa = even_a().to_gnfa()
    assert gnfa._bypass_label("a|b", None, "c", None) == "(a|b)c"


def test_bypass_label_epsilon_self_loop_is_ignored():
    gnfa = even_a().to_gnfa()
    assert gnfa._bypass_label("a", "", "b", None) == "ab"
