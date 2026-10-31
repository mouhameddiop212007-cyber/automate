"""Tests de l'algorithme L* d'Angluin."""

from itertools import product

import pytest
from hypothesis import given, settings

from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.learning import (
    DFATeacher,
    PredicateTeacher,
    Teacher,
    angluin_lstar,
)
from tests.strategies import dfas

ALPHABET = {"a", "b"}
WORDS = [
    "".join(letters) for n in range(8) for letters in product("ab", repeat=n)
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


def test_teacher_alphabet_comes_from_the_target():
    assert DFATeacher(even_a()).alphabet == frozenset({"a", "b"})


def test_dfa_teacher_returns_a_shortest_counterexample():
    accept_all = ExtendedDFA(
        states={"s"},
        input_symbols=ALPHABET,
        transitions={"s": {"a": "s", "b": "s"}},
        initial_state="s",
        final_states={"s"},
    )
    assert DFATeacher(even_a()).equivalence(accept_all) == "a"


def test_dfa_teacher_accepts_an_equivalent_hypothesis():
    target = even_a()
    assert DFATeacher(target).equivalence(target) is None


def test_lstar_learns_even_number_of_a():
    target = even_a()
    learned = angluin_lstar(DFATeacher(target))
    assert len(learned.states) == 2
    assert learned.language_equals(target)


def test_lstar_learns_a_plus_with_its_sink_state():
    target = a_plus()
    learned = angluin_lstar(DFATeacher(target))
    assert len(learned.states) == 3
    assert learned.language_equals(target)


def test_lstar_learns_a_partial_target():
    target = ExtendedDFA(
        states={"0", "1"},
        input_symbols=ALPHABET,
        transitions={"0": {"a": "1"}, "1": {}},
        initial_state="0",
        final_states={"1"},
        allow_partial=True,
    )
    learned = angluin_lstar(DFATeacher(target))
    assert len(learned.states) == 3
    for word in WORDS:
        assert learned.accepts_input(word) == target.accepts_input(word)


def test_lstar_counts_the_queries():
    teacher = DFATeacher(even_a())
    angluin_lstar(teacher)
    assert teacher.membership_queries >= 1
    assert teacher.equivalence_queries >= 1


def test_lstar_learns_from_a_predicate():
    teacher = PredicateTeacher(
        ALPHABET, lambda word: word.count("a") % 3 == 0, max_length=7
    )
    learned = angluin_lstar(teacher)
    assert len(learned.states) == 3
    for word in WORDS:
        assert learned.accepts_input(word) == (word.count("a") % 3 == 0)


def test_lstar_rejects_an_inconsistent_teacher():
    class Liar(Teacher):
        def _is_member(self, word):
            return False

        def _find_counterexample(self, hypothesis):
            return ""

    with pytest.raises(ValueError):
        angluin_lstar(Liar({"a"}))


@settings(max_examples=100)
@given(dfas())
def test_lstar_learns_the_minimal_dfa(target):
    learned = angluin_lstar(DFATeacher(target))
    assert learned.language_equals(target)
    assert len(learned.states) == len(target.minify().states)


@settings(max_examples=100)
@given(dfas())
def test_lstar_asks_at_most_n_equivalence_queries(target):
    teacher = DFATeacher(target)
    learned = angluin_lstar(teacher)
    assert teacher.equivalence_queries <= len(learned.states)
