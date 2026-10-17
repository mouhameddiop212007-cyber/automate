"""Hiérarchie de grammaires formelles.

Seule RegularGrammar (grammaire linéaire à droite) est implémentée pour
l'instant, car c'est la seule utile à la conversion automate <-> grammaire
(#55 du sujet). Les autres classes (ContextFreeGrammar, etc.) sont hors
périmètre de ce projet centré sur les automates finis.
"""


class Grammar:
    """Classe de base abstraite pour toute grammaire formelle.

    Une grammaire est définie par :
    - variables : ensemble des non-terminaux
    - terminals : ensemble des terminaux (l'alphabet)
    - rules : dict non-terminal -> liste de productions (chaque
      production est un tuple de symboles, terminaux et/ou non-terminaux)
    - start_variable : le non-terminal de départ
    """

    def __init__(self, variables, terminals, rules, start_variable):
        self.variables = frozenset(variables)
        self.terminals = frozenset(terminals)
        self.rules = {v: list(prods) for v, prods in rules.items()}
        self.start_variable = start_variable

    def __eq__(self, other):
        return (
            isinstance(other, Grammar)
            and self.variables == other.variables
            and self.terminals == other.terminals
            and self.rules == other.rules
            and self.start_variable == other.start_variable
        )

    def __repr__(self):
        lines = []
        for var in sorted(self.variables, key=str):
            prods = self.rules.get(var, [])
            rhs = " | ".join(
                "".join(str(s) for s in prod) if prod else "ε"
                for prod in prods
            )
            lines.append(f"{var} -> {rhs}")
        return "\n".join(lines)


class RegularGrammar(Grammar):
    """Grammaire linéaire à droite : chaque règle est de la forme
    A -> a B (un terminal suivi d'au plus un non-terminal) ou A -> ε.

    Engendre exactement les langages réguliers (équivalence directe avec
    les automates finis).
    """

    def __init__(self, variables, terminals, rules, start_variable):
        super().__init__(variables, terminals, rules, start_variable)
        self._validate_linear_right()

    def _validate_linear_right(self):
        for var, prods in self.rules.items():
            for prod in prods:
                if len(prod) == 0:
                    continue  # A -> ε, autorisé
                if len(prod) > 2:
                    raise ValueError(
                        f"règle non linéaire à droite : {var} -> {prod!r}"
                    )
                if prod[0] not in self.terminals:
                    raise ValueError(
                        f"le premier symbole doit être un terminal : "
                        f"{var} -> {prod!r}"
                    )
                if len(prod) == 2 and prod[1] not in self.variables:
                    raise ValueError(
                        f"le second symbole doit être un non-terminal : "
                        f"{var} -> {prod!r}"
                    )
