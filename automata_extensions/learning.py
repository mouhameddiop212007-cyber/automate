"""Apprentissage actif d'automates : algorithme L* d'Angluin.

L* retrouve le DFA minimal d'un langage régulier inconnu en interrogeant
un « enseignant » (`Teacher`) :

- question d'appartenance : « ce mot est-il dans le langage ? » ;
- question d'équivalence : « cet automate hypothèse reconnaît-il le bon
  langage ? » ; sinon l'enseignant renvoie un contre-exemple.

On utilise la variante de Maler et Pnueli : un contre-exemple ajoute tous
ses suffixes aux colonnes de la table d'observation, ce qui rend inutile
le test de cohérence de la version d'origine.
"""

from abc import ABC, abstractmethod
from collections import deque
from itertools import product
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
)

from .fa.dfa import ExtendedDFA


class Teacher(ABC):
    """Enseignant (oracle) de L*.

    Les sous-classes définissent `_is_member` et `_find_counterexample` ;
    les méthodes publiques `membership` et `equivalence` comptent les
    questions posées.
    """

    def __init__(self, alphabet: Iterable[str]) -> None:
        self.alphabet: FrozenSet[str] = frozenset(alphabet)
        self.membership_queries = 0
        self.equivalence_queries = 0

    @abstractmethod
    def _is_member(self, word: str) -> bool:
        """Le mot appartient-il au langage cible ?"""

    @abstractmethod
    def _find_counterexample(self, hypothesis: ExtendedDFA) -> Optional[str]:
        """Un mot sur lequel `hypothesis` se trompe, ou None."""

    def membership(self, word: str) -> bool:
        """Question d'appartenance (comptée)."""
        self.membership_queries += 1
        return self._is_member(word)

    def equivalence(self, hypothesis: ExtendedDFA) -> Optional[str]:
        """Question d'équivalence (comptée) : None si l'hypothèse est
        correcte, sinon un contre-exemple."""
        self.equivalence_queries += 1
        return self._find_counterexample(hypothesis)


def _step(dfa: Any, state: Any, symbol: str) -> Any:
    """Successeur dans un DFA éventuellement partiel (None = puits)."""
    if state is None:
        return None
    return dfa.transitions.get(state, {}).get(symbol)


def _accepting(dfa: Any, state: Any) -> bool:
    return state is not None and state in dfa.final_states


class DFATeacher(Teacher):
    """Enseignant dont le langage cible est celui d'un DFA donné.

    L'équivalence est EXACTE et renvoie un contre-exemple de longueur
    minimale (parcours en largeur sur le produit synchronisé).
    """

    def __init__(self, target: Any) -> None:
        super().__init__(target.input_symbols)
        self.target = target

    def _is_member(self, word: str) -> bool:
        return bool(self.target.accepts_input(word))

    def _find_counterexample(self, hypothesis: ExtendedDFA) -> Optional[str]:
        start = (hypothesis.initial_state, self.target.initial_state)
        queue: Deque[Tuple[Any, Any, str]] = deque([(*start, "")])
        visited: Set[Tuple[Any, Any]] = {start}
        while queue:
            hyp_state, target_state, word = queue.popleft()
            if _accepting(hypothesis, hyp_state) != _accepting(
                self.target, target_state
            ):
                return word
            for symbol in sorted(self.alphabet):
                pair = (
                    _step(hypothesis, hyp_state, symbol),
                    _step(self.target, target_state, symbol),
                )
                if pair not in visited:
                    visited.add(pair)
                    queue.append((*pair, word + symbol))
        return None


class PredicateTeacher(Teacher):
    """Enseignant dont le langage cible est défini par une fonction
    Python `predicate(mot) -> bool`.

    L'équivalence est APPROCHÉE : l'hypothèse est comparée à la fonction
    sur tous les mots de longueur au plus `max_length`. Un langage dont
    le DFA minimal est plus grand que ce que `max_length` permet de
    distinguer peut donc être mal appris.
    """

    def __init__(
        self,
        alphabet: Iterable[str],
        predicate: Callable[[str], bool],
        max_length: int = 8,
    ) -> None:
        super().__init__(alphabet)
        self.predicate = predicate
        self.max_length = max_length

    def _is_member(self, word: str) -> bool:
        return bool(self.predicate(word))

    def _find_counterexample(self, hypothesis: ExtendedDFA) -> Optional[str]:
        symbols = sorted(self.alphabet)
        for length in range(self.max_length + 1):
            for letters in product(symbols, repeat=length):
                word = "".join(letters)
                if hypothesis.accepts_input(word) != bool(
                    self.predicate(word)
                ):
                    return word
        return None


def angluin_lstar(teacher: Teacher) -> ExtendedDFA:
    """Apprend le DFA minimal du langage de `teacher` (algorithme L*).

    Parameters
    ----------
    teacher : Teacher
        L'oracle (questions d'appartenance et d'équivalence).

    Returns
    -------
    ExtendedDFA
        Un DFA complet, minimal si l'équivalence de l'enseignant est
        exacte. Les compteurs `teacher.membership_queries` et
        `teacher.equivalence_queries` donnent le nombre de questions.

    Raises
    ------
    ValueError
        Si l'enseignant renvoie un contre-exemple qui n'apporte rien de
        nouveau (enseignant incohérent) : sans ce garde-fou, la boucle
        ne terminerait pas.

    Complexity
    ----------
    Au plus n questions d'équivalence, n étant le nombre d'états du DFA
    minimal ; un nombre polynomial en n, en |Σ| et en la longueur des
    contre-exemples de questions d'appartenance (les réponses sont
    mémorisées : chaque mot n'est demandé qu'une fois).

    References
    ----------
    D. Angluin, Learning regular sets from queries and counterexamples,
    Information and Computation 75 (1987) ; O. Maler et A. Pnueli, On the
    learnability of infinitary regular sets, Information and Computation
    118 (1995) pour la variante par suffixes.
    """
    alphabet = sorted(teacher.alphabet)
    cache: Dict[str, bool] = {}

    def member(word: str) -> bool:
        if word not in cache:
            cache[word] = teacher.membership(word)
        return cache[word]

    prefixes: List[str] = [""]  # lignes de la table : les états
    suffixes: List[str] = [""]  # colonnes de la table : les tests

    def row(word: str) -> Tuple[bool, ...]:
        return tuple(member(word + suffix) for suffix in suffixes)

    while True:
        closed = False
        while not closed:
            closed = True
            known = {row(prefix) for prefix in prefixes}
            for prefix in list(prefixes):
                for symbol in alphabet:
                    extended = prefix + symbol
                    if row(extended) not in known:
                        prefixes.append(extended)
                        known.add(row(extended))
                        closed = False

        names = {prefix: f"q{i}" for i, prefix in enumerate(prefixes)}
        by_row = {row(prefix): prefix for prefix in prefixes}
        transitions = {
            names[prefix]: {
                symbol: names[by_row[row(prefix + symbol)]]
                for symbol in alphabet
            }
            for prefix in prefixes
        }
        hypothesis = ExtendedDFA(
            states=set(names.values()),
            input_symbols=set(alphabet),
            transitions=transitions,
            initial_state="q0",
            final_states={names[p] for p in prefixes if row(p)[0]},
        )

        counterexample = teacher.equivalence(hypothesis)
        if counterexample is None:
            return hypothesis
        added = False
        for start in range(len(counterexample)):
            suffix = counterexample[start:]
            if suffix not in suffixes:
                suffixes.append(suffix)
                added = True
        if not added:
            raise ValueError(
                "contre-exemple déjà pris en compte : enseignant incohérent"
            )
