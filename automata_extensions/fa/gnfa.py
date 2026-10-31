"""ExtendedGNFA : GNFA avec élimination d'états explicite et traçable.

Un GNFA n'a pas la structure d'un DFA/NFA (ses étiquettes sont des
expressions régulières entre deux états, et il n'a qu'un état final) :
il n'hérite donc pas d'ExtendedFA mais étend directement le GNFA natif.
"""

from typing import Any, Dict, List, Optional, Sequence

from automata.fa.gnfa import GNFA


class ExtendedGNFA(GNFA):
    """GNFA étendu : l'élimination d'états est pilotable pas à pas.

    Convention de automata-lib : une étiquette `None` signifie
    « pas de transition », `""` signifie epsilon.
    """

    def eliminable_states(self) -> List[Any]:
        """États éliminables : tous sauf l'initial et le final (ajoutés
        par la construction depuis un DFA/NFA), triés par str.

        Returns
        -------
        list

        Complexity
        ----------
        O(|Q| log |Q|).
        """
        special = {self.initial_state, self.final_state}
        return sorted(set(self.states) - special, key=str)

    def _bypass_label(
        self,
        r1: str,
        r2: Optional[str],
        r3: str,
        r4: Optional[str],
    ) -> str:
        """Étiquette de p -> q après élimination de r :
        r4 | r1 r2* r3, avec r1 = p->r, r2 = r->r, r3 = r->q,
        r4 = p->q (None si absente)."""
        if self._isbracket_req(r1):
            r1 = f"({r1})"
        if r2 is None or r2 == "":
            loop = ""
        elif len(r2) == 1:
            loop = f"{r2}*"
        else:
            loop = f"({r2})*"
        if self._isbracket_req(r3):
            r3 = f"({r3})"
        if r4 is None:
            alt = ""
        elif self._isbracket_req(r4):
            alt = f"|({r4})"
        elif r4 == "":
            alt = "?"
        else:
            alt = f"|{r4}"
        path = f"{r1}{loop}{r3}"
        if alt == "?":
            if path == "":
                return ""  # epsilon | epsilon = epsilon
            if len(path) > 1:
                return f"({path}){alt}"
        return f"{path}{alt}"

    def eliminate_state(self, state: Any) -> "ExtendedGNFA":
        """Élimine un état et renvoie un NOUVEAU GNFA équivalent.

        Pour chaque paire (p, q) de survivants, l'étiquette devient
        r4 | r1 r2* r3 où r1 = p->état, r2 = état->état,
        r3 = état->q et r4 = p->q.

        Parameters
        ----------
        state : l'état à éliminer (ni l'initial ni le final).

        Returns
        -------
        ExtendedGNFA

        Complexity
        ----------
        O(|Q|^2) opérations sur des expressions régulières.
        """
        if state not in self.eliminable_states():
            raise ValueError(f"état non éliminable : {state!r}")
        remaining = set(self.states) - {state}
        old = self.transitions
        new: Dict[Any, Dict[Any, Optional[str]]] = {}
        for p in remaining - {self.final_state}:
            new[p] = {
                q: label for q, label in old.get(p, {}).items() if q != state
            }
        loop = old.get(state, {}).get(state)
        for p in remaining - {self.final_state}:
            for q in remaining - {self.initial_state}:
                r1 = old.get(p, {}).get(state)
                r3 = old.get(state, {}).get(q)
                if r1 is None or r3 is None:
                    continue
                r4 = old.get(p, {}).get(q)
                new[p][q] = self._bypass_label(r1, loop, r3, r4)
        return ExtendedGNFA(
            states=remaining,
            input_symbols=set(self.input_symbols),
            transitions=new,
            initial_state=self.initial_state,
            final_state=self.final_state,
        )

    def elimination_steps(
        self, order: Optional[Sequence[Any]] = None
    ) -> List["ExtendedGNFA"]:
        """Renvoie tous les GNFA intermédiaires : le GNFA de départ, puis
        un GNFA après chaque élimination (le dernier n'a plus que
        l'état initial et l'état final).

        Parameters
        ----------
        order : séquence d'états, une permutation de eliminable_states().
            Par défaut : l'ordre trié par str.

        Returns
        -------
        list of ExtendedGNFA
            len(order) + 1 éléments.

        Complexity
        ----------
        O(|Q|^3) opérations sur des expressions régulières.
        """
        states = self.eliminable_states()
        chosen = list(states if order is None else order)
        if sorted(chosen, key=str) != states:
            raise ValueError(
                "order doit être une permutation de eliminable_states()"
            )
        current: ExtendedGNFA = self
        steps = [current]
        for state in chosen:
            current = current.eliminate_state(state)
            steps.append(current)
        return steps

    def to_regex_with_order(
        self, order: Optional[Sequence[Any]] = None
    ) -> Optional[str]:
        """Expression régulière obtenue en éliminant les états dans
        l'ordre donné (le langage est le même quel que soit l'ordre, mais
        pas l'écriture ni sa taille).

        Returns
        -------
        str or None
            None si le langage est vide.

        Complexity
        ----------
        O(|Q|^3) opérations sur des expressions régulières.
        """
        last = self.elimination_steps(order)[-1]
        row = last.transitions.get(last.initial_state, {})
        return row.get(last.final_state)
