"""Stratégies hypothesis pour générer des automates aléatoires, utilisées
pour le property-based testing (vérifier des invariants mathématiques sur
un grand nombre de cas générés automatiquement, plutôt que des exemples
écrits à la main un par un)."""

from hypothesis import strategies as st
from automata_extensions.fa.dfa import ExtendedDFA

ALPHABET = ['a', 'b']


@st.composite
def dfas(draw, min_states=1, max_states=5):
    """Génère un ExtendedDFA aléatoire, complet, sur l'alphabet {a, b}.

    Complet par construction (chaque état a une transition pour chaque
    symbole), pour éviter d'avoir à gérer allow_partial dans les
    propriétés testées.
    """
    n = draw(st.integers(min_value=min_states, max_value=max_states))
    states = [f"q{i}" for i in range(n)]

    transitions = {}
    for state in states:
        transitions[state] = {
            symbol: draw(st.sampled_from(states)) for symbol in ALPHABET
        }

    initial_state = states[0]
    final_states = draw(
        st.sets(st.sampled_from(states), min_size=0, max_size=n)
    )

    return ExtendedDFA(
        states=set(states),
        input_symbols=set(ALPHABET),
        transitions=transitions,
        initial_state=initial_state,
        final_states=final_states,
    )


words = st.text(alphabet=ALPHABET, max_size=6)
