"""Arbres (chaînes, pour une grammaire linéaire à droite) de dérivation."""


class Leaf:
    """Un symbole terminal consommé."""

    def __init__(self, symbol):
        self.symbol = symbol

    def __repr__(self):
        return self.symbol


class Node:
    """Une étape de dérivation : le non-terminal courant, le terminal lu
    (None si c'est la dernière étape, A -> ε), et le nœud suivant (None si
    dernière étape).
    """

    def __init__(self, variable, leaf=None, child=None):
        self.variable = variable
        self.leaf = leaf
        self.child = child

    def word(self):
        """Reconstruit le mot dérivé en parcourant la chaîne."""
        if self.leaf is None:
            return ""
        rest = self.child.word() if self.child is not None else ""
        return self.leaf.symbol + rest

    def sequence(self):
        """Affiche la suite classique des étapes de dérivation, ex:
        '1 => a2 => a' (variable de départ, puis chaque forme
        sentencielle successive, jusqu'au mot terminal final)."""
        nodes = []
        node = self
        while node is not None:
            nodes.append(node)
            node = node.child

        steps = [str(nodes[0].variable)]
        prefix = ""
        for i in range(1, len(nodes)):
            prefix += nodes[i - 1].leaf.symbol
            steps.append(prefix + str(nodes[i].variable))
        steps.append(prefix)  # forme finale, après application de la
                               # dernière règle (variable -> ε)
        return " => ".join(steps)
