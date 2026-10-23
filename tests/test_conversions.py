from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.fa.dfa import ExtendedDFA
from tests.conftest import make_simple_dfa, make_epsilon_nfa


def test_reverse_swaps_initial_and_final():
    dfa = make_simple_dfa()
    reversed_automaton = dfa.reverse()
    assert isinstance(reversed_automaton, ExtendedNFA)
    assert reversed_automaton.final_states == {'1'}


def test_reverse_accepts_reversed_language():
    dfa = make_simple_dfa()
    # le DFA original accepte les mots qui finissent en état '2'
    # (un seul 'a' depuis '1', sans jamais lire 'b' avant)
    assert dfa.accepts_input('a')
    reversed_automaton = dfa.reverse()
    # le mot inverse de 'a' est 'a' (palindrome trivial ici)
    assert reversed_automaton.accepts_input('a')


def test_epsilon_closure_single_state():
    nfa = make_epsilon_nfa()
    assert nfa.epsilon_closure('1') == {'1', '2', '3'}


def test_epsilon_closure_no_epsilon_transitions():
    nfa = make_epsilon_nfa()
    assert nfa.epsilon_closure('3') == {'3'}


def test_epsilon_closure_on_set_of_states():
    nfa = make_epsilon_nfa()
    assert nfa.epsilon_closure({'2', '3'}) == {'2', '3'}


def test_epsilon_closure_trivial_on_dfa():
    dfa = make_simple_dfa()
    # un DFA n'a jamais de transition epsilon : fermeture = l'état seul
    assert dfa.epsilon_closure('1') == {'1'}


def test_determinize_produces_dfa():
    from automata.fa.dfa import DFA

    nfa = make_epsilon_nfa()
    dfa = nfa.determinize()
    assert isinstance(dfa, DFA)


def test_determinize_preserves_language():
    nfa = make_epsilon_nfa()
    dfa = nfa.determinize()
    # les deux automates doivent accepter/rejeter les mêmes mots
    for word in ['', 'a', 'aa', 'aaa']:
        assert nfa.accepts_input(word) == dfa.accepts_input(word)


def test_determinize_on_multi_target_nfa():
    # NFA avec un vrai non-déterminisme (une transition vers plusieurs états)
    nfa = ExtendedNFA(
        states={'1', '2', '3'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': {'1', '2'}},
            '2': {'b': {'3'}},
            '3': {},
        },
        initial_state='1',
        final_states={'3'},
    )
    dfa = nfa.determinize()
    for word in ['', 'a', 'ab', 'b', 'aab', 'aaab']:
        assert nfa.accepts_input(word) == dfa.accepts_input(word)


def test_reverse_on_nfa_uses_native_and_stays_extended():
    nfa = ExtendedNFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2'}, '2': {}},
        initial_state='1',
        final_states={'2'},
    )
    reversed_nfa = nfa.reverse()
    assert isinstance(reversed_nfa, ExtendedNFA)
    assert reversed_nfa.accepts_input('a') is True
    assert reversed_nfa.accepts_input('b') is False


def test_is_deterministic_false_on_epsilon_nfa():
    nfa = make_epsilon_nfa()
    assert nfa.is_deterministic() is False


def test_remove_epsilon_transitions_on_nfa():
    nfa = make_epsilon_nfa()
    cleaned = nfa.remove_epsilon_transitions()
    for word in ['', 'a', 'aa', 'aaa']:
        assert nfa.accepts_input(word) == cleaned.accepts_input(word)


def test_remove_epsilon_transitions_noop_on_dfa():
    dfa = make_simple_dfa()
    result = dfa.remove_epsilon_transitions()
    assert result.states == dfa.states


def test_is_universal_language_false_on_simple_dfa():
    dfa = make_simple_dfa()
    assert dfa.is_universal_language() is False


def test_is_universal_language_true():
    universal_dfa = ExtendedDFA(
        states={'1'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '1', 'b': '1'}},
        initial_state='1',
        final_states={'1'},
    )
    assert universal_dfa.is_universal_language() is True


def test_eliminate_epsilon_states_normalized_preserves_language():
    nfa = make_epsilon_nfa()
    result = nfa.eliminate_epsilon_states_normalized()
    for word in ['', 'a', 'aa', 'aaa']:
        assert nfa.accepts_input(word) == result.accepts_input(word)


def test_difference_determinizes_nfa_input():
    nfa = ExtendedNFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': {'2'}, '': {'2'}}, '2': {'b': {'2'}}},
        initial_state='1',
        final_states={'2'},
    )
    dfa = make_simple_dfa()
    # ne doit pas planter même avec un NFA en entrée (même alphabet ici)
    result = nfa.difference(dfa)
    assert result is not None


def test_reverse_handles_name_collision():
    dfa = ExtendedDFA(
        states={'1', '__reverse_initial__'},
        input_symbols={'a'},
        transitions={
            '1': {'a': '__reverse_initial__'},
            '__reverse_initial__': {'a': '__reverse_initial__'},
        },
        initial_state='1',
        final_states={'__reverse_initial__'},
    )
    reversed_dfa = dfa.reverse()
    assert reversed_dfa.accepts_input('a') is True


def test_eliminate_epsilon_states_normalized_copies_real_transitions():
    nfa = ExtendedNFA(
        states={'1', '2', '3', '4'},
        input_symbols={'a'},
        transitions={
            '1': {'': {'2', '3'}},
            '2': {'a': {'4'}},
            '3': {'': {'4'}},
            '4': {},
        },
        initial_state='1',
        final_states={'4'},
    )
    result = nfa.eliminate_epsilon_states_normalized()
    for word in ['', 'a']:
        assert nfa.accepts_input(word) == result.accepts_input(word)
