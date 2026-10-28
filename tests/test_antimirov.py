"""Tests des dérivées partielles et de l'automate d'Antimirov."""

from itertools import product

import pytest

from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.regex_ast import (
    Epsilon,
    parse_regex,
    partial_derivatives,
)

REGEXES = [
    "a",
    "ab",
    "a|b",
    "a*b",
    "(a|b)*abb",
    "(ab|a)*",
    "a*a*",
    "(a*|b*)*",
    "ab*a|b",
    "(a|ab)b*",
]
ALPHABET = {"a", "b"}


def test_partial_derivatives_of_a_star_b():
    node = parse_regex("a*b")
    assert partial_derivatives(node, "a") == frozenset({node})
    assert partial_derivatives(node, "b") == frozenset({Epsilon()})


def test_partial_derivatives_of_union_is_a_set_of_two():
    node = parse_regex("ab|ac")
    assert len(partial_derivatives(node, "a")) == 2


def test_partial_derivatives_empty_when_symbol_absent():
    assert partial_derivatives(parse_regex("ab"), "b") == frozenset()


@pytest.mark.parametrize("regex", REGEXES)
def test_antimirov_agrees_with_thompson(regex):
    anti = ExtendedNFA.antimirov_automaton(regex, ALPHABET)
    ref = ExtendedNFA.regex_to_nfa(regex, input_symbols=ALPHABET)
    for n in range(7):
        for letters in product("ab", repeat=n):
            word = "".join(letters)
            assert anti.accepts_input(word) == ref.accepts_input(word), (
                regex,
                word,
            )


@pytest.mark.parametrize("regex", REGEXES)
def test_antimirov_has_at_most_n_plus_one_states(regex):
    occurrences = sum(1 for c in regex if c.isalnum())
    nfa = ExtendedNFA.antimirov_automaton(regex, ALPHABET)
    assert len(nfa.states) <= occurrences + 1


def test_antimirov_has_no_epsilon_transition():
    nfa = ExtendedNFA.antimirov_automaton("(a|b)*abb", ALPHABET)
    assert all("" not in t for t in nfa.transitions.values())
