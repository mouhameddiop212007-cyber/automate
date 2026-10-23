"""Arbre de syntaxe abstraite pour les expressions régulières, et calcul
des dérivées de Brzozowski.

Grammaire supportée : symboles alphanumériques (un caractère chacun),
concaténation (juxtaposition), union (|), étoile de Kleene (*),
parenthésage. Pas de classes de caractères ni d'échappement.
"""


class RegexNode:
    """Classe de base des nœuds de l'AST."""

    pass


class Empty(RegexNode):
    """Langage vide (∅) : ne reconnaît rien, pas même le mot vide."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __eq__(self, other):
        return isinstance(other, Empty)

    def __hash__(self):
        return hash("EMPTY")

    def __repr__(self):
        return "∅"


class Epsilon(RegexNode):
    """Mot vide (ε) : reconnaît uniquement la chaîne vide."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __eq__(self, other):
        return isinstance(other, Epsilon)

    def __hash__(self):
        return hash("EPSILON")

    def __repr__(self):
        return "ε"


class Symbol(RegexNode):
    """Un symbole unique de l'alphabet."""

    def __init__(self, char):
        self.char = char

    def __eq__(self, other):
        return isinstance(other, Symbol) and other.char == self.char

    def __hash__(self):
        return hash(("SYMBOL", self.char))

    def __repr__(self):
        return self.char


class Union(RegexNode):
    """Union de plusieurs sous-expressions (représentée à plat, comme un
    ensemble, pour que r|r et r soient structurellement identiques)."""

    def __init__(self, parts):
        self.parts = frozenset(parts)

    def __eq__(self, other):
        return isinstance(other, Union) and other.parts == self.parts

    def __hash__(self):
        return hash(("UNION", self.parts))

    def __repr__(self):
        return "(" + "|".join(sorted(repr(p) for p in self.parts)) + ")"


class Concat(RegexNode):
    """Concaténation de sous-expressions, représentée à plat (tuple)."""

    def __init__(self, parts):
        self.parts = tuple(parts)

    def __eq__(self, other):
        return isinstance(other, Concat) and other.parts == self.parts

    def __hash__(self):
        return hash(("CONCAT", self.parts))

    def __repr__(self):
        return "".join(repr(p) for p in self.parts)


class Star(RegexNode):
    """Étoile de Kleene d'une sous-expression."""

    def __init__(self, inner):
        self.inner = inner

    def __eq__(self, other):
        return isinstance(other, Star) and other.inner == self.inner

    def __hash__(self):
        return hash(("STAR", self.inner))

    def __repr__(self):
        inner_repr = repr(self.inner)
        if isinstance(self.inner, Symbol):
            return f"{inner_repr}*"
        return f"({inner_repr})*"


# --- Constructeurs "intelligents" : simplifient au moment de la
# construction, pour que des expressions équivalentes produisent le même
# nœud (essentiel pour que brzozowski_automaton termine avec peu d'états).


def mk_union(nodes):
    flat = []
    for n in nodes:
        if isinstance(n, Union):
            flat.extend(n.parts)
        elif not isinstance(n, Empty):
            flat.append(n)
    flat = set(flat)
    if not flat:
        return Empty()
    if len(flat) == 1:
        return next(iter(flat))
    return Union(flat)


def mk_concat(nodes):
    flat = []
    for n in nodes:
        if isinstance(n, Concat):
            flat.extend(n.parts)
        elif isinstance(n, Epsilon):
            continue  # neutre pour la concaténation
        else:
            flat.append(n)
    if any(isinstance(n, Empty) for n in flat):
        return Empty()
    if not flat:
        return Epsilon()
    if len(flat) == 1:
        return flat[0]
    return Concat(flat)


def mk_star(node):
    if isinstance(node, (Empty, Epsilon)):
        return Epsilon()
    if isinstance(node, Star):
        return node  # (r*)* = r*
    return Star(node)


# --- Analyse syntaxique ---


def parse_regex(text):
    """Analyse une expression régulière en AST.

    Grammaire (priorité croissante) : union (|) < concaténation < étoile (*).
    """
    pos = [0]

    def peek():
        return text[pos[0]] if pos[0] < len(text) else None

    def advance():
        c = text[pos[0]]
        pos[0] += 1
        return c

    def parse_union():
        parts = [parse_concat()]
        while peek() == "|":
            advance()
            parts.append(parse_concat())
        return mk_union(parts) if len(parts) > 1 else parts[0]

    def parse_concat():
        parts = []
        while peek() is not None and peek() not in "|)":
            parts.append(parse_star())
        return mk_concat(parts)

    def parse_star():
        atom = parse_atom()
        while peek() == "*":
            advance()
            atom = mk_star(atom)
        return atom

    def parse_atom():
        c = peek()
        if c == "(":
            advance()
            node = parse_union()
            if peek() != ")":
                raise ValueError(
                    f"parenthèse fermante manquante dans {text!r}"
                )
            advance()
            return node
        if c is not None and c.isalnum():
            advance()
            return Symbol(c)
        raise ValueError(f"caractère inattendu {c!r} dans {text!r}")

    result = parse_union()
    if pos[0] != len(text):
        raise ValueError(f"expression régulière invalide : {text!r}")
    return result


def to_string(node):
    return repr(node)


def is_nullable(node):
    """Teste si le mot vide appartient au langage dénoté par `node`."""
    if isinstance(node, Epsilon):
        return True
    if isinstance(node, (Empty, Symbol)):
        return False
    if isinstance(node, Union):
        return any(is_nullable(p) for p in node.parts)
    if isinstance(node, Concat):
        return all(is_nullable(p) for p in node.parts)
    if isinstance(node, Star):
        return True
    raise TypeError(f"nœud inconnu : {node!r}")


def derivative(node, symbol):
    """Calcule la dérivée de Brzozowski de `node` par rapport à `symbol`.

    D_a(L) = {w : aw ∈ L} — le quotient à gauche du langage par le
    symbole `a`, exprimé directement au niveau de la structure de
    l'expression régulière (calcul récursif).
    """
    if isinstance(node, (Empty, Epsilon)):
        return Empty()
    if isinstance(node, Symbol):
        return Epsilon() if node.char == symbol else Empty()
    if isinstance(node, Union):
        return mk_union(derivative(p, symbol) for p in node.parts)
    if isinstance(node, Concat):
        head, *rest = node.parts
        rest_node = mk_concat(rest)
        d_head = mk_concat([derivative(head, symbol), rest_node])
        if is_nullable(head):
            return mk_union([d_head, derivative(rest_node, symbol)])
        return d_head
    if isinstance(node, Star):
        return mk_concat([derivative(node.inner, symbol), node])
    raise TypeError(f"nœud inconnu : {node!r}")


def arden_lemma(coef_regex, const_regex):
    """Résout une équation rationnelle unique X = coef_regex . X + const_regex
    (avec coef_regex ne contenant pas le mot vide), via le lemme d'Arden :
    la solution est X = coef_regex* . const_regex.

    Parameters
    ----------
    coef_regex : str
    const_regex : str

    Returns
    -------
    str
        L'expression régulière solution.
    """
    coef_node = parse_regex(coef_regex) if coef_regex else Empty()
    const_node = parse_regex(const_regex) if const_regex else Empty()
    result = mk_concat([mk_star(coef_node), const_node])
    return to_string(result)


def solve_equation_system(equations, start_variable):
    """Résout un système d'équations rationnelles par élimination et
    substitution successive (généralisation d'arden_lemma à plusieurs
    variables), puis lemme d'Arden sur l'équation finale auto-référente.

    Parameters
    ----------
    equations : dict
        variable -> (coef, const) où coef est un dict
        {autre_variable: expression_regex} et const une expression_regex
        (chaîne). Représente : variable = union_j(coef[j] . j) + const.
    start_variable : la variable dont on veut la solution.

    Returns
    -------
    str
        L'expression régulière solution pour start_variable.

    Complexity
    ----------
    O(n^3) où n est le nombre de variables.
    """
    variables = list(equations.keys())
    coef = {}
    const = {}
    for var in variables:
        raw_coef, raw_const = equations[var]
        coef[var] = {
            other: parse_regex(expr) for other, expr in raw_coef.items()
        }
        # None = pas de terme constant (état non-acceptant, langage ∅).
        # '' = mot vide accepté (état acceptant via ε) : parse_regex('')
        # renvoie justement Epsilon() par construction de la grammaire.
        const[var] = (
            parse_regex(raw_const) if raw_const is not None else Empty()
        )

    remaining = set(variables)
    to_eliminate = [v for v in variables if v != start_variable]

    for k in to_eliminate:
        self_coef = coef[k].pop(k, Empty())
        starred = mk_star(self_coef)
        new_terms = {j: mk_concat([starred, c]) for j, c in coef[k].items()}
        new_const = mk_concat([starred, const[k]])

        for i in remaining:
            if i == k:
                continue
            coef_ik = coef[i].pop(k, None)
            if coef_ik is None:
                continue
            for j, term in new_terms.items():
                add = mk_concat([coef_ik, term])
                coef[i][j] = mk_union([coef[i].get(j, Empty()), add])
            const[i] = mk_union([const[i], mk_concat([coef_ik, new_const])])

        remaining.discard(k)

    self_loop = coef[start_variable].pop(start_variable, Empty())
    result = mk_concat([mk_star(self_loop), const[start_variable]])
    return to_string(result)
