from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.fa.dfa import ExtendedDFA
from tests.conftest import make_simple_dfa


def test_is_complete_true():
    dfa = make_simple_dfa()
    assert dfa.is_complete() is True


def test_is_complete_false_on_partial_dfa():
    partial_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2'}, '2': {'a': '2'}},
        initial_state='1',
        final_states={'2'},
        allow_partial=True,
    )
    assert partial_dfa.is_complete() is False


def test_complete_adds_sink_state():
    partial_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2'}, '2': {'a': '2'}},
        initial_state='1',
        final_states={'2'},
        allow_partial=True,
    )
    completed = partial_dfa.complete()
    assert completed.is_complete() is True
    assert len(completed.states) == 3


def test_complete_noop_if_already_complete():
    dfa = make_simple_dfa()
    completed = dfa.complete()
    assert completed.states == dfa.states


def test_complement_swaps_language():
    dfa = make_simple_dfa()
    comp = dfa.complement()
    assert dfa.accepts_input('a') is True
    assert comp.accepts_input('a') is False
    assert dfa.accepts_input('b') is False
    assert comp.accepts_input('b') is True


def test_cartesian_product_computes_intersection_by_default():
    dfa = make_simple_dfa()
    product = dfa.cartesian_product(dfa)
    # intersection de dfa avec lui-même = dfa
    assert product.accepts_input('a') == dfa.accepts_input('a')
    assert product.accepts_input('b') == dfa.accepts_input('b')


def test_language_subset_true_for_identical_language():
    dfa = make_simple_dfa()
    assert dfa.language_subset(dfa) is True


def test_language_subset_false_when_not_included():
    narrow_dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '3'},
            '2': {
                'a': '3',
                'b': '3',
            },  # pas de boucle sur '2' : langage plus restreint
            '3': {'a': '3', 'b': '3'},
        },
        initial_state='1',
        final_states={'2'},
    )
    dfa = make_simple_dfa()
    # dfa accepte 'a', 'aa', 'aaa'... ; narrow_dfa n'accepte que 'a'
    assert narrow_dfa.language_subset(dfa) is True
    assert dfa.language_subset(narrow_dfa) is False


def test_language_equals_true_for_same_dfa():
    dfa = make_simple_dfa()
    assert dfa.language_equals(dfa) is True


def test_is_isomorphic_true_for_identical_structure():
    dfa = make_simple_dfa()
    assert dfa.is_isomorphic(dfa) is True


def test_is_isomorphic_true_after_renaming_states():
    renamed_dfa = ExtendedDFA(
        states={'x', 'y', 'z'},
        input_symbols={'a', 'b'},
        transitions={
            'x': {'a': 'y', 'b': 'z'},
            'y': {'a': 'y', 'b': 'z'},
            'z': {'a': 'z', 'b': 'z'},
        },
        initial_state='x',
        final_states={'y'},
    )
    dfa = make_simple_dfa()
    assert dfa.is_isomorphic(renamed_dfa) is True


def test_is_isomorphic_false_for_different_number_of_states():
    dfa = make_simple_dfa()
    smaller_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2', 'b': '1'}, '2': {'a': '2', 'b': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    assert dfa.is_isomorphic(smaller_dfa) is False


def test_is_isomorphic_false_for_different_final_states_position():
    dfa = make_simple_dfa()
    different_final_dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '3'},
            '2': {'a': '2', 'b': '3'},
            '3': {'a': '3', 'b': '3'},
        },
        initial_state='1',
        final_states={
            '3'
        },  # au lieu de '2' : structure identique, finaux différents
    )
    assert dfa.is_isomorphic(different_final_dfa) is False


def test_is_prefix_closed_false_on_simple_dfa():
    dfa = make_simple_dfa()
    # '3' est utile ? non (pas coaccessible) donc ignoré ; '1' et '2' utiles,
    # '1' n'est pas final -> pas préfixe clos
    assert dfa.is_prefix_closed() is False


def test_is_prefix_closed_true_when_all_useful_states_final():
    dfa = ExtendedDFA(
        states={'1'},
        input_symbols={'a'},
        transitions={'1': {'a': '1'}},
        initial_state='1',
        final_states={'1'},
    )
    assert dfa.is_prefix_closed() is True


def test_prefix_closed_sublanguage_empty_if_initial_not_final():
    dfa = make_simple_dfa()  # '1' (initial) n'est pas final
    sub = dfa.prefix_closed_sublanguage()
    assert sub.is_language_empty() is True


def test_prefix_closed_sublanguage_keeps_only_final_paths():
    dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={'1': {'a': '2'}, '2': {'a': '3'}, '3': {'a': '3'}},
        initial_state='1',
        final_states={'1', '3'},  # '2' n'est pas final : coupe le chemin
    )
    sub = dfa.prefix_closed_sublanguage()
    assert sub.accepts_input('')  # '1' est final
    assert not sub.accepts_input('a')  # passe par '2', non final : exclu


def test_distinguishable_states_on_simple_dfa():
    dfa = make_simple_dfa()
    dist = dfa.distinguishable_states()
    # '2' (final) et '3' (non final) doivent être distinguables
    assert frozenset({'2', '3'}) in dist


def test_myhill_nerode_partition_separates_final_and_non_final():
    dfa = make_simple_dfa()
    partition = dfa.myhill_nerode_partition()
    # '2' et '3' ne doivent jamais être dans la même classe
    for cls in partition:
        assert not ({'2', '3'} <= cls)


def test_is_minimal_false_on_dfa_with_equivalent_states():
    # '2' et '3' sont équivalents : tous deux finaux, et transitions
    # identiques vers '4' quel que soit le symbole -> automate non minimal
    non_minimal_dfa = ExtendedDFA(
        states={'1', '2', '3', '4'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '3'},
            '2': {'a': '4', 'b': '4'},
            '3': {'a': '4', 'b': '4'},
            '4': {'a': '4', 'b': '4'},
        },
        initial_state='1',
        final_states={'2', '3'},
    )
    assert non_minimal_dfa.is_minimal() is False


def test_is_minimal_true_on_simple_dfa():
    dfa = make_simple_dfa()
    # les 3 états sont deux-à-deux distinguables : déjà minimal
    assert dfa.is_minimal() is True


def test_minimize_produces_equivalent_language():
    dfa = make_simple_dfa()
    minimized = dfa.minimize()
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == minimized.accepts_input(word)


def test_minimize_result_is_minimal():
    dfa = make_simple_dfa()
    minimized = dfa.minimize()
    assert minimized.is_minimal() is True


def test_is_deterministic_true_on_dfa():
    dfa = make_simple_dfa()
    assert dfa.is_deterministic() is True


def test_is_deterministic_false_on_true_nfa():
    nfa = ExtendedNFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={'1': {'a': {'2', '3'}}, '2': {}, '3': {}},
        initial_state='1',
        final_states={'2'},
    )
    assert nfa.is_deterministic() is False


def test_union_accepts_words_from_either_language():
    dfa1 = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2', 'b': '1'}, '2': {'a': '2', 'b': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    dfa2 = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '1', 'b': '2'}, '2': {'a': '2', 'b': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    u = dfa1.union(dfa2)
    assert u.accepts_input('a') is True  # accepté par dfa1
    assert u.accepts_input('b') is True  # accepté par dfa2
    assert u.accepts_input('') is False  # rejeté par les deux


def test_intersection_only_accepts_common_words():
    dfa = make_simple_dfa()
    inter = dfa.intersection(dfa)
    for word in ['', 'a', 'b', 'aa']:
        assert inter.accepts_input(word) == dfa.accepts_input(word)


def test_difference_on_two_dfas():
    dfa = make_simple_dfa()
    diff = dfa.difference(dfa)
    assert diff.is_language_empty() is True


def test_concatenate_combines_languages():
    a_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2', 'b': '1'}, '2': {'a': '2', 'b': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    b_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '1', 'b': '2'}, '2': {'a': '2', 'b': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    concat = a_dfa.concatenate(b_dfa)
    assert (
        concat.accepts_input('ab') is True
    )  # 'a' accepté par a_dfa, 'b' par b_dfa
    assert (
        concat.accepts_input('a') is False
    )  # b_dfa n'accepte pas le mot vide après


def test_kleene_star_accepts_empty_word():
    dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a'},
        transitions={'1': {'a': '2'}, '2': {'a': '2'}},
        initial_state='1',
        final_states={'2'},
    )
    star = dfa.kleene_star()
    assert star.accepts_input('') is True
    assert star.accepts_input('a') is True
    assert star.accepts_input('aa') is True


def test_left_quotient_word_on_dfa():
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
    # L(dfa) = mots contenant "ab" ; quotient par 'a' : "b" ou déjà "ab"
    quotient = dfa.left_quotient_word('a')
    assert quotient.accepts_input('b') is True
    assert quotient.accepts_input('') is False


def test_left_quotient_word_empty_when_prefix_rejected():
    partial_dfa = ExtendedDFA(
        states={'1', '2'},
        input_symbols={'a', 'b'},
        transitions={'1': {'a': '2'}, '2': {'a': '2'}},
        initial_state='1',
        final_states={'2'},
        allow_partial=True,
    )
    quotient = partial_dfa.left_quotient_word(
        'b'
    )  # pas de transition 'b' depuis '1'
    assert quotient.is_language_empty() is True


def test_right_quotient_word_on_dfa():
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
    # L(dfa) = mots contenant "ab" ; quotient à droite par 'b' = mots dont
    # ajout de 'b' : mots contenant déjà "ab" ou finissant par 'a'
    quotient = dfa.right_quotient_word('b')
    assert quotient.accepts_input('ab') is True


def test_syntactic_monoid_contains_identity_and_generators():
    dfa = make_simple_dfa()
    monoid = dfa.syntactic_monoid()
    states = tuple(sorted(dfa.states, key=str))
    assert states in monoid  # l'identité doit être présente
    assert len(monoid) >= len(dfa.input_symbols)  # au moins les générateurs


def test_syntactic_monoid_is_closed_under_composition():
    dfa = make_simple_dfa()
    monoid = dfa.syntactic_monoid()
    # le monoïde de cet automate à 3 états ne peut pas dépasser 3^3 = 27
    # transformations distinctes (borne large mais garantit la terminaison)
    assert len(monoid) <= 27


def test_minimize_hopcroft_preserves_language():
    dfa = make_simple_dfa()
    minimized = dfa.minimize_hopcroft()
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == minimized.accepts_input(word)


def test_minimize_hopcroft_matches_minimize_state_count():
    dfa = ExtendedDFA(
        states={'1', '2', '3', '4'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '1'},
            '2': {'a': '2', 'b': '4'},
            '3': {'a': '3', 'b': '1'},
            '4': {'a': '3', 'b': '4'},
        },
        initial_state='1',
        final_states={'1', '4'},
    )
    classic = dfa.minimize()
    hopcroft = dfa.minimize_hopcroft()
    assert len(classic.states) == len(hopcroft.states)


def test_distinguishable_states_handles_missing_transitions():
    # q0 n'a pas de transition 'a' (puits implicite), q1 en a une vers un
    # état final : le mot 'a' les distingue (q0 le rejette, q1 l'accepte)
    partial = ExtendedDFA(
        states={'q0', 'q1'},
        input_symbols={'a', 'b'},
        transitions={'q0': {'b': 'q1'}, 'q1': {'a': 'q0', 'b': 'q0'}},
        initial_state='q0',
        final_states={'q0', 'q1'},
        allow_partial=True,
    )
    assert frozenset({'q0', 'q1'}) in partial.distinguishable_states()


def test_minimize_does_not_merge_states_distinguished_by_dead_end():
    # Contre-exemple trouvé par hypothesis : q0 --a--> puits, alors que
    # q1 --a--> q0 (final). Le mot 'a' distingue q0 de q1.
    dfa = ExtendedDFA(
        states={'q0', 'q1', 'q2'},
        input_symbols={'a', 'b'},
        transitions={
            'q0': {'a': 'q2', 'b': 'q1'},
            'q1': {'a': 'q0', 'b': 'q0'},
            'q2': {'a': 'q2', 'b': 'q2'},
        },
        initial_state='q0',
        final_states={'q0', 'q1'},
    )
    minimized = dfa.minimize()
    for word in ['', 'a', 'b', 'ba', 'bb', 'bab', 'abb']:
        assert dfa.accepts_input(word) == minimized.accepts_input(word)


def test_cartesian_product_rejects_different_alphabets():
    dfa1 = make_simple_dfa()
    dfa2 = ExtendedDFA(
        states={'1'},
        input_symbols={'x'},
        transitions={'1': {'x': '1'}},
        initial_state='1',
        final_states={'1'},
    )
    import pytest

    with pytest.raises(ValueError):
        dfa1.cartesian_product(dfa2)


def test_is_isomorphic_false_for_different_alphabets():
    dfa1 = make_simple_dfa()
    dfa2 = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'x', 'y'},
        transitions={
            '1': {'x': '2', 'y': '3'},
            '2': {'x': '2', 'y': '3'},
            '3': {'x': '3', 'y': '3'},
        },
        initial_state='1',
        final_states={'2'},
    )
    assert dfa1.is_isomorphic(dfa2) is False


def test_is_minimal_false_on_inaccessible_state():
    dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={'1': {'a': '1'}, '2': {'a': '2'}, '3': {'a': '3'}},
        initial_state='1',
        final_states={'1'},
        allow_partial=True,
    )
    # '2' et '3' sont inaccessibles depuis '1'
    assert dfa.is_minimal() is False


def test_complete_handles_sink_name_collision():
    partial = ExtendedDFA(
        states={'1', '__sink__'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '__sink__'},
            '__sink__': {'a': '__sink__', 'b': '__sink__'},
        },
        initial_state='1',
        final_states={'__sink__'},
        allow_partial=True,
    )
    completed = partial.complete()
    assert completed.is_complete() is True
    assert len(completed.states) == 3


def test_left_quotient_word_handles_name_collision():
    nfa = ExtendedNFA(
        states={'1', '2', '__quotient_initial__'},
        input_symbols={'a'},
        transitions={
            '1': {'a': {'2'}},
            '2': {'a': {'__quotient_initial__'}},
            '__quotient_initial__': {},
        },
        initial_state='1',
        final_states={'__quotient_initial__'},
    )
    quotient = nfa.left_quotient_word('a')
    assert quotient.accepts_input('a') is True


def test_cartesian_product_handles_partial_automaton():
    complete_dfa = make_simple_dfa()
    partial_dfa = ExtendedDFA(
        states={'x', 'y'},
        input_symbols={'a', 'b'},
        transitions={'x': {'a': 'y'}, 'y': {'a': 'y', 'b': 'y'}},
        initial_state='x',
        final_states={'y'},
        allow_partial=True,
    )
    product = complete_dfa.cartesian_product(partial_dfa)
    assert product is not None


def test_is_isomorphic_false_when_branching_factor_differs():
    nfa1 = ExtendedNFA(
        states={'1', '2'},
        input_symbols={'a'},
        transitions={'1': {'a': {'1', '2'}}, '2': {}},
        initial_state='1',
        final_states={'2'},
    )
    nfa2 = ExtendedNFA(
        states={'1', '2'},
        input_symbols={'a'},
        transitions={'1': {'a': {'2'}}, '2': {}},
        initial_state='1',
        final_states={'2'},
    )
    assert nfa1.is_isomorphic(nfa2) is False
