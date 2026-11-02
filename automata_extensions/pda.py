"""Automates à pile non déterministes.

Un automate à pile (PDA) lit un mot en manipulant une pile. Une
transition `(état, lettre ou "", sommet)` mène à un ensemble de couples
`(état, symboles empilés)` : le sommet est dépilé, puis les symboles
sont empilés (le premier symbole du tuple devient le nouveau sommet).
La lettre "" désigne une epsilon-transition.

Le langage reconnu est défini soit par état final, soit par pile vide.
"""

from collections import deque
from typing import (
    TYPE_CHECKING,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

if TYPE_CHECKING:
    from .cfg import ContextFreeGrammar

Push = Union[str, Sequence[str]]
Config = Tuple[str, int, Tuple[str, ...]]
Key = Tuple[str, str, str]
Move = Tuple[str, Tuple[str, ...]]

ACCEPTANCE_MODES = ("final_state", "empty_stack")


class PDA:
    """Automate à pile non déterministe, immuable.

    Parameters
    ----------
    states, input_symbols, stack_symbols : itérables de chaînes.
    transitions : dictionnaire `(état, lettre ou "", sommet)` vers un
        itérable de `(état d'arrivée, symboles empilés)`. Les symboles
        empilés forment un tuple (le premier devient le sommet) ; une
        simple chaîne est lue caractère par caractère.
    initial_state, initial_stack_symbol : départ.
    final_states : états finals (mode `final_state`).
    acceptance : `"final_state"` ou `"empty_stack"`.
    """

    def __init__(
        self,
        states: Iterable[str],
        input_symbols: Iterable[str],
        stack_symbols: Iterable[str],
        transitions: Mapping[Key, Iterable[Tuple[str, Push]]],
        initial_state: str,
        initial_stack_symbol: str,
        final_states: Iterable[str] = (),
        acceptance: str = "final_state",
    ) -> None:
        self.states: FrozenSet[str] = frozenset(states)
        self.input_symbols: FrozenSet[str] = frozenset(input_symbols)
        self.stack_symbols: FrozenSet[str] = frozenset(stack_symbols)
        self.initial_state = initial_state
        self.initial_stack_symbol = initial_stack_symbol
        self.final_states: FrozenSet[str] = frozenset(final_states)
        self.acceptance = acceptance
        self.transitions: Dict[Key, FrozenSet[Move]] = {
            key: frozenset((target, tuple(push)) for target, push in moves)
            for key, moves in transitions.items()
        }
        self._validate()

    def _validate(self) -> None:
        if self.acceptance not in ACCEPTANCE_MODES:
            raise ValueError(f"mode d'acceptation inconnu : {self.acceptance}")
        if self.initial_state not in self.states:
            raise ValueError(f"état initial inconnu : {self.initial_state!r}")
        if self.initial_stack_symbol not in self.stack_symbols:
            raise ValueError(
                f"symbole de pile initial inconnu : "
                f"{self.initial_stack_symbol!r}"
            )
        if not self.final_states <= self.states:
            raise ValueError("états finals inconnus")
        for (state, letter, top), moves in self.transitions.items():
            if state not in self.states:
                raise ValueError(f"état inconnu : {state!r}")
            if letter != "" and letter not in self.input_symbols:
                raise ValueError(f"lettre inconnue : {letter!r}")
            if top not in self.stack_symbols:
                raise ValueError(f"sommet de pile inconnu : {top!r}")
            for target, push in moves:
                if target not in self.states:
                    raise ValueError(f"état d'arrivée inconnu : {target!r}")
                if not set(push) <= self.stack_symbols:
                    raise ValueError(f"symboles empilés inconnus : {push}")

    def __repr__(self) -> str:
        count = sum(len(moves) for moves in self.transitions.values())
        return (
            f"PDA({len(self.states)} états, {count} transitions, "
            f"acceptation={self.acceptance!r})"
        )

    # ------------------------------------------------------------------
    # Exécution
    # ------------------------------------------------------------------

    def initial_config(self) -> Config:
        """Configuration de départ : (état initial, 0, pile initiale)."""
        return (self.initial_state, 0, (self.initial_stack_symbol,))

    def _is_accepting(self, config: Config, length: int) -> bool:
        state, position, stack = config
        if position != length:
            return False
        if self.acceptance == "empty_stack":
            return not stack
        return state in self.final_states

    def _next_configs(
        self, config: Config, word: Sequence[str]
    ) -> Iterable[Config]:
        state, position, stack = config
        if not stack:
            return
        top, rest = stack[0], stack[1:]
        letters = [""]
        if position < len(word):
            letters.append(word[position])
        for letter in letters:
            step = 1 if letter else 0
            for target, push in self.transitions.get((state, letter, top), ()):
                yield (target, position + step, push + rest)

    def find_run(
        self,
        word: Sequence[str],
        max_stack_height: Optional[int] = None,
    ) -> Optional[List[Config]]:
        """Cherche un calcul acceptant (parcours en largeur).

        Renvoie la liste des configurations `(état, position, pile)` de
        la configuration initiale à une configuration acceptante (la
        pile est un tuple dont le sommet est en tête), ou None.

        Le non-déterminisme et les epsilon-transitions peuvent faire
        grandir la pile sans fin : on borne donc sa hauteur par
        `max_stack_height` (par défaut `len(word) + 2`). Cette borne ne
        perd aucun mot pour les automates issus d'une grammaire en forme
        normale de Chomsky (`cfg_to_pda`) ni pour les exemples usuels ;
        pour un automate quelconque, c'est une recherche bornée : un
        résultat négatif prouve seulement l'absence de calcul de pile
        bornée.

        Complexity
        ----------
        Au plus (états x positions x piles de hauteur bornée)
        configurations : exponentiel en la borne dans le pire cas.
        """
        bound = len(word) + 2 if max_stack_height is None else max_stack_height
        start = self.initial_config()
        parent: Dict[Config, Optional[Config]] = {start: None}
        queue: Deque[Config] = deque([start])
        while queue:
            config = queue.popleft()
            if self._is_accepting(config, len(word)):
                run: List[Config] = []
                current: Optional[Config] = config
                while current is not None:
                    run.append(current)
                    current = parent[current]
                run.reverse()
                return run
            for nxt in self._next_configs(config, word):
                if len(nxt[2]) <= bound and nxt not in parent:
                    parent[nxt] = config
                    queue.append(nxt)
        return None

    def accepts(
        self,
        word: Sequence[str],
        max_stack_height: Optional[int] = None,
    ) -> bool:
        """Le mot est-il accepté ? (voir `find_run` pour la borne.)"""
        return self.find_run(word, max_stack_height) is not None

    def is_deterministic(self) -> bool:
        """Au plus un choix dans chaque situation, et aucun conflit entre
        une epsilon-transition et une transition qui lit une lettre."""
        by_situation: Dict[Tuple[str, str], List[str]] = {}
        for (state, letter, top), moves in self.transitions.items():
            if len(moves) > 1:
                return False
            if moves:
                by_situation.setdefault((state, top), []).append(letter)
        return all(
            "" not in letters or len(letters) == 1
            for letters in by_situation.values()
        )


def cfg_to_pda(grammar: "ContextFreeGrammar") -> PDA:
    """Automate à pile (pile vide) équivalent à la grammaire.

    On convertit d'abord en forme normale de Chomsky. L'automate n'a
    qu'un état `q` ; la pile contient la forme sentielle restant à
    dériver (sommet = symbole le plus à gauche). Une production A -> w
    devient l'epsilon-transition `(q, "", A) -> (q, w)` et chaque
    terminal a donne `(q, a, a) -> (q, ε)` : le mot est accepté si et
    seulement si une dérivation gauche l'engendre.

    Complexity
    ----------
    Linéaire en la taille de la grammaire en forme normale.
    """
    cnf = grammar.to_cnf()
    transitions: Dict[Key, Set[Move]] = {}
    for lhs, rhs in cnf.productions:
        transitions.setdefault(("q", "", lhs), set()).add(("q", rhs))
    for terminal in cnf.terminals:
        transitions[("q", terminal, terminal)] = {("q", ())}
    return PDA(
        {"q"},
        cnf.terminals,
        cnf.variables | cnf.terminals,
        transitions,
        "q",
        cnf.start,
        acceptance="empty_stack",
    )
