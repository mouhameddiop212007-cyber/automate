"""Fixtures partagées entre tous les fichiers de test."""

from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.fa.nfa import ExtendedNFA


def make_simple_dfa():
    return ExtendedDFA(
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


def make_epsilon_nfa():
    """NFA avec transitions epsilon : 1 --eps--> 2 --eps--> 3, et 1 --a--> 1"""
    return ExtendedNFA(
        states={'1', '2', '3'},
        input_symbols={'a'},
        transitions={
            '1': {'a': {'1'}, '': {'2'}},
            '2': {'': {'3'}},
            '3': {},
        },
        initial_state='1',
        final_states={'3'},
    )
