from automata_extensions.fa.dfa import ExtendedDFA


def test_extended_dfa_instantiation():
    """Vérifie que ExtendedDFA fonctionne comme un DFA normal (héritage OK)."""
    dfa = ExtendedDFA(
        states={'1', '2', '3'},
        input_symbols={'a', 'b'},
        transitions={
            '1': {'a': '2', 'b': '3'},
            '2': {'a': '2', 'b': '3'},
            '3': {'a': '3', 'b': '3'},
        },
        initial_state='1',
        final_states={'2'},
    )
    assert dfa.accepts_input('a')
    assert not dfa.accepts_input('b')
