"""Export DOT/SVG/PDF/TikZ des automates."""

from collections import deque
from math import isqrt
from typing import Any, Dict, List, Optional, Tuple

from ._host import FAHost

_TEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _tex_escape(text: str) -> str:
    """Échappe les caractères spéciaux de LaTeX dans `text`."""
    return "".join(_TEX_SPECIAL.get(char, char) for char in text)


class VisualisationMixin(FAHost):
    """Regroupe les méthodes d'export visuel de l'automate."""

    def export_dot(self) -> str:
        """Renvoie le code source DOT (Graphviz) de l'automate, en texte.

        Réutilise show_diagram() natif de automata-lib (nécessite
        pygraphviz), sans dépendre d'un appel externe au binaire Graphviz
        pour cette seule étape.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return str(self.show_diagram())

    def export_svg(self, filename: str) -> str:
        """Exporte l'automate en image SVG via Graphviz (binaire dot requis).

        Parameters
        ----------
        filename : str
            Chemin du fichier de sortie.
        """
        self.show_diagram().draw(filename, format="svg", prog="dot")
        return filename

    def export_pdf(self, filename: str) -> str:
        """Exporte l'automate en PDF via Graphviz (binaire dot requis).

        Parameters
        ----------
        filename : str
            Chemin du fichier de sortie.
        """
        self.show_diagram().draw(filename, format="pdf", prog="dot")
        return filename

    def _tikz_state_order(self) -> List[Any]:
        """États dans l'ordre d'un parcours en largeur depuis l'état
        initial (successeurs triés par str, pour un résultat déterministe),
        puis les états inaccessibles triés par str."""
        order = [self.initial_state]
        seen = {self.initial_state}
        queue = deque(order)
        while queue:
            state = queue.popleft()
            for symbol in sorted(self.transitions.get(state, {}), key=str):
                successors = self._successors(state, symbol)
                for target in sorted(successors, key=str):
                    if target not in seen:
                        seen.add(target)
                        order.append(target)
                        queue.append(target)
        order.extend(sorted(set(self.states) - seen, key=str))
        return order

    def export_tikz(
        self, filename: Optional[str] = None, standalone: bool = False
    ) -> str:
        """Renvoie le code TikZ (bibliothèque `automata`) de l'automate.

        Les états sont placés sur une grille dans l'ordre d'un parcours en
        largeur depuis l'état initial ; les étiquettes parallèles sont
        fusionnées ; epsilon est affiché en $\\varepsilon$ ; les
        caractères spéciaux de LaTeX sont échappés. Aucun outil externe
        n'est requis.

        Parameters
        ----------
        filename : str, optional
            Si donné, le code est aussi écrit dans ce fichier.
        standalone : bool
            Si vrai, produit un document LaTeX complet et compilable
            (classe `standalone`) au lieu du seul environnement
            `tikzpicture`.

        Returns
        -------
        str
            Le code TikZ.

        Complexity
        ----------
        O(|Q| + |E| log |E|)
        """
        order = self._tikz_state_order()
        index = {state: i for i, state in enumerate(order)}
        columns = isqrt(max(len(order) - 1, 0)) + 1
        header = (
            r"\begin{tikzpicture}[->, >=stealth, shorten >=1pt, auto,"
            r" semithick, initial text=]"
        )
        lines = [header]
        for i, state in enumerate(order):
            options = ["state"]
            if state == self.initial_state:
                options.append("initial")
            if state in self.final_states:
                options.append("accepting")
            x = 3 * (i % columns)
            y = -3 * (i // columns)
            label = _tex_escape(str(state))
            lines.append(
                "  \\node[" + ", ".join(options) + f"] (q{i})"
                f" at ({x},{y}) {{" + label + "};"
            )
        labels: Dict[Tuple[int, int], List[str]] = {}
        for state in order:
            for symbol in sorted(self.transitions.get(state, {}), key=str):
                if symbol == "":
                    text = r"$\varepsilon$"
                else:
                    text = _tex_escape(str(symbol))
                for target in self._successors(state, symbol):
                    pair = (index[state], index[target])
                    labels.setdefault(pair, []).append(text)
        for (src, dst), names in sorted(labels.items()):
            style = ""
            if src == dst:
                style = "[loop above]"
            elif (dst, src) in labels:
                style = "[bend left]"
            lines.append(
                f"  \\path (q{src}) edge{style} node {{"
                + ", ".join(names)
                + f"}} (q{dst});"
            )
        lines.append(r"\end{tikzpicture}")
        body = "\n".join(lines) + "\n"
        if standalone:
            code = (
                "\\documentclass[tikz, border=5pt]{standalone}\n"
                "\\usetikzlibrary{automata}\n"
                "\\begin{document}\n" + body + "\\end{document}\n"
            )
        else:
            code = "% Requires \\usetikzlibrary{automata}\n" + body
        if filename is not None:
            with open(filename, "w", encoding="utf-8") as handle:
                handle.write(code)
        return code
