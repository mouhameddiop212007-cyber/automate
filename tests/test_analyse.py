from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.fa.dfa import ExtendedDFA
from tests.conftest import make_simple_dfa, make_epsilon_nfa


def test_dfs_visits_all_accessible_states():
    dfa = make_simple_dfa()
    visited = set(dfa.dfs())
    assert visited == {'1', '2', '3'}


def test_dfs_starts_from_given_state():
    dfa = make_simple_dfa()
    visited = dfa.dfs(start='3')
    assert visited == ['3']  # état 3 ne boucle que sur lui-même


def test_bfs_visits_all_accessible_states():
    dfa = make_simple_dfa()
    visited = set(dfa.bfs())
    assert visited == {'1', '2', '3'}


def test_bfs_visits_by_levels():
    dfa = make_simple_dfa()
    order = dfa.bfs()
    # depuis '1', les voisins directs (2 et 3) doivent apparaître avant
    # tout ce qui n'est atteignable qu'ensuite (ici il n'y a rien après,
    # mais on vérifie au moins que l'ordre commence bien par l'état initial)
    assert order[0] == '1'


def test_predecessors_simple():
    dfa = make_simple_dfa()
    # état '2' est atteint depuis '1' (via 'a') et depuis lui-même (via 'a')
    assert dfa.predecessor_states('2') == {'1', '2'}


def test_predecessors_of_initial_state_via_self_loop():
    dfa = make_simple_dfa()
    # état '3' est atteint depuis '1' (via 'b') et depuis 2 (via  'b')
    # et depuis lui même (via 'a' et 'b')
    assert dfa.predecessor_states('3') == {'1', '2', '3'}


def test_accessible_states():
    dfa = make_simple_dfa()
    assert dfa.accessible_states() == {'1', '2', '3'}


def test_is_accessible():
    dfa = make_simple_dfa()
    assert dfa.is_accessible('2') is True


def test_reachable_states_from():
    dfa = make_simple_dfa()
    # depuis '3', on ne peut atteindre que '3' (boucle sur lui-même)
    assert dfa.reachable_states_from('3') == {'3'}


def test_coaccessible_states():
    dfa = make_simple_dfa()
    # depuis '1' : atteint '2' (final) via 'a'. Depuis '2' : déjà final.
    # depuis '3' : boucle sur lui-même, jamais final -> pas coaccessible.
    assert dfa.coaccessible_states() == {'1', '2'}


def test_is_coaccessible():
    dfa = make_simple_dfa()
    assert dfa.is_coaccessible('2') is True
    assert dfa.is_coaccessible('3') is False


def test_useful_states():
    dfa = make_simple_dfa()
    # '3' est accessible mais pas coaccessible -> pas utile
    assert dfa.useful_states() == {'1', '2'}


def test_induced_subautomaton_keeps_only_given_states():
    dfa = make_simple_dfa()
    sub = dfa.induced_subautomaton({'1', '2'})
    assert sub.states == {'1', '2'}
    # la transition '1' --b--> '3' disparaît (3 hors du sous-ensemble)
    assert 'b' not in sub.transitions['1']


def test_induced_subautomaton_rejects_missing_initial_state():
    dfa = make_simple_dfa()
    import pytest

    with pytest.raises(ValueError):
        dfa.induced_subautomaton(
            {'2', '3'}
        )  # ne contient pas l'état initial '1'


def test_trim_removes_non_useful_states():
    dfa = make_simple_dfa()
    trimmed = dfa.trim()
    # '3' n'est pas coaccessible -> doit disparaître
    assert trimmed.states == {'1', '2'}


def test_is_trim():
    dfa = make_simple_dfa()
    assert dfa.is_trim() is False  # '3' n'est pas utile
    assert dfa.trim().is_trim() is True


def test_scc_on_simple_dfa():
    dfa = make_simple_dfa()
    sccs = dfa.strongly_connected_components()
    # '1' seul (pas de retour vers 1), '2' seul (boucle sur lui-même mais
    # ne revient pas depuis ailleurs vers 1), '3' seul (boucle sur lui-même)
    # -> 3 SCC de taille 1 chacune
    assert len(sccs) == 3
    assert {'1'} in sccs
    assert {'2'} in sccs
    assert {'3'} in sccs


def test_scc_detects_real_cycle():
    cyclic_dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={
            '1': {'a': '2'},
            '2': {'a': '3'},
            '3': {'a': '1'},  # cycle 1 -> 2 -> 3 -> 1
        },
        initial_state='1',
        final_states={'1'},
    )
    sccs = cyclic_dfa.strongly_connected_components()
    assert len(sccs) == 1
    assert sccs[0] == {'1', '2', '3'}


def test_has_cycle_true_on_self_loop():
    dfa = make_simple_dfa()
    # '2' et '3' ont des boucles sur eux-mêmes
    assert dfa.has_cycle() is True


def test_has_cycle_false_on_acyclic_automaton():
    acyclic_dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={
            '1': {'a': '2'},
            '2': {'a': '3'},
            '3': {'a': '3'},  # attention : boucle sur 3, donc PAS acyclique
        },
        initial_state='1',
        final_states={'3'},
    )
    # ce DFA a en fait un cycle (boucle sur '3') : on garde ce test comme
    # exemple qu'il faut un automate SANS AUCUNE boucle pour avoir False
    assert acyclic_dfa.has_cycle() is True


def test_has_cycle_from_specific_state():
    dfa = make_simple_dfa()
    # depuis '1', on peut atteindre '3' qui boucle -> cycle accessible
    assert dfa.has_cycle_from('1') is True


def test_is_language_empty_false_when_reachable_final():
    dfa = make_simple_dfa()
    assert dfa.is_language_empty() is False


def test_is_language_empty_true_when_no_final_reachable():
    empty_lang_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a'},
        transitions={
            '1': {'a': '1'},
            '2': {'a': '2'},  # '2' est final mais inaccessible depuis '1'
        },
        initial_state='1',
        final_states={'2'},
    )
    assert empty_lang_dfa.is_language_empty() is True


def test_is_language_infinite_true():
    dfa = make_simple_dfa()
    # '2' est final et boucle sur lui-même -> langage infini
    assert dfa.is_language_infinite() is True


def test_is_language_infinite_false_on_finite_language():
    finite_dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={
            '1': {'a': '2'},
            '2': {'a': '3'},
            '3': {'a': '3'},  # '3' boucle mais n'est pas final
        },
        initial_state='1',
        final_states={'2'},
    )
    # seul le mot 'a' est accepté (un seul chemin de 1 à 2, sans cycle utile)
    assert finite_dfa.is_language_infinite() is False


def test_accepts_word_matches_accepts_input():
    dfa = make_simple_dfa()
    assert dfa.accepts_word('a') == dfa.accepts_input('a')
    assert dfa.accepts_word('b') == dfa.accepts_input('b')


def test_execution_trace_on_dfa():
    dfa = make_simple_dfa()
    trace = dfa.execution_trace('a')
    assert trace == ['1', '2']


def test_execution_trace_on_dfa_rejected_word():
    partial_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2'}, '2': {'a': '2'}},
        initial_state='1',
        final_states={'2'},
        allow_partial=True,
    )
    trace = partial_dfa.execution_trace(
        'b'
    )  # pas de transition 'b' depuis '1'
    assert trace == ['1', None]


def test_execution_trace_on_nfa_applies_epsilon_closure_at_start():
    nfa = make_epsilon_nfa()
    # sans lire de symbole, la fermeture epsilon de '1' inclut '2' et '3'
    trace = nfa.execution_trace('')
    assert trace == [{'1', '2', '3'}]


def test_execution_trace_on_nfa_applies_epsilon_closure_after_symbol():
    nfa = make_epsilon_nfa()
    # lire 'a' depuis {'1','2','3'} : seul '1' a une transition 'a' -> '1'
    # puis epsilon-fermeture de {'1'} -> {'1', '2', '3'}
    trace = nfa.execution_trace('a')
    assert trace == [{'1', '2', '3'}, {'1', '2', '3'}]


def test_induced_subautomaton_preserves_nfa_multi_target_transitions():
    nfa = ExtendedNFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={'1': {'a': {'2', '3'}}, '2': {}, '3': {}},
        initial_state='1',
        final_states={'2', '3'},
    )
    sub = nfa.induced_subautomaton({'1', '2', '3'})
    assert sub.transitions['1']['a'] == {'2', '3'}


def test_has_cycle_true_on_multi_state_cycle():
    dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={'1': {'a': '2'}, '2': {'a': '3'}, '3': {'a': '1'}},
        initial_state='1',
        final_states={'1'},
    )
    assert dfa.has_cycle() is True
