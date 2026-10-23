from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.regex_ast import arden_lemma
from tests.conftest import make_simple_dfa


def test_regex_to_nfa_accepts_matching_words():
    nfa = ExtendedNFA.regex_to_nfa('a*b', input_symbols={'a', 'b'})
    assert nfa.accepts_input('b') is True
    assert nfa.accepts_input('aab') is True
    assert nfa.accepts_input('a') is False


def test_to_regex_state_elimination_roundtrip():
    dfa = make_simple_dfa()
    regex = dfa.to_regex_state_elimination()
    assert isinstance(regex, str)
    assert len(regex) > 0
    # vérifie la cohérence : reconstruire un NFA depuis la regex obtenue
    # doit reconnaître le même langage que dfa
    reconstructed = ExtendedNFA.regex_to_nfa(
        regex, input_symbols=dfa.input_symbols
    )
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == reconstructed.accepts_input(word)


def test_brzozowski_derivative_simple():
    # dérivée de "ab" par 'a' = "b"
    result = ExtendedDFA.brzozowski_derivative("ab", "a")
    assert result == "b"


def test_brzozowski_derivative_no_match():
    # dérivée de "ab" par 'b' = ∅ (pas de mot commençant par 'b')
    result = ExtendedDFA.brzozowski_derivative("ab", "b")
    assert result == "∅"


def test_brzozowski_automaton_accepts_correct_language():
    dfa = ExtendedDFA.brzozowski_automaton("a*b", input_symbols={"a", "b"})
    assert dfa.accepts_input("b") is True
    assert dfa.accepts_input("aab") is True
    assert dfa.accepts_input("a") is False
    assert dfa.accepts_input("") is False


def test_brzozowski_automaton_union():
    dfa = ExtendedDFA.brzozowski_automaton("a|b", input_symbols={"a", "b"})
    assert dfa.accepts_input("a") is True
    assert dfa.accepts_input("b") is True
    assert dfa.accepts_input("ab") is False


def test_to_regex_arden_roundtrip():
    dfa = make_simple_dfa()
    regex = dfa.to_regex_arden()
    assert isinstance(regex, str)
    assert len(regex) > 0
    reconstructed = ExtendedNFA.regex_to_nfa(
        regex, input_symbols=dfa.input_symbols
    )
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == reconstructed.accepts_input(word)


def test_to_regex_arden_agrees_with_state_elimination():
    dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '1'},
            '2': {'a': '2', 'b': '3'},
            '3': {'a': '3', 'b': '3'},
        },
        initial_state='1',
        final_states={'3'},
    )
    arden_regex = dfa.to_regex_arden()
    elimination_regex = dfa.to_regex_state_elimination()
    # les deux méthodes doivent reconnaître le même langage (pas forcément
    # la même expression textuelle)
    arden_nfa = ExtendedNFA.regex_to_nfa(
        arden_regex, input_symbols=dfa.input_symbols
    )
    elim_nfa = ExtendedNFA.regex_to_nfa(
        elimination_regex, input_symbols=dfa.input_symbols
    )
    for word in ['', 'a', 'b', 'ab', 'ba', 'aab', 'abb', 'aaa']:
        assert arden_nfa.accepts_input(word) == elim_nfa.accepts_input(word)


def test_arden_lemma_simple():
    # X = aX + b  =>  X = a*b
    result = arden_lemma('a', 'b')
    assert result == 'a*b'


def test_solve_equation_system_two_variables():
    from automata_extensions.regex_ast import solve_equation_system

    # X = aY (X non-acceptant : pas de mot vide) ; Y = bX + ε (Y acceptant)
    # Langage attendu : a(ba)*
    equations = {
        'X': ({'Y': 'a'}, None),
        'Y': ({'X': 'b'}, ''),
    }
    result = solve_equation_system(equations, start_variable='X')
    reconstructed = ExtendedNFA.regex_to_nfa(result, input_symbols={'a', 'b'})
    assert reconstructed.accepts_input('a') is True
    assert reconstructed.accepts_input('aba') is True
    assert reconstructed.accepts_input('b') is False
    assert reconstructed.accepts_input('') is False
