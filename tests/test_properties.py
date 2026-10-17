
"""Property-based testing : vérifie des invariants mathématiques sur des
automates générés aléatoirement (hypothesis), en complément des tests
unitaires classiques à exemples fixes.
"""

from hypothesis import given, settings
from tests.strategies import dfas, words


@given(dfa=dfas())
@settings(max_examples=200)
def test_minimize_is_idempotent(dfa):
    """Minimiser un automate déjà minimal ne doit rien changer (à
    isomorphisme près) : minimize(minimize(x)) a le même nombre d'états
    que minimize(x)."""
    once = dfa.minimize()
    twice = once.minimize()
    assert len(once.states) == len(twice.states)


@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_minimize_preserves_language(dfa, word):
    """Minimiser ne doit jamais changer le langage reconnu."""
    minimized = dfa.minimize()
    assert dfa.accepts_input(word) == minimized.accepts_input(word)


@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_complement_of_complement_is_original_language(dfa, word):
    """Le complément du complément doit reconnaître le même langage que
    l'automate de départ (involution)."""
    double_complement = dfa.complement().complement()
    assert dfa.accepts_input(word) == double_complement.accepts_input(word)


@given(dfa1=dfas(max_states=3), dfa2=dfas(max_states=3), word=words)
@settings(max_examples=200)
def test_union_is_commutative(dfa1, dfa2, word):
    """L(a ∪ b) = L(b ∪ a)."""
    u1 = dfa1.union(dfa2)
    u2 = dfa2.union(dfa1)
    assert u1.accepts_input(word) == u2.accepts_input(word)


@given(dfa1=dfas(max_states=3), dfa2=dfas(max_states=3), word=words)
@settings(max_examples=200)
def test_intersection_is_commutative(dfa1, dfa2, word):
    """L(a ∩ b) = L(b ∩ a)."""
    i1 = dfa1.intersection(dfa2)
    i2 = dfa2.intersection(dfa1)
    assert i1.accepts_input(word) == i2.accepts_input(word)


@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_accessible_states_is_subset_of_states(dfa, word):
    """Les états accessibles sont toujours un sous-ensemble des états de
    l'automate (propriété structurelle de base)."""
    assert dfa.accessible_states().issubset(dfa.states)


@given(dfa=dfas())
@settings(max_examples=200)
def test_trim_result_is_always_trim(dfa):
    """Après un trim(), l'automate résultant doit toujours être trim —
    sauf le cas particulier du langage vide, où trim() renvoie
    volontairement un automate à 1 état non-coaccessible plutôt que de
    ne pas pouvoir construire d'automate du tout (0 état est impossible,
    un état initial est obligatoire)."""
    trimmed = dfa.trim()
    if trimmed.is_language_empty():
        return  # cas particulier assumé, voir docstring de trim()
    assert trimmed.is_trim() is True

@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_reverse_twice_preserves_language(dfa, word):
    """Renverser deux fois un automate doit redonner le même langage
    (le mot renversé deux fois = le mot lui-même)."""
    double_reversed = dfa.reverse().reverse()
    assert dfa.accepts_input(word) == double_reversed.accepts_input(word)


@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_to_grammar_roundtrip_preserves_language(dfa, word):
    """Convertir en grammaire puis reconstruire l'automate ne doit pas
    changer le langage reconnu (#55, aller-retour)."""
    from automata_extensions.fa.nfa import ExtendedNFA
    grammar = dfa.to_grammar()
    rebuilt = ExtendedNFA.grammar_to_automaton(grammar)
    assert dfa.accepts_input(word) == rebuilt.accepts_input(word)


@given(dfa=dfas())
@settings(max_examples=200)
def test_kleene_star_always_accepts_empty_word(dfa):
    """L'étoile de Kleene de n'importe quel langage doit toujours
    accepter le mot vide (par définition, L* contient toujours ε)."""
    star = dfa.kleene_star()
    assert star.accepts_input('') is True


@given(dfa=dfas())
@settings(max_examples=200)
def test_language_equals_is_reflexive(dfa):
    """Un automate doit toujours être équivalent à lui-même."""
    assert dfa.language_equals(dfa) is True


@given(dfa=dfas())
@settings(max_examples=200)
def test_is_isomorphic_is_reflexive(dfa):
    """Un automate doit toujours être isomorphe à lui-même (identité)."""
    assert dfa.is_isomorphic(dfa) is True


@given(dfa1=dfas(max_states=3), dfa2=dfas(max_states=3), word=words)
@settings(max_examples=200)
def test_difference_of_self_is_always_empty(dfa1, dfa2, word):
    """L(a) - L(a) doit toujours être vide, quel que soit l'automate."""
    diff = dfa1.difference(dfa1)
    assert diff.accepts_input(word) is False

@given(dfa=dfas(), word=words)
@settings(max_examples=200)
def test_minimize_hopcroft_agrees_with_classic_minimize(dfa, word):
    """Les deux algorithmes de minimisation doivent reconnaître le même
    langage, quel que soit l'automate de départ."""
    classic = dfa.minimize()
    hopcroft = dfa.minimize_hopcroft()
    assert classic.accepts_input(word) == hopcroft.accepts_input(word)

@given(dfa=dfas())
@settings(max_examples=200)
def test_minimal_dfa_is_unique_up_to_isomorphism(dfa):
    """Théorème classique : le DFA minimal d'un langage est unique à
    renommage des états près. Deux algorithmes de minimisation corrects
    (classique et Hopcroft) doivent donc produire des automates
    isomorphes, pas seulement des automates de même langage."""
    assert dfa.minimize().is_isomorphic(dfa.minimize_hopcroft()) is True


@given(dfa=dfas())
@settings(max_examples=200)
def test_minimization_results_are_minimal(dfa):
    """Le résultat des deux algorithmes doit être reconnu minimal par
    is_minimal() (accessible, et tous les états deux à deux
    distinguables)."""
    assert dfa.minimize().is_minimal() is True
    assert dfa.minimize_hopcroft().is_minimal() is True
