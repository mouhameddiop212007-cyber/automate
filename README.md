# automata_extensions

![CI](https://github.com/mouhameddiop212007-cyber/automate/actions/workflows/ci.yml/badge.svg)

Extension pédagogique de la bibliothèque [`automata-lib`](https://pypi.org/project/automata-lib/) (version **9.2.0**, figée) :
algorithmes classiques de théorie des langages sur les automates finis, les expressions régulières et les grammaires régulières.
`automata-lib` n'est **jamais modifiée** : tout passe par héritage multiple et mixins.

## Installation

```bash
brew install graphviz pkg-config cairo      # macOS : nécessaire pour les exports visuels
python3 -m venv automate-env
source automate-env/bin/activate
pip install -e .
pip install pytest hypothesis pytest-cov    # pour lancer les tests
```

## Utilisation

```python
from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.fa.nfa import ExtendedNFA

dfa = ExtendedDFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2', 'b': '3'},
        '2': {'a': '2', 'b': '3'},
        '3': {'a': '3', 'b': '3'},
    },
    initial_state='1',
    final_states={'2'},
)

dfa.accessible_states()          # états accessibles depuis l'état initial
dfa.trim().states                # {'1', '2'} : '3' n'est pas coaccessible
dfa.complement().accepts_input('a')   # False
dfa.minimize()                   # DFA minimal (méthode classique)
dfa.minimize_hopcroft()          # même résultat, algorithme de Hopcroft

# Les méthodes retournent toujours un NOUVEL automate (immuabilité) : elles se chaînent
dfa.trim().minimize().to_regex_arden()

# Expressions régulières
nfa = ExtendedNFA.regex_to_nfa('a*b', input_symbols={'a', 'b'})
nfa.accepts_input('aab')         # True
ExtendedDFA.brzozowski_derivative('ab', 'a')   # 'b'
```

## Exemples

Le notebook [`visite_guidee.ipynb`](visite_guidee.ipynb) déroule une visite guidée (analyse, opérations, minimisation, regex, NFA epsilon, grammaires, export DOT), avec les sorties.

## Extensions au-delà du cahier des charges

- **Tests par propriétés** (`hypothesis`) : 16 propriétés mathématiques vérifiées sur des automates aléatoires ; elles ont révélé deux vrais bugs (voir le compte rendu).
- **Hopcroft** : `minimize_hopcroft()`, validé contre `minimize()` par differential testing.
- **Antimirov** : un NFA d'au plus n + 1 états, bien plus petit que l'automate de Brzozowski.
- **`ExtendedGNFA`** : élimination d'états pas à pas, avec l'ordre au choix.
- **Export TikZ** natif (sans `dot2tex`) : code `tikzpicture` prêt à coller dans un document LaTeX.
- **L\* d'Angluin** : apprend un DFA minimal en interrogeant un enseignant (un DFA, ou une simple fonction Python).

```python
nfa = ExtendedNFA.antimirov_automaton("(a|b)*a(a|b)(a|b)", {"a", "b"})
len(nfa.states)                          # 4 (contre 8 pour Brzozowski)

g = dfa.to_gnfa()                        # DFA -> GNFA
g.to_regex_with_order(["i", "p"])        # (ab*a|b)*
g.to_regex_with_order(["p", "i"])        # même langage, écriture plus lourde
g.elimination_steps()                    # tous les GNFA intermédiaires

dfa.export_tikz()                        # code TikZ (str)
dfa.export_tikz("automate.tex", standalone=True)   # document LaTeX compilable

from automata_extensions.learning import PredicateTeacher, angluin_lstar
teacher = PredicateTeacher({"a", "b"}, lambda w: w.count("a") % 3 == 0, max_length=7)
angluin_lstar(teacher)                   # DFA à 3 états, appris par 19 + 2 questions
```

## Architecture

```
automata_extensions/
├── fa/
│   ├── base.py            ExtendedFA : assemble les mixins + utilitaires internes
│   ├── dfa.py, nfa.py     ExtendedDFA(ExtendedFA, DFA), ExtendedNFA(ExtendedFA, NFA)
│   └── mixins/
│       ├── analyse.py        parcours, accessibilité, SCC, cycles, simulation
│       ├── operations.py     relations, opérations sur les langages, minimisation
│       ├── conversions.py    epsilon, déterminisation, regex <-> automates
│       ├── grammaire.py      grammaires, dérivations, résiduels, morphismes
│       └── visualisation.py  export DOT / SVG / PDF
├── grammar/               Grammar, RegularGrammar, Node/Leaf (arbres de dérivation)
└── regex_ast.py           AST des regex, dérivées de Brzozowski, lemme d'Arden
tests/                     tests unitaires + property-based (hypothesis)
```

## Principes de conception

- **Immuabilité** : aucune méthode ne modifie `self`, chaque transformation renvoie un nouvel automate.
- **Wrapper plutôt que réimplémenter** : quand `automata-lib` 9.2.0 fournit déjà l'algorithme
  (`complement`, `union`, `intersection`, `difference`, `concatenate`, `kleene_star`, `reverse` sur NFA,
  `NFA.from_regex`, `GNFA.to_regex`), la méthode est un wrapper dont le résultat est ré-enveloppé en `Extended*`
  pour rester chaînable.
- **Pas de collision de noms** : une méthode native de même nom mais de sens différent est contournée par un
  renommage (`predecessor_states` au lieu de `predecessors`, `left_quotient_word` / `right_quotient_word`
  au lieu de `left_quotient` / `right_quotient`). Vérifié par introspection (`hasattr`) avant chaque ajout.
- **Lisibilité avant optimisation** : chaque méthode a une docstring avec complexité (et références si pertinent).

## Tests

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=automata_extensions --cov-report=term-missing -q
```

Les tests combinent des exemples écrits à la main et du **property-based testing** (`hypothesis`) qui vérifie
des invariants (`minimize` idempotent, `complement∘complement = id`, unicité du DFA minimal à isomorphisme près,
accord entre `minimize` et `minimize_hopcroft`, etc.) sur des automates générés aléatoirement.

## Limites connues

- `export_tikz` n'est pas implémenté (il faudrait la dépendance externe `dot2tex`) ; il lève `NotImplementedError`.
- `is_isomorphic` n'est rigoureux que pour des DFA (un seul successeur par symbole).
- `cartesian_product` ignore les transitions manquantes : correct avec le prédicat par défaut (intersection),
  à revoir pour un prédicat personnalisé de type union.
- `trim()` d'un automate au langage vide renvoie un automate à un seul état non coaccessible (un état initial
  est obligatoire) : il n'est donc pas « trim » au sens strict, c'est un cas limite assumé.
- `syntactic_monoid` peut être de taille exponentielle ; `residual_automaton` est en O(|Q|³·|Σ|).
- Dans `minimize_hopcroft`, la file de séparateurs est une liste Python (retraits en O(n)) : simplification
  pédagogique, la borne O(n log n) n'est donc pas atteinte à la lettre.
