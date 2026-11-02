"""Automates de Büchi non déterministes.

Un automate de Büchi lit un mot infini. Il l'accepte si l'un de ses
calculs passe une infinité de fois par un état acceptant.

Les mots infinis traités ici sont les mots ultimement périodiques
`prefix . loop^omega` (« lassos »), représentés par le couple
`(prefix, loop)` avec `loop` non vide. Deux automates de Büchi ont le
même langage s'ils acceptent les mêmes lassos : c'est ce que testent les
propriétés du projet.
"""

from collections import deque
from typing import (
    Any,
    Deque,
    Dict,
    FrozenSet,
    Hashable,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

State = Hashable
Lasso = Tuple[List[str], List[str]]


class BuchiAutomaton:
    """Automate de Büchi avec un état initial, immuable.

    Parameters
    ----------
    states : états (objets hachables).
    input_symbols : alphabet.
    transitions : dictionnaire `(état, lettre)` vers un itérable
        d'états d'arrivée.
    initial_state : état initial.
    accepting_states : états acceptants.
    """

    def __init__(
        self,
        states: Iterable[State],
        input_symbols: Iterable[str],
        transitions: Mapping[Tuple[State, str], Iterable[State]],
        initial_state: State,
        accepting_states: Iterable[State],
    ) -> None:
        self.states: FrozenSet[State] = frozenset(states)
        self.input_symbols: FrozenSet[str] = frozenset(input_symbols)
        self.initial_state = initial_state
        self.accepting_states: FrozenSet[State] = frozenset(accepting_states)
        self.transitions: Dict[Tuple[State, str], FrozenSet[State]] = {
            key: frozenset(targets) for key, targets in transitions.items()
        }
        self._validate()

    def _validate(self) -> None:
        if self.initial_state not in self.states:
            raise ValueError(f"état initial inconnu : {self.initial_state!r}")
        if not self.accepting_states <= self.states:
            raise ValueError("états acceptants inconnus")
        for (state, letter), targets in self.transitions.items():
            if state not in self.states:
                raise ValueError(f"état inconnu : {state!r}")
            if letter not in self.input_symbols:
                raise ValueError(f"lettre inconnue : {letter!r}")
            if not targets <= self.states:
                raise ValueError("états d'arrivée inconnus")

    def __repr__(self) -> str:
        count = sum(len(t) for t in self.transitions.values())
        return (
            f"BuchiAutomaton({len(self.states)} états, {count} transitions, "
            f"{len(self.accepting_states)} acceptants)"
        )

    @classmethod
    def from_dfa(cls, dfa: Any) -> "BuchiAutomaton":
        """Lit un DFA comme un automate de Büchi (états finals devenus
        acceptants) : il accepte les mots infinis dont une infinité de
        préfixes sont dans le langage du DFA. Fonctionne avec tout objet
        qui a `states`, `input_symbols`, `transitions` (dictionnaire de
        dictionnaires), `initial_state` et `final_states`."""
        transitions: Dict[Tuple[State, str], Set[State]] = {}
        for state, row in dfa.transitions.items():
            for letter, target in row.items():
                transitions[(state, letter)] = {target}
        return cls(
            dfa.states,
            dfa.input_symbols,
            transitions,
            dfa.initial_state,
            dfa.final_states,
        )

    # ------------------------------------------------------------------
    # Graphe
    # ------------------------------------------------------------------

    def successors(self, state: State, letter: str) -> FrozenSet[State]:
        """États atteignables depuis `state` en lisant `letter`."""
        return self.transitions.get((state, letter), frozenset())

    def _moves(self, state: State) -> List[Tuple[str, State]]:
        """Arcs sortants `(lettre, cible)`, dans un ordre déterministe."""
        arcs = [
            (letter, target)
            for letter in sorted(self.input_symbols)
            for target in sorted(self.successors(state, letter), key=repr)
        ]
        return arcs

    def _shortest_paths(
        self, sources: Iterable[State]
    ) -> Dict[State, List[str]]:
        """Plus court mot menant des `sources` à chaque état atteint
        (mot vide pour les sources elles-mêmes)."""
        words: Dict[State, List[str]] = {s: [] for s in sources}
        queue: Deque[State] = deque(words)
        while queue:
            state = queue.popleft()
            for letter, target in self._moves(state):
                if target not in words:
                    words[target] = words[state] + [letter]
                    queue.append(target)
        return words

    def reachable_states(self) -> FrozenSet[State]:
        """États atteignables depuis l'état initial."""
        return frozenset(self._shortest_paths([self.initial_state]))

    def _cycle_word(self, state: State) -> Optional[List[str]]:
        """Plus court mot non vide qui ramène de `state` à `state`."""
        first = {}
        queue: Deque[State] = deque()
        for letter, target in self._moves(state):
            if target not in first:
                first[target] = [letter]
                queue.append(target)
        while queue:
            current = queue.popleft()
            if current == state:
                return first[current]
            for letter, target in self._moves(current):
                if target not in first:
                    first[target] = first[current] + [letter]
                    queue.append(target)
        return None

    def find_accepted_lasso(self) -> Optional[Lasso]:
        """Un mot infini accepté, sous la forme `(prefix, loop)`, ou None
        si le langage est vide.

        Un mot est accepté si et seulement s'il existe un état
        acceptant atteignable qui est sur un cycle : le préfixe mène à
        cet état, la boucle le parcourt. On choisit le lasso le plus
        court.

        Complexity
        ----------
        O(|F| (|Q| + |delta|)).
        """
        prefixes = self._shortest_paths([self.initial_state])
        best: Optional[Tuple[int, Lasso]] = None
        for state in sorted(self.accepting_states, key=repr):
            if state not in prefixes:
                continue
            loop = self._cycle_word(state)
            if loop is None:
                continue
            size = len(prefixes[state]) + len(loop)
            if best is None or size < best[0]:
                best = (size, (prefixes[state], loop))
        return None if best is None else best[1]

    def is_empty(self) -> bool:
        """Le langage (de mots infinis) est-il vide ?"""
        return self.find_accepted_lasso() is None

    # ------------------------------------------------------------------
    # Reconnaissance d'un lasso
    # ------------------------------------------------------------------

    def accepts_lasso(
        self, prefix: Sequence[str], loop: Sequence[str]
    ) -> bool:
        """Le mot `prefix . loop^omega` est-il accepté ?

        On lit `prefix`, puis on construit le graphe dont les arcs sont
        les lectures complètes de `loop` (marqués si un état acceptant
        est traversé). Le mot est accepté si et seulement si un arc
        marqué, atteignable, est sur un cycle de ce graphe.

        Complexity
        ----------
        O(|Q|^2 |loop| |delta|) dans le pire cas.
        """
        if len(loop) == 0:
            raise ValueError("la boucle ne doit pas être vide")
        current: Set[State] = {self.initial_state}
        for letter in prefix:
            current = {t for s in current for t in self.successors(s, letter)}
        # Arcs du graphe des segments : état -> {(cible, marqué)}.
        segment: Dict[State, Set[Tuple[State, bool]]] = {}

        def read_loop(origin: State) -> Set[Tuple[State, bool]]:
            frontier = {(origin, False)}
            for letter in loop:
                frontier = {
                    (t, flag or t in self.accepting_states)
                    for s, flag in frontier
                    for t in self.successors(s, letter)
                }
            return frontier

        def edges(state: State) -> Set[Tuple[State, bool]]:
            if state not in segment:
                segment[state] = read_loop(state)
            return segment[state]

        def closure(sources: Iterable[State]) -> Set[State]:
            seen = set(sources)
            stack = list(seen)
            while stack:
                state = stack.pop()
                for target, _ in edges(state):
                    if target not in seen:
                        seen.add(target)
                        stack.append(target)
            return seen

        for state in closure(current):
            for target, marked in edges(state):
                if marked and state in closure([target]):
                    return True
        return False

    # ------------------------------------------------------------------
    # Opérations
    # ------------------------------------------------------------------

    def intersection(self, other: "BuchiAutomaton") -> "BuchiAutomaton":
        """Automate de Büchi pour l'intersection des langages
        (construction de Choueka).

        Les états sont `(p, q, i)` où `i` indique quel automate on attend :
        `i = 0` tant qu'on attend un état acceptant du premier, `i = 1`
        ensuite pour le second ; l'indicateur repasse à 0 quand le
        second est vu. Sont acceptants les `(p, q, 1)` avec `q`
        acceptant : on les revisite infiniment souvent si et seulement
        si les deux acceptent infiniment souvent. L'alphabet est
        l'intersection des alphabets.

        Complexity
        ----------
        O(2 |Q1| |Q2|) états.
        """
        alphabet = self.input_symbols & other.input_symbols
        start = (self.initial_state, other.initial_state, 0)
        states: Set[Tuple[State, State, int]] = {start}
        transitions: Dict[Tuple[State, str], Set[State]] = {}
        queue: Deque[Tuple[State, State, int]] = deque([start])
        while queue:
            p, q, flag = queue.popleft()
            if flag == 0 and p in self.accepting_states:
                new_flag = 1
            elif flag == 1 and q in other.accepting_states:
                new_flag = 0
            else:
                new_flag = flag
            for letter in sorted(alphabet):
                for p2 in self.successors(p, letter):
                    for q2 in other.successors(q, letter):
                        target = (p2, q2, new_flag)
                        transitions.setdefault(((p, q, flag), letter), set())
                        transitions[((p, q, flag), letter)].add(target)
                        if target not in states:
                            states.add(target)
                            queue.append(target)
        accepting = {
            s for s in states if s[2] == 1 and s[1] in other.accepting_states
        }
        return BuchiAutomaton(states, alphabet, transitions, start, accepting)

    def union(self, other: "BuchiAutomaton") -> "BuchiAutomaton":
        """Automate de Büchi pour l'union des langages : union disjointe
        (états étiquetés 0 et 1) plus un nouvel état initial qui copie
        les transitions des deux anciens états initiaux."""
        start: State = ("init",)
        states: Set[State] = {start}
        transitions: Dict[Tuple[State, str], Set[State]] = {}
        accepting: Set[State] = set()
        for tag, automaton in enumerate((self, other)):
            states |= {(tag, s) for s in automaton.states}
            accepting |= {(tag, s) for s in automaton.accepting_states}
            for (state, letter), targets in automaton.transitions.items():
                tagged = {(tag, t) for t in targets}
                transitions.setdefault(((tag, state), letter), set())
                transitions[((tag, state), letter)] |= tagged
                if state == automaton.initial_state:
                    transitions.setdefault((start, letter), set())
                    transitions[(start, letter)] |= tagged
        return BuchiAutomaton(
            states,
            self.input_symbols | other.input_symbols,
            transitions,
            start,
            accepting,
        )
