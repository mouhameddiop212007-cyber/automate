"""Déclarations de typage partagées par tous les mixins.

Les mixins sont écrits indépendamment de automata-lib mais utilisent les
attributs d'un automate (states, transitions...) fournis par la classe
finale (ExtendedDFA/ExtendedNFA). FAHost déclare ces attributs pour mypy ;
il n'a aucun effet à l'exécution (simples annotations).
"""

from typing import TYPE_CHECKING, Any


class FAHost:
    """Hôte de typage : ce que les mixins attendent de la classe finale."""

    states: Any
    input_symbols: Any
    transitions: Any
    initial_state: Any
    final_states: Any

    if TYPE_CHECKING:
        # Les méthodes des autres mixins et de automata-lib sont connues
        # de la classe finale, pas du mixin isolé : mypy les voit comme Any.
        def __getattr__(self, name: str) -> Any: ...
