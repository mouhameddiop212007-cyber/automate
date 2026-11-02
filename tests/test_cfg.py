"""Tests des grammaires hors-contexte : CNF, CYK, Earley."""

from itertools import product

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from automata_extensions.cfg import ContextFreeGrammar, tree_yield

ANBN = ContextFreeGrammar.from_text("S -> a S b | ε")
DYCK = ContextFreeGrammar.from_text("S -> S S | ( S ) | ε")
PALINDROMES = ContextFreeGrammar.from_text("S -> a S a | b S b | a | b | ε")
EQUAL = ContextFreeGrammar.from_text("S -> a S b S | b S a S | ε")
EXPR = ContextFreeGrammar.from_text(
    """
    E -> E + T | T
    T -> T * F | F
    F -> ( E ) | x
    """
)


def words(alphabet: str, max_length: int):
    for size in range(max_length + 1):
        for letters in product(alphabet, repeat=size):
            yield "".join(letters)


def is_dyck(word: str) -> bool:
    depth = 0
    for char in word:
        depth += 1 if char == "(" else -1
        if depth < 0:
            return False
    return depth == 0


CASES = [
    (
        ANBN,
        "ab",
        lambda w: (
            w == "a" * (len(w) // 2) + "b" * (len(w) // 2) and len(w) % 2 == 0
        ),
    ),
    (DYCK, "()", is_dyck),
    (PALINDROMES, "ab", lambda w: w == w[::-1]),
    (EQUAL, "ab", lambda w: w.count("a") == w.count("b")),
]


@pytest.mark.parametrize("grammar, alphabet, predicate", CASES)
def test_cyk_and_earley_match_predicate(grammar, alphabet, predicate):
    for word in words(alphabet, 8):
        expected = predicate(word)
        assert grammar.cyk(word) == expected, word
        assert grammar.earley_accepts(word) == expected, word


def test_cyk_equals_earley_on_expressions():
    for word in words("x+*()", 5):
        assert EXPR.cyk(word) == EXPR.earley_accepts(word), word
    assert EXPR.cyk("x+x*x")
    assert EXPR.cyk("(x+x)*x")
    assert not EXPR.cyk("x+")


def test_accepts_is_cyk():
    assert ANBN.accepts("aabb")
    assert not ANBN.accepts("aab")


def test_cnf_shape_and_language():
    for grammar, alphabet, predicate in CASES:
        cnf = grammar.to_cnf()
        assert cnf.is_cnf()
        for word in words(alphabet, 6):
            assert cnf.cyk(word) == predicate(word)
    assert EXPR.to_cnf().is_cnf()


def test_is_cnf_rejects_other_shapes():
    assert not ANBN.is_cnf()
    assert not ContextFreeGrammar.from_text("S -> A\nA -> a").is_cnf()
    # epsilon seulement sur l'axiome qui n'est jamais à droite
    assert ContextFreeGrammar.from_text("S -> A A | ε\nA -> a").is_cnf()
    assert not ContextFreeGrammar.from_text("S -> S S | a | ε").is_cnf()
    assert not ContextFreeGrammar.from_text("S -> a A\nA -> a").is_cnf()


def test_nullable_generating_reachable():
    grammar = ContextFreeGrammar.from_text(
        """
        S -> A B | a
        A -> ε | a
        B -> A A
        C -> C c
        D -> d
        """
    )
    assert grammar.nullable_variables() == {"A", "B", "S"}
    assert grammar.generating_variables() == {"S", "A", "B", "D"}
    assert grammar.reachable_symbols() == {"S", "A", "B", "a"}
    assert not grammar.is_empty_language()


def test_remove_useless():
    grammar = ContextFreeGrammar.from_text(
        "S -> a S | b\nC -> C c\nD -> d\nE -> a"
    )
    cleaned = grammar.remove_useless()
    assert cleaned.variables == {"S"}
    assert cleaned.productions == {("S", ("a", "S")), ("S", ("b",))}


def test_empty_language():
    grammar = ContextFreeGrammar.from_text("S -> S a")
    assert grammar.is_empty_language()
    assert grammar.remove_useless().productions == frozenset()
    assert not grammar.cyk("")
    assert not grammar.cyk("a")
    assert not grammar.earley_accepts("a")
    assert grammar.cyk_parse("a") is None
    assert grammar.enumerate_words(3) == []


def test_remove_epsilon_keeps_language():
    for grammar, alphabet, predicate in CASES:
        reduced = grammar.remove_epsilon()
        epsilon_rules = [p for p in reduced.productions if p[1] == ()]
        assert all(lhs == reduced.start for lhs, _ in epsilon_rules)
        for word in words(alphabet, 6):
            assert reduced.earley_accepts(word) == predicate(word)


def test_remove_epsilon_without_nullable_start():
    grammar = ContextFreeGrammar.from_text("S -> A a\nA -> ε | b")
    reduced = grammar.remove_epsilon()
    assert reduced.start == "S"
    assert all(rhs != () for _, rhs in reduced.productions)
    assert reduced.earley_accepts("a") and reduced.earley_accepts("ba")


def test_remove_unit_productions():
    reduced = EXPR.remove_unit_productions()
    for lhs, rhs in reduced.productions:
        assert not (len(rhs) == 1 and rhs[0] in reduced.variables)
    for word in words("x+*()", 4):
        assert reduced.earley_accepts(word) == EXPR.earley_accepts(word)


def test_unit_cycle_terminates():
    grammar = ContextFreeGrammar.from_text("S -> A | a\nA -> S | b")
    assert grammar.cyk("a") and grammar.cyk("b")
    assert not grammar.cyk("ab")


def test_fresh_names_do_not_clash():
    # "S0" (axiome frais) et "S_1" (binarisation) sont déjà pris
    grammar = ContextFreeGrammar.from_text("S -> S0 a b\nS0 -> b | S_1")
    cnf = grammar.to_cnf()
    assert cnf.is_cnf()
    for word in (["b", "a", "b"], ["S_1", "a", "b"], ["a", "b"], ["b"]):
        assert cnf.cyk(word) == grammar.earley_accepts(word)
    assert cnf.cyk(["S_1", "a", "b"])
    clash = ContextFreeGrammar.from_text("S -> T_a a | a\nT_a -> a")
    assert clash.to_cnf().cyk("aa") and clash.to_cnf().cyk("a")


def test_cyk_table_contents():
    table = ANBN.cyk_table("aabb")
    assert len(table) == 4
    cnf = ANBN.to_cnf()
    assert cnf.start in table[3][0]
    assert table[0][0] != frozenset()


def test_cyk_parse_tree():
    for word in ["", "ab", "aabb", "aaabbb"]:
        tree = ANBN.cyk_parse(word)
        assert tree is not None
        assert "".join(tree_yield(tree)) == word
    assert ANBN.cyk_parse("aab") is None
    assert ANBN.cyk_parse("ba") is None
    assert ANBN.cyk_parse("") == (ANBN.to_cnf().start,)


def test_parse_tree_uses_grammar_productions():
    grammar = EXPR
    cnf = grammar.to_cnf()
    tree = grammar.cyk_parse("x+x")
    assert tree is not None

    def check(node):
        if len(node) == 2:
            assert (node[0], (node[1],)) in cnf.productions
        else:
            rhs = (node[1][0], node[2][0])
            assert (node[0], rhs) in cnf.productions
            check(node[1])
            check(node[2])

    check(tree)
    assert tree_yield(tree) == ["x", "+", "x"]


def test_cyk_on_list_of_terminals():
    grammar = ContextFreeGrammar.from_text("S -> id + id | id")
    assert grammar.cyk(["id", "+", "id"])
    assert grammar.earley_accepts(["id"])
    assert not grammar.cyk(["+"])


def test_enumerate_words():
    assert ANBN.enumerate_words(6) == ["", "ab", "aabb", "aaabbb"]
    assert PALINDROMES.enumerate_words(2) == ["", "a", "b", "aa", "bb"]
    brute = [w for w in words("ab", 6) if w.count("a") == w.count("b")]
    assert EQUAL.enumerate_words(6) == sorted(brute, key=lambda w: (len(w), w))


def test_from_text_and_str_roundtrip():
    for grammar in [ANBN, DYCK, PALINDROMES, EQUAL, EXPR]:
        again = ContextFreeGrammar.from_text(str(grammar), grammar.start)
        assert again == grammar
        assert hash(again) == hash(grammar)
        assert repr(grammar).startswith("ContextFreeGrammar(")
    assert str(ANBN) == "S -> ε | a S b"
    assert ANBN != "S -> a S b | ε"


def test_from_text_comments_and_eps():
    grammar = ContextFreeGrammar.from_text(
        "# commentaire\n\nS -> a S | eps\n", start="S"
    )
    assert grammar.cyk("aaa") and grammar.cyk("")


def test_from_text_errors():
    with pytest.raises(ValueError):
        ContextFreeGrammar.from_text("S a b")
    with pytest.raises(ValueError):
        ContextFreeGrammar.from_text("")
    with pytest.raises(ValueError):
        ContextFreeGrammar.from_text(" -> a")
    with pytest.raises(ValueError):
        ContextFreeGrammar.from_text("A B -> a")


def test_constructor_validation():
    with pytest.raises(ValueError):
        ContextFreeGrammar({"S"}, {"a"}, [], "T")
    with pytest.raises(ValueError):
        ContextFreeGrammar({"S", "a"}, {"a"}, [], "S")
    with pytest.raises(ValueError):
        ContextFreeGrammar({"S"}, {"a"}, [("T", ("a",))], "S")
    with pytest.raises(ValueError):
        ContextFreeGrammar({"S"}, {"a"}, [("S", ("b",))], "S")


def test_rules_sorted():
    assert ANBN.rules("S") == [(), ("a", "S", "b")]


@st.composite
def random_grammars(draw):
    variables = ["S", "A", "B"]
    symbols = variables + ["a", "b"]
    rules = []
    for _ in range(draw(st.integers(min_value=1, max_value=6))):
        lhs = draw(st.sampled_from(variables))
        rhs = tuple(
            draw(st.lists(st.sampled_from(symbols), min_size=0, max_size=3))
        )
        rules.append((lhs, rhs))
    return ContextFreeGrammar(variables, ["a", "b"], rules, "S")


@settings(max_examples=100)
@given(random_grammars())
def test_cyk_equals_earley_on_random_grammars(grammar):
    cnf = grammar.to_cnf()
    assert cnf.is_cnf()
    for word in words("ab", 4):
        assert grammar.cyk(word) == grammar.earley_accepts(word)


@settings(max_examples=100)
@given(random_grammars())
def test_enumeration_matches_membership(grammar):
    listed = set(grammar.enumerate_words(4))
    assert listed == {w for w in words("ab", 4) if grammar.earley_accepts(w)}
    if grammar.is_empty_language():
        assert not listed
