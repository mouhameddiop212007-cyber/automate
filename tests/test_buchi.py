"""Tests des automates de Büchi."""

from itertools import product

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from automata_extensions.buchi import BuchiAutomaton


def inf_a() -> BuchiAutomaton:
    """Une infinité de a (déterministe)."""
    return BuchiAutomaton(
        {0, 1},
        {"a", "b"},
        {(0, "a"): {1}, (0, "b"): {0}, (1, "a"): {1}, (1, "b"): {0}},
        0,
        {1},
    )


def fin_a() -> BuchiAutomaton:
    """Un nombre fini de a (non déterministe : on devine le dernier a)."""
    return BuchiAutomaton(
        {"p", "q"},
        {"a", "b"},
        {
            ("p", "a"): {"p", "q"},
            ("p", "b"): {"p", "q"},
            ("q", "b"): {"q"},
        },
        "p",
        {"q"},
    )


def lassos(alphabet, max_prefix, max_loop):
    for i in range(max_prefix + 1):
        for prefix in product(alphabet, repeat=i):
            for j in range(1, max_loop + 1):
                for loop in product(alphabet, repeat=j):
                    yield list(prefix), list(loop)


def test_infinitely_many_a():
    automaton = inf_a()
    for prefix, loop in lassos("ab", 3, 3):
        assert automaton.accepts_lasso(prefix, loop) == ("a" in loop)


def test_finitely_many_a():
    automaton = fin_a()
    for prefix, loop in lassos("ab", 3, 3):
        assert automaton.accepts_lasso(prefix, loop) == ("a" not in loop)


def test_lasso_validation():
    with pytest.raises(ValueError):
        inf_a().accepts_lasso("a", "")
    assert not inf_a().accepts_lasso("c", "a")  # lettre inconnue : rejeté


def test_emptiness_and_witness():
    for automaton in (inf_a(), fin_a()):
        lasso = automaton.find_accepted_lasso()
        assert lasso is not None
        assert automaton.accepts_lasso(*lasso)
        assert not automaton.is_empty()
    assert inf_a().find_accepted_lasso() == (["a"], ["a"])
    assert fin_a().find_accepted_lasso() == (["a"], ["b"])


def test_empty_languages():
    # acceptant mais sans cycle
    no_cycle = BuchiAutomaton({0, 1}, {"a"}, {(0, "a"): {1}}, 0, {1})
    assert no_cycle.is_empty()
    assert no_cycle.find_accepted_lasso() is None
    # acceptant sur un cycle, mais inaccessible
    unreachable = BuchiAutomaton(
        {0, 1}, {"a"}, {(0, "a"): {0}, (1, "a"): {1}}, 0, {1}
    )
    assert unreachable.is_empty()
    assert unreachable.reachable_states() == {0}
    assert not unreachable.accepts_lasso("", "a")
    # aucun état acceptant
    assert BuchiAutomaton({0}, {"a"}, {(0, "a"): {0}}, 0, set()).is_empty()


def test_accepting_initial_state_on_cycle():
    automaton = BuchiAutomaton({0}, {"a"}, {(0, "a"): {0}}, 0, {0})
    assert automaton.find_accepted_lasso() == ([], ["a"])
    assert automaton.accepts_lasso("aa", "a")


def test_accepting_state_visited_once_only():
    # 0 -a-> 1 (acceptant) -a-> 2 -a-> 2 : 1 n'est visité qu'une fois
    automaton = BuchiAutomaton(
        {0, 1, 2},
        {"a"},
        {(0, "a"): {1}, (1, "a"): {2}, (2, "a"): {2}},
        0,
        {1},
    )
    assert automaton.is_empty()
    assert not automaton.accepts_lasso("", "a")


def test_loop_longer_than_one_letter():
    automaton = BuchiAutomaton(
        {0, 1},
        {"a", "b"},
        {(0, "a"): {1}, (1, "b"): {0}},
        0,
        {1},
    )
    assert automaton.accepts_lasso("", "ab")
    assert automaton.accepts_lasso("ab", "ab")
    assert not automaton.accepts_lasso("", "ba")
    assert automaton.accepts_lasso("a", "ba")


def test_intersection_both_conditions():
    both = inf_a().intersection(inf_b())
    for prefix, loop in lassos("ab", 2, 3):
        expected = "a" in loop and "b" in loop
        assert both.accepts_lasso(prefix, loop) == expected
    assert both.find_accepted_lasso() is not None


def inf_b() -> BuchiAutomaton:
    return BuchiAutomaton(
        {0, 1},
        {"a", "b"},
        {(0, "b"): {1}, (0, "a"): {0}, (1, "b"): {1}, (1, "a"): {0}},
        0,
        {1},
    )


def test_intersection_empty():
    only_b = fin_a()  # finitement de a et infiniment de a : vide
    product_automaton = inf_a().intersection(only_b)
    assert product_automaton.is_empty()


def test_union():
    union = inf_a().union(fin_a())
    for prefix, loop in lassos("ab", 2, 3):
        assert union.accepts_lasso(prefix, loop)  # a dans loop ou non
    union = inf_a().union(inf_b())
    for prefix, loop in lassos("ab", 2, 3):
        assert union.accepts_lasso(prefix, loop) == (
            "a" in loop or "b" in loop
        )
    assert union.input_symbols == {"a", "b"}


def test_union_with_empty():
    nothing = BuchiAutomaton({0}, {"a", "b"}, {}, 0, set())
    union = inf_a().union(nothing)
    for prefix, loop in lassos("ab", 2, 2):
        assert union.accepts_lasso(prefix, loop) == ("a" in loop)


def test_validation_errors():
    with pytest.raises(ValueError):
        BuchiAutomaton({0}, {"a"}, {}, 1, set())
    with pytest.raises(ValueError):
        BuchiAutomaton({0}, {"a"}, {}, 0, {1})
    with pytest.raises(ValueError):
        BuchiAutomaton({0}, {"a"}, {(1, "a"): {0}}, 0, set())
    with pytest.raises(ValueError):
        BuchiAutomaton({0}, {"a"}, {(0, "b"): {0}}, 0, set())
    with pytest.raises(ValueError):
        BuchiAutomaton({0}, {"a"}, {(0, "a"): {1}}, 0, set())


def test_repr_and_successors():
    automaton = inf_a()
    assert "BuchiAutomaton(" in repr(automaton)
    assert automaton.successors(0, "a") == {1}
    assert automaton.successors(0, "c") == frozenset()


def _even_a_dfa():
    from types import SimpleNamespace

    return SimpleNamespace(
        states={"e", "o"},
        input_symbols={"a", "b"},
        transitions={
            "e": {"a": "o", "b": "e"},
            "o": {"a": "e", "b": "o"},
        },
        initial_state="e",
        final_states={"e"},
    )


def _check_even_a(automaton):
    assert automaton.accepts_lasso("", "b")
    assert not automaton.accepts_lasso("a", "b")
    assert automaton.accepts_lasso("", "ab")  # préfixes pairs infiniment


def test_from_dfa_duck_typed():
    _check_even_a(BuchiAutomaton.from_dfa(_even_a_dfa()))


def test_from_dfa_real_automata_lib():
    dfa_module = pytest.importorskip("automata.fa.dfa")
    stub = _even_a_dfa()
    dfa = dfa_module.DFA(
        states=stub.states,
        input_symbols=stub.input_symbols,
        transitions=stub.transitions,
        initial_state=stub.initial_state,
        final_states=stub.final_states,
    )
    _check_even_a(BuchiAutomaton.from_dfa(dfa))


@st.composite
def random_buchi(draw):
    size = draw(st.integers(min_value=1, max_value=3))
    states = list(range(size))
    transitions = {}
    for state in states:
        for letter in "ab":
            targets = draw(st.lists(st.sampled_from(states), max_size=2))
            if targets:
                transitions[(state, letter)] = set(targets)
    accepting = draw(st.lists(st.sampled_from(states), max_size=size))
    return BuchiAutomaton(states, "ab", transitions, 0, accepting)


@settings(max_examples=60)
@given(random_buchi(), random_buchi())
def test_intersection_and_union_semantics(left, right):
    inter = left.intersection(right)
    union = left.union(right)
    for prefix, loop in lassos("ab", 2, 2):
        a = left.accepts_lasso(prefix, loop)
        b = right.accepts_lasso(prefix, loop)
        assert inter.accepts_lasso(prefix, loop) == (a and b)
        assert union.accepts_lasso(prefix, loop) == (a or b)


@settings(max_examples=100)
@given(random_buchi())
def test_witness_is_accepted_and_emptiness_is_sound(automaton):
    lasso = automaton.find_accepted_lasso()
    if lasso is None:
        assert automaton.is_empty()
        for prefix, loop in lassos("ab", 3, 3):
            assert not automaton.accepts_lasso(prefix, loop)
    else:
        assert automaton.accepts_lasso(*lasso)
