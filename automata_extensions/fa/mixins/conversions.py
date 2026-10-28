"""Conversions regex <-> automates (Brzozowski, Thompson, etc.)."""

from typing import TYPE_CHECKING, Any, Dict, FrozenSet, Optional, Set, Tuple

from ...regex_ast import (
    RegexNode,
    derivative,
    is_nullable,
    parse_regex,
    to_string,
)
from ._host import FAHost

if TYPE_CHECKING:
    from ..base import ExtendedFA


class ConversionsMixin(FAHost):
    """Regroupe les conversions entre représentations (regex, automates)."""

    def reverse(self) -> Any:
        """Renvoie l'automate renversé : transitions inversées, échange
        initial/finaux. Un nouvel état initial unique est créé, relié par
        epsilon aux anciens états finaux (le résultat est donc un NFA).

        Returns
        -------
        ExtendedNFA
            Un nouvel automate (self n'est jamais modifié : immuabilité).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        from automata.fa.nfa import NFA

        if isinstance(self, NFA):
            native_result = super().reverse()  # type: ignore[misc]
            return self._wrap_native_result(native_result)

        from ..nfa import ExtendedNFA  # import différé pour éviter un cycle

        new_initial = "__reverse_initial__"
        while new_initial in self.states:
            new_initial += "_"

        new_states = set(self.states) | {new_initial}
        new_transitions: Dict[Any, Dict[Any, Set[Any]]] = {
            state: {} for state in new_states
        }

        for state in self.states:
            for symbol in self.input_symbols:
                for target in self._successors(state, symbol):
                    new_transitions[target].setdefault(symbol, set()).add(
                        state
                    )

        # epsilon ('') du nouvel état initial vers les anciens finaux
        new_transitions[new_initial][""] = set(self.final_states)

        return ExtendedNFA(
            states=new_states,
            input_symbols=set(self.input_symbols),
            transitions=new_transitions,
            initial_state=new_initial,
            final_states={self.initial_state},
        )

    def epsilon_closure(self, states: Any) -> Set[Any]:
        """Calcule l'epsilon-fermeture d'un état ou d'un ensemble d'états.

        L'epsilon-fermeture d'un ensemble S est l'ensemble de tous les états
        atteignables depuis S en ne suivant que des transitions epsilon
        (symbole vide '').

        Parameters
        ----------
        states : état unique ou set d'états
            Le ou les états de départ.

        Returns
        -------
        set
            L'epsilon-fermeture (contient toujours au moins `states`).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if not isinstance(states, (set, frozenset)):
            states = {states}

        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()
            for next_state in self._successors(state, ""):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

        return closure

    def determinize(self) -> "ExtendedFA":
        """Convertit un NFA en DFA équivalent (sous-ensembles).

        Ne visite que les sous-ensembles d'états réellement accessibles
        (construction "paresseuse"), plutôt que de générer par avance les
        2^|Q| sous-ensembles possibles.

        Returns
        -------
        ExtendedDFA
            Un DFA équivalent (langage identique).

        Complexity
        ----------
        O(2^|Q|) dans le pire cas, souvent bien moins en pratique.
        """
        from ..dfa import ExtendedDFA

        initial_closure = frozenset(self.epsilon_closure(self.initial_state))

        new_states: Set[FrozenSet[Any]] = {initial_closure}
        new_transitions: Dict[FrozenSet[Any], Dict[Any, FrozenSet[Any]]] = {}
        stack = [initial_closure]
        while stack:
            current = stack.pop()
            # pas de garde "if current in new_transitions" ici : un état
            # n'est poussé sur la pile qu'au moment où il est ajouté à
            # new_states, donc il ne peut jamais y être poussé deux fois.
            new_transitions[current] = {}

            for symbol in self.input_symbols:
                next_set: Set[Any] = set()
                for state in current:
                    next_set |= self._successors(state, symbol)
                next_closure = (
                    frozenset(self.epsilon_closure(next_set))
                    if next_set
                    else frozenset()
                )

                new_transitions[current][symbol] = next_closure
                if next_closure not in new_states:
                    new_states.add(next_closure)
                    stack.append(next_closure)

        # état puits explicite pour les sous-ensembles vides, si nécessaire
        empty_state: FrozenSet[Any] = frozenset()
        if empty_state in new_states:
            new_transitions[empty_state] = {
                symbol: empty_state for symbol in self.input_symbols
            }

        new_final_states = {
            state for state in new_states if state & set(self.final_states)
        }

        # renommage des frozenset en identifiants lisibles (str)
        state_names = {
            state: str(set(state)) if state else "∅" for state in new_states
        }

        return ExtendedDFA(
            states=set(state_names.values()),
            input_symbols=set(self.input_symbols),
            transitions={
                state_names[state]: {
                    symbol: state_names[target]
                    for symbol, target in trans.items()
                }
                for state, trans in new_transitions.items()
            },
            initial_state=state_names[initial_closure],
            final_states={state_names[state] for state in new_final_states},
        )

    def remove_epsilon_transitions(self) -> "ExtendedFA":
        """Renvoie un NFA équivalent sans transitions epsilon.

        Sur un NFA, wrappe eliminate_lambda() natif de automata-lib (même
        tâche, nom différent — pas de collision, mais on évite de dupliquer
        l'algorithme conformément à §4.2 du sujet).
        Sur un DFA, qui n'a jamais de transition epsilon par construction,
        renvoie simplement une copie (immuabilité).

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        from automata.fa.dfa import DFA

        if isinstance(self, DFA):
            automaton_cls: Any = type(self)
            return automaton_cls(
                states=set(self.states),
                input_symbols=set(self.input_symbols),
                transitions={s: dict(p) for s, p in self.transitions.items()},
                initial_state=self.initial_state,
                final_states=set(self.final_states),
                allow_partial=getattr(self, "allow_partial", False),
            )

        native_result = self.eliminate_lambda()
        return self._wrap_native_result(native_result)

    def is_universal_language(self) -> bool:
        """Décide si le langage reconnu est Σ* tout entier (DFA).

        Réduction classique : L(self) = Σ* ssi complement(L(self)) est vide.

        Complexity
        ----------
        O(|Q| . |Σ|)
        """
        return self.complement().is_language_empty()

    def eliminate_epsilon_states_normalized(self) -> "ExtendedFA":
        """Élimination directe des transitions epsilon, sur un ε-AFND
        normalisé (méthode alternative à remove_epsilon_transitions).

        Une transition p --eps--> q n'est éliminée que lorsque q est déjà
        epsilon-libre (aucune transition epsilon sortante) : ses
        transitions réelles sont alors copiées sur p, et p devient final
        si q l'est. On traite ainsi les chaînes epsilon en partant de leur
        extrémité, ce qui évite de propager une information incomplète.

        Suppose l'absence de cycle d'epsilon-transitions (cohérent avec un
        automate "normalisé").

        Complexity
        ----------
        O(|Q|^3) dans le pire cas.
        """
        states = set(self.states)
        transitions = {s: dict(self.transitions.get(s, {})) for s in states}
        final_states = set(self.final_states)

        def eps_targets(state: Any) -> Set[Any]:
            t = transitions[state].get("", set())
            if isinstance(t, str):
                t = {t}
            return set(t)

        progress = True
        while progress:
            progress = False
            for p in list(states):
                for q in eps_targets(p):
                    if eps_targets(q):
                        continue  # q pas encore epsilon-libre : on attend

                    for symbol, targets in transitions.get(q, {}).items():
                        if symbol == "":
                            continue
                        targets = (
                            targets
                            if isinstance(targets, (set, frozenset))
                            else {targets}
                        )
                        existing = transitions[p].get(symbol, set())
                        existing = (
                            existing
                            if isinstance(existing, (set, frozenset))
                            else {existing}
                        )
                        transitions[p][symbol] = existing | targets

                    if q in final_states:
                        final_states.add(p)

                    remaining = eps_targets(p) - {q}
                    if remaining:
                        transitions[p][""] = remaining
                    else:
                        transitions[p].pop("", None)

                    progress = True

        from ..nfa import ExtendedNFA

        return ExtendedNFA(
            states=states,
            input_symbols=set(self.input_symbols),
            transitions=transitions,
            initial_state=self.initial_state,
            final_states=final_states,
        )

    @classmethod
    def regex_to_nfa(cls, regex: str, input_symbols: Set[str]) -> "ExtendedFA":
        """Construit un NFA reconnaissant le langage d'une expression
        régulière (construction de Thompson).

        Wrapper autour de NFA.from_regex() natif de automata-lib.

        Parameters
        ----------
        regex : str
        input_symbols : set

        Returns
        -------
        ExtendedNFA
        """
        from automata.fa.nfa import NFA
        from ..nfa import ExtendedNFA

        native_result = NFA.from_regex(regex, input_symbols=input_symbols)
        return ExtendedNFA(
            states=set(native_result.states),
            input_symbols=set(native_result.input_symbols),
            transitions={
                s: dict(p) for s, p in native_result.transitions.items()
            },
            initial_state=native_result.initial_state,
            final_states=set(native_result.final_states),
        )

    def to_regex_state_elimination(self) -> str:
        """Convertit l'automate en expression régulière équivalente, par
        élimination d'états successive.

        Wrapper autour de GNFA.from_dfa(...).to_regex() natif de
        automata-lib (le GNFA est justement la structure interne dédiée à
        cette élimination d'états). Si self est un NFA, il est d'abord
        déterminisé.

        Returns
        -------
        str

        Complexity
        ----------
        O(|Q|^3) taille de l'expression résultante.
        """
        from automata.fa.dfa import DFA
        from automata.fa.gnfa import GNFA

        dfa: Any = self if isinstance(self, DFA) else self.determinize()
        gnfa = GNFA.from_dfa(dfa)
        return gnfa.to_regex()

    @staticmethod
    def brzozowski_derivative(regex: str, symbol: str) -> str:
        """Calcule la dérivée de Brzozowski d'une expression régulière par
        rapport à un symbole (calcul récursif direct sur l'AST).

        Parameters
        ----------
        regex : str
        symbol : str

        Returns
        -------
        str
            La dérivée, sous forme d'expression régulière.

        Complexity
        ----------
        O(taille de regex) par dérivée.
        """
        node = parse_regex(regex)
        return to_string(derivative(node, symbol))

    @classmethod
    def antimirov_automaton(
        cls, regex: str, input_symbols: Set[str]
    ) -> "ExtendedFA":
        """Construit l'automate d'Antimirov d'une expression régulière :
        un NFA dont les états sont les dérivées partielles successives.

        Parameters
        ----------
        regex : str
        input_symbols : set

        Returns
        -------
        ExtendedNFA
            NFA sans transition epsilon, d'au plus n + 1 états, où n est
            le nombre d'occurrences de symboles dans `regex`.

        Complexity
        ----------
        Au plus n + 1 états (théorème d'Antimirov), donc beaucoup plus
        petit en général que l'automate de Brzozowski.

        References
        ----------
        V. Antimirov, Partial derivatives of regular expressions and
        finite automaton constructions, TCS 155 (1996).
        """
        from ...regex_ast import is_nullable, parse_regex
        from ...regex_ast import partial_derivatives
        from ..nfa import ExtendedNFA

        root = parse_regex(regex)
        names: Dict[RegexNode, str] = {root: "q0"}
        transitions: Dict[str, Dict[str, Set[str]]] = {}
        stack = [root]

        while stack:
            node = stack.pop()
            targets: Dict[str, Set[str]] = {}
            for symbol in sorted(input_symbols):
                reached = partial_derivatives(node, symbol)
                if not reached:
                    continue
                for target in sorted(reached, key=repr):
                    if target not in names:
                        names[target] = f"q{len(names)}"
                        stack.append(target)
                targets[symbol] = {names[t] for t in reached}
            transitions[names[node]] = targets

        return ExtendedNFA(
            states=set(names.values()),
            input_symbols=set(input_symbols),
            transitions=transitions,
            initial_state="q0",
            final_states={names[n] for n in names if is_nullable(n)},
        )

    @classmethod
    def brzozowski_automaton(
        cls, regex: str, input_symbols: Set[str]
    ) -> "ExtendedFA":
        """Construit l'automate de Brzozowski d'une expression régulière :
        les états sont les dérivées distinctes de l'expression de départ.

        Parameters
        ----------
        regex : str
        input_symbols : set

        Returns
        -------
        ExtendedDFA

        Complexity
        ----------
        Dépend du nombre de dérivées distinctes (fini pour tout langage
        régulier, mais peut être exponentiel en théorie ; les
        simplifications de regex_ast le limitent en pratique).
        """
        from ..dfa import ExtendedDFA

        root = parse_regex(regex)
        state_names = {root: "q0"}
        counter = [1]

        def name_for(node: RegexNode) -> str:
            if node not in state_names:
                state_names[node] = f"q{counter[0]}"
                counter[0] += 1
            return state_names[node]

        transitions: Dict[str, Dict[str, str]] = {}
        stack = [root]
        seen = {root}

        while stack:
            node = stack.pop()
            transitions[name_for(node)] = {}
            for symbol in input_symbols:
                d = derivative(node, symbol)
                if d not in seen:
                    seen.add(d)
                    stack.append(d)
                transitions[name_for(node)][symbol] = name_for(d)

        final_states = {state_names[n] for n in seen if is_nullable(n)}

        return ExtendedDFA(
            states=set(state_names.values()),
            input_symbols=set(input_symbols),
            transitions=transitions,
            initial_state=name_for(root),
            final_states=final_states,
            allow_partial=True,
        )

    def to_regex_arden(self) -> str:
        """Convertit l'automate en expression régulière équivalente, par
        résolution du système d'équations de langages associé (lemme
        d'Arden). Réutilise solve_equation_system (#58) : chaque état est
        une variable, avec pour coefficients ses transitions sortantes et
        pour constante epsilon s'il est final.

        Returns
        -------
        str

        Complexity
        ----------
        O(|Q|^3)
        """
        from ...regex_ast import solve_equation_system
        from automata.fa.dfa import DFA

        dfa: Any = self if isinstance(self, DFA) else self.determinize()

        equations: Dict[Any, Tuple[Dict[Any, str], Optional[str]]] = {}
        for state in dfa.states:
            coef: Dict[Any, str] = {}
            for symbol in dfa.input_symbols:
                for target in dfa._successors(state, symbol):
                    coef[target] = coef.get(target, "")
                    coef[target] = (
                        symbol
                        if not coef[target]
                        else f"({coef[target]}|{symbol})"
                    )
            const = "" if state in dfa.final_states else None
            equations[state] = (coef, const)

        return solve_equation_system(
            equations, start_variable=dfa.initial_state
        )
