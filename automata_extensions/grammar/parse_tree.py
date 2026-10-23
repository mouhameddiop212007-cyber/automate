"""Arbres (chaînes, pour une grammaire linéaire à droite) de dérivation."""

from typing import Any, List, Optional


class Leaf:
    """Un symbole terminal consommé."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def __repr__(self) -> str:
        return self.symbol


class Node:
    """Une étape de dérivation : le non-terminal courant, le terminal lu
    (None si c'est la dernière étape, A -> ε), et le nœud suivant (None si
    dernière étape).
    """

    def __init__(
        self,
        variable: Any,
        leaf: Optional[Leaf] = None,
        child: Optional["Node"] = None,
    ) -> None:
        self.variable = variable
        self.leaf = leaf
        self.child = child

    def word(self) -> str:
        """Reconstruit le mot dérivé en parcourant la chaîne."""
        if self.leaf is None:
            return ""
        rest = self.child.word() if self.child is not None else ""
        return self.leaf.symbol + rest

    def sequence(self) -> str:
        """Affiche la suite classique des étapes de dérivation, ex:
        '1 => a2 => a' (variable de départ, puis chaque forme
        sentencielle successive, jusqu'au mot terminal final)."""
        nodes: List[Node] = []
        current: Optional[Node] = self
        while current is not None:
            nodes.append(current)
            current = current.child

        steps = [str(nodes[0].variable)]
        prefix = ""
        for i in range(1, len(nodes)):
            leaf = nodes[i - 1].leaf
            assert leaf is not None, "étape intermédiaire sans terminal lu"
            prefix += leaf.symbol
            steps.append(prefix + str(nodes[i].variable))
        steps.append(prefix)  # forme finale, après application de la
        # dernière règle (variable -> ε)
        return " => ".join(steps)
