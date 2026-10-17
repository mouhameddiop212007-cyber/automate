from automata_extensions.fa.nfa import ExtendedNFA
from automata_extensions.fa.dfa import ExtendedDFA
from tests.conftest import make_simple_dfa, make_epsilon_nfa


def test_to_grammar_produces_regular_grammar():
    dfa = make_simple_dfa()
    grammar = dfa.to_grammar()
    assert grammar.start_variable == '1'
    assert () in grammar.rules['2']  # '2' est final


def test_grammar_to_automaton_roundtrip():
    dfa = make_simple_dfa()
    grammar = dfa.to_grammar()
    rebuilt = ExtendedNFA.grammar_to_automaton(grammar)
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == rebuilt.accepts_input(word)


def test_regular_grammar_rejects_non_linear_rule():
    from automata_extensions.grammar.grammar import RegularGrammar
    import pytest
    with pytest.raises(ValueError):
        RegularGrammar(
            variables={'A', 'B', 'C'},
            terminals={'a'},
            rules={'A': [('a', 'B', 'C')]},  # trop long : pas linéaire à droite
            start_variable='A',
        )


def test_derivation_tree_word_matches_input():
    dfa = make_simple_dfa()
    tree = dfa.derivation_tree('a')
    assert tree.word() == 'a'


def test_derivation_tree_sequence_format():
    dfa = make_simple_dfa()
    tree = dfa.derivation_tree('a')
    sequence = tree.sequence()
    assert sequence == '1 => a2 => a'


def test_myhill_nerode_language_classes_count_matches_minimal_states():
    dfa = make_simple_dfa()
    classes = dfa.myhill_nerode_language_classes()
    minimal = dfa.minimize()
    assert len(classes) == len(minimal.states)


def test_myhill_nerode_language_classes_empty_word_is_self():
    dfa = make_simple_dfa()
    classes = dfa.myhill_nerode_language_classes()
    assert "" in classes
    for word in ['', 'a', 'b']:
        assert classes[""].accepts_input(word) == dfa.accepts_input(word)


def test_residual_automaton_preserves_language():
    dfa = make_simple_dfa()
    residual = dfa.residual_automaton()
    for word in ['', 'a', 'b', 'aa', 'ab', 'ba', 'bb']:
        assert dfa.accepts_input(word) == residual.accepts_input(word)


def test_automaton_morphism_identity_is_valid():
    dfa = make_simple_dfa()
    identity_mapping = {s: s for s in dfa.states}
    assert dfa.automaton_morphism(dfa, identity_mapping) is True


def test_automaton_morphism_detects_invalid_mapping():
    dfa = make_simple_dfa()
    bad_mapping = {'1': '2', '2': '1', '3': '3'}  # ne préserve pas l'état initial
    assert dfa.automaton_morphism(dfa, bad_mapping) is False


def test_automaton_morphism_valid_renaming():
    dfa = make_simple_dfa()
    renamed = ExtendedDFA(
        states={'x', 'y', 'z'}, input_symbols={'a', 'b'},
        transitions={
            'x': {'a': 'y', 'b': 'z'},
            'y': {'a': 'y', 'b': 'z'},
            'z': {'a': 'z', 'b': 'z'},
        },
        initial_state='x', final_states={'y'},
    )
    mapping = {'1': 'x', '2': 'y', '3': 'z'}
    assert dfa.automaton_morphism(renamed, mapping) is True


def test_grammar_repr_shows_rules():
    dfa = make_simple_dfa()
    grammar = dfa.to_grammar()
    text = repr(grammar)
    assert isinstance(text, str)
    assert '->' in text
    assert 'ε' in text  # '2' est final : au moins une règle X -> ε


def test_grammar_equality():
    dfa = make_simple_dfa()
    g1 = dfa.to_grammar()
    g2 = dfa.to_grammar()
    assert g1 == g2


def test_regular_grammar_rejects_non_terminal_first_symbol():
    from automata_extensions.grammar.grammar import RegularGrammar
    import pytest
    with pytest.raises(ValueError):
        RegularGrammar(
            variables={'A', 'B'}, terminals={'a'},
            rules={'A': [('B', 'B')]},  # 'B' n'est pas un terminal
            start_variable='A',
        )


def test_regular_grammar_rejects_non_variable_second_symbol():
    from automata_extensions.grammar.grammar import RegularGrammar
    import pytest
    with pytest.raises(ValueError):
        RegularGrammar(
            variables={'A', 'B'}, terminals={'a', 'b'},
            rules={'A': [('a', 'b')]},  # 'b' n'est pas un non-terminal
            start_variable='A',
        )


def test_grammar_to_automaton_handles_accept_state_collision():
    from automata_extensions.grammar.grammar import RegularGrammar
    grammar = RegularGrammar(
        variables={'__accept__', 'B'}, terminals={'a'},
        rules={'__accept__': [('a', 'B')], 'B': [()]},
        start_variable='__accept__',
    )
    automaton = ExtendedNFA.grammar_to_automaton(grammar)
    assert automaton.accepts_input('a') is True


def test_grammar_to_automaton_handles_single_terminal_production():
    from automata_extensions.grammar.grammar import RegularGrammar
    # A -> a (un terminal seul, sans non-terminal suivant) : le mot
    # s'arrête ici, différent de A -> ε (qui rend A lui-même final)
    grammar = RegularGrammar(
        variables={'A'}, terminals={'a'},
        rules={'A': [('a',)]},
        start_variable='A',
    )
    automaton = ExtendedNFA.grammar_to_automaton(grammar)
    assert automaton.accepts_input('a') is True
    assert automaton.accepts_input('') is False


def test_automaton_morphism_false_on_unmapped_final_state():
    dfa = make_simple_dfa()
    incomplete_mapping = {'1': '1', '2': '2'}  # '3' absent du mapping
    assert dfa.automaton_morphism(dfa, incomplete_mapping) is False


def test_automaton_morphism_false_on_final_state_mismatch():
    dfa = make_simple_dfa()
    wrong_mapping = {'1': '1', '2': '1', '3': '3'}  # '2' (final) -> '1' (non final)
    assert dfa.automaton_morphism(dfa, wrong_mapping) is False


def test_automaton_morphism_false_on_target_not_in_mapping():
    dfa = make_simple_dfa()
    partial_mapping = {'1': '1', '3': '3'}  # '2' absent : l'état initial est OK
    # mais la transition '1' --a--> '2' référence un état hors mapping
    assert dfa.automaton_morphism(dfa, partial_mapping) is False


def test_automaton_morphism_false_on_wrong_target_transition():
    dfa = make_simple_dfa()
    wrong_target_mapping = {'1': '1', '2': '3', '3': '2'}  # états finaux OK par coïncidence mais transitions fausses
    assert dfa.automaton_morphism(dfa, wrong_target_mapping) is False
