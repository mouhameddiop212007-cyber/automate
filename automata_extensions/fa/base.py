"""Classe de base ExtendedFA : combine tous les mixins d'algorithmes ajoutés
aux automates finis de automata-lib, sans jamais modifier automata-lib."""

from .mixins.analyse import AnalyseMixin
from .mixins.operations import OperationsMixin
from .mixins.conversions import ConversionsMixin
from .mixins.grammaire import GrammaireMixin
from .mixins.visualisation import VisualisationMixin


class ExtendedFA(
    AnalyseMixin,
    OperationsMixin,
    ConversionsMixin,
    GrammaireMixin,
    VisualisationMixin,
):
    """Regroupe tous les algorithmes ajoutés. À combiner via héritage multiple
    avec une classe de automata-lib, ex: class ExtendedDFA(ExtendedFA, DFA)."""

    def _successors(self, state, symbol):
        """Renvoie les états atteints depuis `state` en lisant `symbol`.

        Uniformise DFA (transitions[state][symbol] = état unique) et
        NFA (transitions[state][symbol] = ensemble d'états), pour que les
        algorithmes du mixin n'aient jamais à faire cette distinction.

        Returns
        -------
        set
            Ensemble des états successeurs (vide si pas de transition).
        """
        targets = self.transitions.get(state, {}).get(symbol, set())
        if isinstance(targets, (set, frozenset)):
            return set(targets)
        return {targets}

    def _wrap_native_result(self, automaton):
        """Reconstruit un automate Extended* à partir d'un automate natif
        automata-lib (ex: renvoyé par une méthode wrappée comme complement()),
        pour que le résultat reste chaînable avec nos propres algorithmes.

        Le type Extended* choisi correspond au type RÉEL de `automaton`
        (DFA ou NFA), pas à celui de self : certaines opérations natives
        (concatenate, kleene_star...) renvoient toujours un NFA même si
        self était un DFA.
        """
        from automata.fa.dfa import DFA
        from automata.fa.nfa import NFA
        from .dfa import ExtendedDFA
        from .nfa import ExtendedNFA

        if isinstance(automaton, DFA):
            target_cls = ExtendedDFA
        elif isinstance(automaton, NFA):
            target_cls = ExtendedNFA
        else:
            target_cls = type(self)

        kwargs = dict(
            states=set(automaton.states),
            input_symbols=set(automaton.input_symbols),
            transitions={s: dict(p) for s, p in automaton.transitions.items()},
            initial_state=automaton.initial_state,
            final_states=set(automaton.final_states),
        )
        if isinstance(automaton, DFA):
            kwargs["allow_partial"] = getattr(
                automaton, "allow_partial", False
            )
        return target_cls(**kwargs)
