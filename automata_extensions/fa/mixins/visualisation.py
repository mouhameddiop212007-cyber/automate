"""Export DOT/SVG/PDF/TikZ des automates."""

from typing import NoReturn, Optional

from ._host import FAHost


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

    def export_tikz(self, filename: Optional[str] = None) -> NoReturn:
        """Export TikZ (non supporté directement).

        Graphviz ne produit pas nativement de code TikZ/PGF ; cela
        nécessiterait l'outil externe dot2tex, absent de nos dépendances.
        Documenté comme limitation assumée plutôt qu'implémenté
        incorrectement.
        """
        raise NotImplementedError(
            "L'export TikZ nécessite l'outil externe dot2tex (non installé "
            "dans ce projet). Utiliser export_dot()/export_svg()/export_pdf() "
            "en attendant, ou ajouter dot2tex comme dépendance optionnelle."
        )
