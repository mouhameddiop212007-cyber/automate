"""Grammaires hors-contexte : forme normale de Chomsky, CYK et Earley.

Une grammaire est un quadruplet (variables, terminaux, productions,
axiome). Une production est un couple (variable, membre droit) où le
membre droit est un tuple de symboles ; le tuple vide est epsilon.

Les symboles sont des chaînes quelconques (« S », « T_a »...). Un mot est
une séquence de terminaux : une chaîne dont chaque caractère est un
terminal, ou une liste de terminaux.
"""

from itertools import product
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

if TYPE_CHECKING:
    from .pda import PDA

Production = Tuple[str, Tuple[str, ...]]
Tree = Tuple[Any, ...]


def _fresh(base: str, taken: Set[str]) -> str:
    """Renvoie un nom absent de `taken` (on ajoute des apostrophes à
    `base` tant qu'il est pris) et l'y enregistre."""
    name = base
    while name in taken:
        name += "'"
    taken.add(name)
    return name


def tree_yield(tree: Tree) -> List[str]:
    """Mot (liste de terminaux) lu sur les feuilles d'un arbre de
    dérivation renvoyé par `cyk_parse`."""
    leaves: List[str] = []
    for child in tree[1:]:
        if isinstance(child, str):
            leaves.append(child)
        else:
            leaves.extend(tree_yield(child))
    return leaves


class ContextFreeGrammar:
    """Grammaire hors-contexte immuable.

    Parameters
    ----------
    variables, terminals : itérables de chaînes (ensembles disjoints).
    productions : itérable de couples (variable, membre droit).
    start : l'axiome (une des variables).
    """

    def __init__(
        self,
        variables: Iterable[str],
        terminals: Iterable[str],
        productions: Iterable[Tuple[str, Iterable[str]]],
        start: str,
    ) -> None:
        self.variables: FrozenSet[str] = frozenset(variables)
        self.terminals: FrozenSet[str] = frozenset(terminals)
        self.productions: FrozenSet[Production] = frozenset(
            (lhs, tuple(rhs)) for lhs, rhs in productions
        )
        self.start = start
        self._cnf: Optional["ContextFreeGrammar"] = None
        self._validate()

    def _validate(self) -> None:
        if self.start not in self.variables:
            raise ValueError(f"axiome inconnu : {self.start!r}")
        common = self.variables & self.terminals
        if common:
            raise ValueError(f"variables et terminaux communs : {common}")
        symbols = self.variables | self.terminals
        for lhs, rhs in self.productions:
            if lhs not in self.variables:
                raise ValueError(f"membre gauche inconnu : {lhs!r}")
            unknown = set(rhs) - symbols
            if unknown:
                raise ValueError(f"symboles inconnus : {unknown}")

    @classmethod
    def from_text(
        cls, text: str, start: Optional[str] = None
    ) -> "ContextFreeGrammar":
        """Construit une grammaire depuis un texte.

        Une règle par ligne : `S -> a S b | ε`. Les symboles sont séparés
        par des espaces ; `ε` (ou `eps`, ou rien) est le mot vide. Les
        variables sont les membres gauches, tous les autres symboles
        sont des terminaux. L'axiome est la première variable, sauf si
        `start` est donné. Les lignes vides et celles qui commencent par
        `#` sont ignorées.
        """
        variables: List[str] = []
        raw: List[Tuple[str, Tuple[str, ...]]] = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                raise ValueError(f"règle sans '->' : {line!r}")
            lhs, rhs_text = line.split("->", 1)
            lhs = lhs.strip()
            if not lhs or " " in lhs:
                raise ValueError(f"membre gauche invalide : {lhs!r}")
            if lhs not in variables:
                variables.append(lhs)
            for alternative in rhs_text.split("|"):
                symbols = alternative.split()
                if symbols in (["ε"], ["eps"]):
                    symbols = []
                raw.append((lhs, tuple(symbols)))
        if not variables:
            raise ValueError("grammaire vide")
        terminals = {
            symbol
            for _, rhs in raw
            for symbol in rhs
            if symbol not in variables
        }
        return cls(variables, terminals, raw, start or variables[0])

    # ------------------------------------------------------------------
    # Affichage, égalité
    # ------------------------------------------------------------------

    def rules(self, variable: str) -> List[Tuple[str, ...]]:
        """Membres droits de `variable`, triés."""
        return sorted(r for lhs, r in self.productions if lhs == variable)

    def __str__(self) -> str:
        order = [self.start] + sorted(self.variables - {self.start})
        lines = []
        for variable in order:
            alternatives = [
                " ".join(rhs) if rhs else "ε" for rhs in self.rules(variable)
            ]
            if alternatives:
                lines.append(f"{variable} -> " + " | ".join(alternatives))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ContextFreeGrammar({str(self)!r})"

    def _key(self) -> Tuple[Any, ...]:
        return (self.variables, self.terminals, self.productions, self.start)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, ContextFreeGrammar)
            and self._key() == other._key()
        )

    def __hash__(self) -> int:
        return hash(self._key())

    # ------------------------------------------------------------------
    # Analyse
    # ------------------------------------------------------------------

    def nullable_variables(self) -> FrozenSet[str]:
        """Variables qui dérivent le mot vide.

        Complexity
        ----------
        O(|G|^2) (point fixe).
        """
        nullable: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                if lhs not in nullable and all(s in nullable for s in rhs):
                    nullable.add(lhs)
                    changed = True
        return frozenset(nullable)

    def generating_variables(self) -> FrozenSet[str]:
        """Variables qui dérivent au moins un mot de terminaux."""
        generating: Set[str] = set()
        changed = True
        while changed:
            changed = False
            for lhs, rhs in self.productions:
                if lhs not in generating and all(
                    s in self.terminals or s in generating for s in rhs
                ):
                    generating.add(lhs)
                    changed = True
        return frozenset(generating)

    def reachable_symbols(self) -> FrozenSet[str]:
        """Symboles (variables et terminaux) accessibles depuis l'axiome."""
        seen = {self.start}
        stack = [self.start]
        while stack:
            symbol = stack.pop()
            for lhs, rhs in self.productions:
                if lhs == symbol:
                    for other in rhs:
                        if other not in seen:
                            seen.add(other)
                            stack.append(other)
        return frozenset(seen)

    def is_empty_language(self) -> bool:
        """Le langage engendré est-il vide ?"""
        return self.start not in self.generating_variables()

    # ------------------------------------------------------------------
    # Simplifications
    # ------------------------------------------------------------------

    def remove_useless(self) -> "ContextFreeGrammar":
        """Supprime les variables non génératrices puis inaccessibles.

        Le langage est inchangé. Si l'axiome est non générateur, le
        langage est vide : on renvoie une grammaire sans production.
        """
        generating = self.generating_variables()
        if self.start not in generating:
            return ContextFreeGrammar(
                {self.start}, self.terminals, set(), self.start
            )
        kept = {
            (lhs, rhs)
            for lhs, rhs in self.productions
            if lhs in generating
            and all(s in self.terminals or s in generating for s in rhs)
        }
        interim = ContextFreeGrammar(
            generating, self.terminals, kept, self.start
        )
        reachable = interim.reachable_symbols()
        return ContextFreeGrammar(
            generating & reachable,
            self.terminals,
            {(lhs, rhs) for lhs, rhs in kept if lhs in reachable},
            self.start,
        )

    def _epsilon_free_productions(self) -> Set[Production]:
        """Productions sans epsilon-règle, qui engendrent les mêmes mots
        non vides : on ajoute, pour chaque règle, toutes les variantes où
        l'on omet des variables annulables."""
        nullable = self.nullable_variables()
        productions: Set[Production] = set()
        for lhs, rhs in self.productions:
            options: List[Tuple[str, ...]] = [()]
            for symbol in rhs:
                extended = [prefix + (symbol,) for prefix in options]
                if symbol in nullable:
                    extended += options
                options = extended
            productions.update((lhs, option) for option in options if option)
        return productions

    def remove_epsilon(self) -> "ContextFreeGrammar":
        """Supprime les epsilon-productions.

        Si l'axiome est annulable (le mot vide est dans le langage), un
        nouvel axiome `S0 -> S | ε` est introduit : c'est la seule
        epsilon-production restante, et S0 n'apparaît dans aucun membre
        droit.

        Complexity
        ----------
        Exponentielle dans le nombre de variables annulables d'un même
        membre droit (au plus 2^k variantes par règle).
        """
        productions = self._epsilon_free_productions()
        variables = set(self.variables)
        start = self.start
        if self.start in self.nullable_variables():
            taken = set(self.variables) | set(self.terminals)
            start = _fresh(self.start + "0", taken)
            variables.add(start)
            productions.add((start, ()))
            productions.add((start, (self.start,)))
        return ContextFreeGrammar(
            variables, self.terminals, productions, start
        )

    @staticmethod
    def _is_unit(rhs: Tuple[str, ...], variables: FrozenSet[str]) -> bool:
        return len(rhs) == 1 and rhs[0] in variables

    def remove_unit_productions(self) -> "ContextFreeGrammar":
        """Supprime les règles unitaires A -> B (B variable) : A reçoit
        les règles non unitaires de toutes les variables B atteintes
        depuis A par des règles unitaires.

        Complexity
        ----------
        O(|V|^2 |P|).
        """
        closure: Dict[str, Set[str]] = {v: {v} for v in self.variables}
        changed = True
        while changed:
            changed = False
            for a in self.variables:
                for b in list(closure[a]):
                    for lhs, rhs in self.productions:
                        if (
                            lhs == b
                            and self._is_unit(rhs, self.variables)
                            and rhs[0] not in closure[a]
                        ):
                            closure[a].add(rhs[0])
                            changed = True
        productions = {
            (a, rhs)
            for a in self.variables
            for b in closure[a]
            for lhs, rhs in self.productions
            if lhs == b and not self._is_unit(rhs, self.variables)
        }
        return ContextFreeGrammar(
            self.variables, self.terminals, productions, self.start
        )

    # ------------------------------------------------------------------
    # Forme normale de Chomsky
    # ------------------------------------------------------------------

    def _with_fresh_start(self) -> "ContextFreeGrammar":
        """Étape START : nouvel axiome S0 -> S, qui n'apparaît jamais à
        droite."""
        taken = set(self.variables) | set(self.terminals)
        start = _fresh(self.start + "0", taken)
        return ContextFreeGrammar(
            self.variables | {start},
            self.terminals,
            set(self.productions) | {(start, (self.start,))},
            start,
        )

    def _wrap_terminals(self) -> "ContextFreeGrammar":
        """Étape TERM : dans les membres droits de longueur >= 2, chaque
        terminal a est remplacé par une variable T_a (avec T_a -> a)."""
        taken = set(self.variables) | set(self.terminals)
        wrappers: Dict[str, str] = {}
        productions: Set[Production] = set()
        for lhs, rhs in sorted(self.productions):
            if len(rhs) < 2:
                productions.add((lhs, rhs))
                continue
            new_rhs: List[str] = []
            for symbol in rhs:
                if symbol in self.terminals:
                    if symbol not in wrappers:
                        wrappers[symbol] = _fresh("T_" + symbol, taken)
                    new_rhs.append(wrappers[symbol])
                else:
                    new_rhs.append(symbol)
            productions.add((lhs, tuple(new_rhs)))
        for terminal, name in wrappers.items():
            productions.add((name, (terminal,)))
        return ContextFreeGrammar(
            self.variables | set(wrappers.values()),
            self.terminals,
            productions,
            self.start,
        )

    def _binarize(self) -> "ContextFreeGrammar":
        """Étape BIN : A -> X1 X2 ... Xn devient A -> X1 A1, A1 -> X2 A2,
        ..., A(n-2) -> X(n-1) Xn."""
        taken = set(self.variables) | set(self.terminals)
        variables = set(self.variables)
        productions: Set[Production] = set()
        counter = 0
        for lhs, rhs in sorted(self.productions):
            current = lhs
            remaining = rhs
            while len(remaining) > 2:
                counter += 1
                name = _fresh(f"{lhs}_{counter}", taken)
                variables.add(name)
                productions.add((current, (remaining[0], name)))
                current = name
                remaining = remaining[1:]
            productions.add((current, remaining))
        return ContextFreeGrammar(
            variables, self.terminals, productions, self.start
        )

    def to_cnf(self) -> "ContextFreeGrammar":
        """Convertit en forme normale de Chomsky (même langage).

        Toute production est alors A -> a, ou A -> B C ; seul l'axiome
        peut avoir A -> ε, et il n'apparaît alors dans aucun membre
        droit. Étapes : START, TERM, BIN, DEL (epsilon), UNIT, puis
        suppression des variables inutiles.

        Complexity
        ----------
        Taille de la grammaire obtenue en O(|G|^2) dans le pire cas.

        References
        ----------
        Hopcroft, Motwani, Ullman, Introduction to Automata Theory,
        Languages and Computation, section 7.1.
        """
        grammar = self._with_fresh_start()._wrap_terminals()._binarize()
        nullable_start = grammar.start in grammar.nullable_variables()
        grammar = ContextFreeGrammar(
            grammar.variables,
            grammar.terminals,
            grammar._epsilon_free_productions(),
            grammar.start,
        ).remove_unit_productions()
        if nullable_start:
            grammar = ContextFreeGrammar(
                grammar.variables,
                grammar.terminals,
                set(grammar.productions) | {(grammar.start, ())},
                grammar.start,
            )
        return grammar.remove_useless()

    def is_cnf(self) -> bool:
        """La grammaire est-elle en forme normale de Chomsky ?"""
        on_the_right = {s for _, rhs in self.productions for s in rhs}
        for lhs, rhs in self.productions:
            if len(rhs) == 1 and rhs[0] in self.terminals:
                continue
            if len(rhs) == 2 and all(s in self.variables for s in rhs):
                continue
            if (
                rhs == ()
                and lhs == self.start
                and self.start not in on_the_right
            ):
                continue
            return False
        return True

    def _normal_form(self) -> "ContextFreeGrammar":
        if self.is_cnf():
            return self
        if self._cnf is None:
            self._cnf = self.to_cnf()
        return self._cnf

    # ------------------------------------------------------------------
    # Reconnaissance
    # ------------------------------------------------------------------

    def cyk_table(self, word: Sequence[str]) -> List[List[FrozenSet[str]]]:
        """Table de l'algorithme CYK : `table[l - 1][i]` est l'ensemble des
        variables qui dérivent la sous-chaîne de longueur l commençant en
        i (calculée sur la forme normale de Chomsky).

        Complexity
        ----------
        O(n^3 |G|) pour un mot de longueur n.
        """
        grammar = self._normal_form()
        length_n = len(word)
        by_terminal: Dict[str, Set[str]] = {}
        binary: List[Tuple[str, str, str]] = []
        for lhs, rhs in grammar.productions:
            if len(rhs) == 1:
                by_terminal.setdefault(rhs[0], set()).add(lhs)
            elif len(rhs) == 2:
                binary.append((lhs, rhs[0], rhs[1]))
        table: List[List[Set[str]]] = [
            [set() for _ in range(length_n - size + 1)]
            for size in range(1, length_n + 1)
        ]
        for i, symbol in enumerate(word):
            table[0][i] = set(by_terminal.get(symbol, set()))
        for size in range(2, length_n + 1):
            for i in range(length_n - size + 1):
                cell = table[size - 1][i]
                for split in range(1, size):
                    left = table[split - 1][i]
                    right = table[size - split - 1][i + split]
                    if left and right:
                        for lhs, b, c in binary:
                            if b in left and c in right:
                                cell.add(lhs)
        return [[frozenset(cell) for cell in row] for row in table]

    def cyk(self, word: Sequence[str]) -> bool:
        """Le mot est-il engendré ? (algorithme CYK sur la forme normale
        de Chomsky.)

        Complexity
        ----------
        O(n^3 |G|).

        References
        ----------
        Cocke, Younger, Kasami (1965-1967).
        """
        grammar = self._normal_form()
        if len(word) == 0:
            return (grammar.start, ()) in grammar.productions
        table = self.cyk_table(word)
        return grammar.start in table[len(word) - 1][0]

    def accepts(self, word: Sequence[str]) -> bool:
        """Synonyme de `cyk`."""
        return self.cyk(word)

    def cyk_parse(self, word: Sequence[str]) -> Optional[Tree]:
        """Arbre de dérivation du mot dans la forme normale de Chomsky,
        ou None s'il n'est pas engendré.

        Un nœud est `(variable, fils_gauche, fils_droit)` ; une feuille
        est `(variable, terminal)` ; le mot vide donne `(axiome,)`.
        `tree_yield(arbre)` redonne le mot.
        """
        grammar = self._normal_form()
        if len(word) == 0:
            if (grammar.start, ()) in grammar.productions:
                return (grammar.start,)
            return None
        table = self.cyk_table(word)
        if grammar.start not in table[len(word) - 1][0]:
            return None
        binary = sorted(
            (lhs, rhs[0], rhs[1])
            for lhs, rhs in grammar.productions
            if len(rhs) == 2
        )

        def build(variable: str, i: int, size: int) -> Tree:
            if size == 1:
                return (variable, word[i])
            for split in range(1, size):
                for lhs, b, c in binary:
                    if (
                        lhs == variable
                        and b in table[split - 1][i]
                        and c in table[size - split - 1][i + split]
                    ):
                        return (
                            variable,
                            build(b, i, split),
                            build(c, i + split, size - split),
                        )
            raise AssertionError("table CYK incohérente")  # pragma: no cover

        return build(grammar.start, 0, len(word))

    def earley_accepts(self, word: Sequence[str]) -> bool:
        """Le mot est-il engendré ? (algorithme d'Earley, sur la grammaire
        d'origine, sans la convertir.)

        Sert d'oracle indépendant de CYK. Les variables annulables sont
        gérées par la correction d'Aycock et Horspool.

        Complexity
        ----------
        O(n^3), et O(n^2) pour une grammaire non ambiguë.

        References
        ----------
        J. Earley (1970) ; Aycock et Horspool (2002).
        """
        nullable = self.nullable_variables()
        length_n = len(word)
        Item = Tuple[str, Tuple[str, ...], int, int]
        chart: List[Set[Item]] = [set() for _ in range(length_n + 1)]
        for rhs in self.rules(self.start):
            chart[0].add((self.start, rhs, 0, 0))
        for k in range(length_n + 1):
            agenda = list(chart[k])
            while agenda:
                lhs, rhs, dot, origin = agenda.pop()
                added: List[Item] = []
                if dot < len(rhs):
                    symbol = rhs[dot]
                    if symbol in self.variables:
                        for expansion in self.rules(symbol):
                            added.append((symbol, expansion, 0, k))
                        if symbol in nullable:
                            added.append((lhs, rhs, dot + 1, origin))
                    elif k < length_n and word[k] == symbol:
                        chart[k + 1].add((lhs, rhs, dot + 1, origin))
                else:
                    for waiting in list(chart[origin]):
                        w_lhs, w_rhs, w_dot, w_origin = waiting
                        if w_dot < len(w_rhs) and w_rhs[w_dot] == lhs:
                            added.append((w_lhs, w_rhs, w_dot + 1, w_origin))
                for item in added:
                    if item not in chart[k]:
                        chart[k].add(item)
                        agenda.append(item)
        return any(
            lhs == self.start and dot == len(rhs) and origin == 0
            for lhs, rhs, dot, origin in chart[length_n]
        )

    # ------------------------------------------------------------------
    # Énumération et conversion
    # ------------------------------------------------------------------

    def enumerate_words(self, max_length: int) -> List[str]:
        """Tous les mots engendrés de longueur au plus `max_length`, triés
        par longueur puis par ordre alphabétique (programmation dynamique
        sur la forme normale de Chomsky). Les terminaux sont concaténés :
        à réserver aux terminaux d'un caractère.

        Complexity
        ----------
        Dépend du nombre de mots engendrés ; potentiellement exponentielle
        en `max_length`.
        """
        grammar = self._normal_form()
        by_length: Dict[int, Dict[str, Set[str]]] = {}
        for size in range(1, max_length + 1):
            level: Dict[str, Set[str]] = {}
            for lhs, rhs in grammar.productions:
                if size == 1 and len(rhs) == 1:
                    level.setdefault(lhs, set()).add(rhs[0])
                elif size >= 2 and len(rhs) == 2:
                    for cut in range(1, size):
                        left = by_length[cut].get(rhs[0], set())
                        right = by_length[size - cut].get(rhs[1], set())
                        for u, v in product(left, right):
                            level.setdefault(lhs, set()).add(u + v)
            by_length[size] = level
        words: Set[str] = set()
        if (grammar.start, ()) in grammar.productions:
            words.add("")
        for level in by_length.values():
            words |= level.get(grammar.start, set())
        return sorted(words, key=lambda w: (len(w), w))

    def to_pda(self) -> "PDA":
        """Automate à pile (acceptation par pile vide) équivalent."""
        from .pda import cfg_to_pda

        return cfg_to_pda(self)
