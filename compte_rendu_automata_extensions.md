# Compte rendu — Extension de la bibliothèque automata-lib

Projet L2 Informatique, Université Grenoble Alpes — Mouhamed Diop.
Document autonome (§6 du sujet) : il permet de reprendre le projet, dans un nouveau chat ou par une autre personne, sans perte de contexte.

> Source des chiffres : toutes les mesures ci-dessous (tests, couverture, ruff, mypy) proviennent de sorties de terminal exécutées sur la machine de l'étudiant (Mac, Python 3.12, automata-lib 9.2.0), pas d'estimations.

---

## 1. Contexte du projet

- **Sujet** : « Extension de la bibliothèque automata-lib — Langages, Automates, Grammaires et Extensions Python » (projet pédagogique, durée trois mois).
- **Objectif** : fournir un paquet Python `automata_extensions` qui **étend** automata-lib (version figée **9.2.0**) avec 62 algorithmes sur les automates finis, répartis en 3 niveaux, **sans jamais modifier automata-lib**.
- **Exigences du sujet (§4)** : héritage + mixins, immuabilité (chaque méthode renvoie un nouvel automate), docstrings (Returns / Complexity / References), tests `pytest`, packaging `pip install -e .`, documentation (README, exemples, complexité), PEP8, `typing` / `FrozenSet` (§4.2).
- **Environnement** : macOS, venv `automate-env` dans `~/Documents/automate`, Graphviz / pygraphviz installés via Homebrew.
- **Publication** : dépôt GitHub (privé), historique nettoyé, intégration continue, badge de statut dans le README.
- **Objectif personnel** : se démarquer par des extensions difficiles (property-based testing, Hopcroft, differential testing).

## 2. État actuel (mesuré)

| Critère | Résultat |
|---|---|
| Algorithmes du cahier des charges | **62 / 62** (niveau 1 : 41, niveau 2 : 13, niveau 3 : 8) |
| Extensions hors cahier des charges | `minimize_hopcroft`, tests par propriétés (`hypothesis`), dérivées partielles d'Antimirov, `ExtendedGNFA` (élimination d'états pas à pas), export TikZ natif, L\* d'Angluin, grammaires hors-contexte (CNF, CYK, Earley), automates à pile, automates de Büchi |
| Tests | **270 passent** (247 unitaires + 23 propriétés `hypothesis` : 16 à 200 exemples, 5 à 100 et 2 à 60) |
| Couverture (`pytest-cov`) | **98 %** (1952 instructions, 31 non couvertes) |
| PEP8 (`ruff`, règles E, W, F, 79 colonnes, `ruff format`) | **0 erreur** |
| Typage (`mypy`, `disallow_untyped_defs`) | **Success** sur 21 fichiers |
| Documentation | `README.md` (146 lignes) + docstrings avec complexité |
| Packaging | `pyproject.toml` (setuptools), `pip install -e .` |
| Versionnement | git, un commit par étape ; dépôt GitHub privé `mouhameddiop212007-cyber/automate` |
| Intégration continue | **GitHub Actions verte** (Ubuntu, Python 3.10, 3.11, 3.12 et 3.13 en matrice) : `ruff check`, `ruff format --check`, `mypy`, `pytest --cov` |
| Reproductibilité | clone + venv neuf + `pip install -e ".[dev]"` : **146 passed, 3 skipped** ; avec `.[dev,visual]` : 149 passed |

Couverture par fichier : `grammar.py`, `visualisation.py`, `_host.py`, `dfa.py`, `nfa.py`, `gnfa.py`, `learning.py` à 100 % ; `analyse.py` 99 % ; `conversions.py` 99 % ; `grammaire.py` 97 % ; `operations.py` 97 % ; `parse_tree.py` 97 % ; `base.py` 96 % ; `regex_ast.py` 94 %. Nouveaux fichiers : `cfg.py` 99 %, `pda.py` 100 %, `buchi.py` 100 %.

## 3. Architecture actuelle

```
automata_extensions/
├── regex_ast.py            # AST de regex, dérivées, lemme d'Arden, systèmes d'équations
├── learning.py             # L* d'Angluin (DFATeacher, PredicateTeacher)
├── cfg.py                  # ContextFreeGrammar : CNF, CYK, Earley
├── pda.py                  # PDA, cfg_to_pda
├── buchi.py                # BuchiAutomaton (lassos, Choueka)
├── fa/
│   ├── base.py             # ExtendedFA (5 mixins) + _successors + _wrap_native_result
│   ├── dfa.py              # ExtendedDFA(ExtendedFA, DFA)
│   ├── nfa.py              # ExtendedNFA(ExtendedFA, NFA)
│   └── mixins/
│       ├── _host.py        # FAHost : déclarations de typage partagées
│       ├── analyse.py      # parcours, accessibilité, SCC, cycles, trace
│       ├── operations.py   # relations et opérations sur les langages, minimisation
│       ├── conversions.py  # epsilon, déterminisation, regex <-> automates
│       ├── grammaire.py    # grammaires, dérivations, résiduels, morphismes
│       └── visualisation.py# export DOT / SVG / PDF
├── grammar/
│   ├── grammar.py          # Grammar, RegularGrammar
│   └── parse_tree.py       # Leaf, Node (chaîne de dérivation)
tests/  conftest.py, strategies.py, test_analyse / conversions / grammar /
        operations / regex / visualisation / properties / base
```

Principes :

- `ExtendedDFA(ExtendedFA, DFA)` et `ExtendedNFA(ExtendedFA, NFA)` : héritage multiple, les mixins sont fournis par `ExtendedFA`.
- `_successors(state, symbol)` uniformise DFA (une cible) et NFA (un ensemble) : les algorithmes ne font jamais la distinction.
- `_wrap_native_result(automaton)` reconstruit un `Extended*` à partir d'un résultat natif, pour que les wrappers restent chaînables (`dfa.union(x).trim().minimize()`).
- L'epsilon est le symbole `''`, absent de `input_symbols` : on itère donc sur `self.transitions.get(state, {})` et non sur l'alphabet.

### Extensions récentes

- **`partial_derivatives` / `antimirov_automaton`** (`regex_ast.py`, `mixins/conversions.py`) : la dérivée de Brzozowski est une expression, celle d'Antimirov un *ensemble* d'expressions ; chaque élément devient un état d'un NFA sans epsilon.
- **`ExtendedGNFA`** (`fa/gnfa.py`) : étend directement le `GNFA` natif. Méthodes : `eliminable_states`, `eliminate_state` (renvoie un nouveau GNFA), `elimination_steps`, `to_regex_with_order` ; `to_gnfa()` sur DFA/NFA.
- **`export_tikz`** (`mixins/visualisation.py`) : code TikZ (bibliothèque `automata`) produit nativement, sans `dot2tex` : états placés sur une grille dans l'ordre d'un parcours en largeur, étiquettes parallèles fusionnées, epsilon en `$\varepsilon$`, caractères spéciaux de LaTeX échappés, option `standalone=True` pour un document compilable.
- **`angluin_lstar`** (`learning.py`) : apprend le DFA minimal d'un langage régulier par questions (variante de Maler et Pnueli). Enseignants : `DFATeacher` (équivalence exacte, contre-exemple le plus court) et `PredicateTeacher` (fonction Python, équivalence approchée jusqu'à `max_length`). Mesures :
  - DFA à 4 états « nombre pair de a » : 2 états appris, 5 questions d'appartenance, 1 d'équivalence ;
  - « nombre de a multiple de 3 » (fonction Python) : 3 états, 19 / 2, regex apprise `((ab*ab*a|b))*` ;
  - « la 3e lettre avant la fin est un a » : 8 états (2³), 44 / 2, correct sur les 2047 mots de longueur ≤ 10.
- **`ContextFreeGrammar`** (`cfg.py`) : `from_text("S -> a S b | ε")`, `to_cnf()`, `cyk`, `cyk_table`, `cyk_parse` (arbre), `earley_accepts`, `enumerate_words`, `to_pda()`. Mesures : `S -> a S b | ε` (2 productions) donne 7 productions en forme normale ; le langage de Dyck 9 ; une grammaire d'expressions arithmétiques (6 règles, avec règles unitaires) 20 ; l'arbre de `x+x*x` a pour feuilles `x`, `+`, `x`, `*`, `x`.
- **`PDA`** (`pda.py`) : `find_run` renvoie un calcul acceptant (plus court, par parcours en largeur) ; `cfg_to_pda` donne un PDA à un état ; exemples écrits à la main : a^n b^n (pile vide), palindromes pairs (état final, non déterministe). Le calcul de `aabb` par le PDA de `S -> a S b | ε` compte 12 configurations.
- **`BuchiAutomaton`** (`buchi.py`) : `accepts_lasso`, `find_accepted_lasso`, `is_empty`, `intersection`, `union`, `from_dfa`. « Une infinité de a » a pour témoin `(['a'], ['a'])` ; « un nombre fini de a » (non déterministe) `(['a'], ['b'])` ; l'intersection « infiniment de a » et « infiniment de b » compte 5 états et a pour témoin `(['a', 'b'], ['a', 'b'])` ; l'intersection avec « un nombre fini de a » est vide.

Mesures (nombre d'états, sortie de terminal) :

| Regex | Brzozowski (DFA) | Antimirov (NFA) | Thompson (`NFA.from_regex`) |
|---|---|---|---|
| `a*b` | 3 | 2 | 5 |
| `(a\|b)*abb` | 4 | 4 | 12 |
| `(ab\|a)*` | 3 | 2 | 8 |
| `(a\|b)*a(a\|b)(a\|b)` | 8 | 4 | 18 |
| `ab*a\|b` | 4 | 3 | 10 |

Le quatrième cas est l'exemple classique d'explosion exponentielle du DFA (2³ états) face à un NFA de 4 états.

## 4. Historique des décisions

1. **Module externe, jamais de modification d'automata-lib** (version figée 9.2.0) : conforme au §4.2.
2. **Wrapper plutôt que réimplémenter** quand automata-lib offre déjà la méthode (vérifié par `hasattr`, jamais supposé) : `complement`, `union`, `intersection`, `difference`, `concatenate`, `kleene_star`, `reverse` (NFA), `regex_to_nfa` (`NFA.from_regex`), `to_regex_state_elimination` (`GNFA`).
3. **Réimplémentation volontaire** là où le sujet demande la construction classique : `minimize` (classes de Myhill-Nerode), `brzozowski_*`, `to_regex_arden`.
4. **Renommage en cas de collision de sens** avec automata-lib :
   - `predecessors` → `predecessor_states` (le natif manipule des mots, pas des états) ;
   - `left_quotient` / `right_quotient` → `left_quotient_word` / `right_quotient_word` (les natifs prennent un automate en argument).
5. **Document PDF non fiable écarté** : un PDF fourni (`automata_documentation_v1.pdf`) contredisait le sujet officiel et présentait des signes de fabrication. Seule la partie vérifiée par introspection dans le venv a été retenue.
6. **Typage des mixins par `FAHost`** (voir §6).
7. **Extra optionnel `visual`** (`pygraphviz`, `coloraide`) : ces paquets exigent Graphviz sur la machine ; ils sont donc déclarés comme extra (`pip install -e ".[visual]"`) et les 3 tests de visualisation correspondants sont ignorés (`skipif`) quand ils sont absents, au lieu d'échouer.
8. **Intégration continue** : une machine vierge à chaque push, pour détecter ce qui ne marchait que sur le poste de l'étudiant.
9. **Méthode de travail** : un algorithme, ses tests, un commit ; scripts de remplacement qui comptent les occurrences et refusent de modifier en cas d'ambiguïté (voir §10).
10. **`ExtendedGNFA` n'hérite pas d'`ExtendedFA`** : un GNFA a des transitions p → q étiquetées par des regex et un seul `final_state`, alors que les mixins supposent la structure DFA/NFA (`transitions[état][symbole]`, `final_states`). Il étend donc directement le `GNFA` natif, dont `from_dfa` / `from_nfa` renvoient `cls(...)` et donnent donc un `ExtendedGNFA`.
11. **Ordre d'élimination visible** : `to_regex` natif choisit seul l'état à éliminer. `to_regex_with_order` rend ce choix explicite : pour « nombre pair de a », l'ordre `i, p` donne `(ab*a|b)*` (identique au natif) et l'ordre `p, i` donne `b*a(ab*a|b)*ab*|b*`, même langage mais écriture plus lourde.
12. **Export TikZ natif plutôt que `dot2tex`** : `dot2tex` est peu maintenu, exige Graphviz et LaTeX, et rendrait l'export intestable en CI. Un export natif est déterministe et testable ligne par ligne. **Leçon** : les premiers tests comparaient des chaînes et passaient, alors que le code produit ne compilait pas (`>=stealth'` est une syntaxe de l'ancien PGF, rejetée par PGF 3.1.10 : `Unknown arrow tip kind`). Corrigé en `>=stealth`, et ajout d'un test qui compile réellement le document avec `pdflatex` (ignoré s'il est absent).
13. **L\* : variante de Maler et Pnueli** : tous les suffixes du contre-exemple deviennent des colonnes de la table d'observation, ce qui rend inutile le test de cohérence de la version d'origine (les lignes des mots d'accès restent distinctes par construction). Un garde-fou `ValueError` évite la boucle infinie face à un enseignant incohérent. Deux propriétés `hypothesis` vérifient sur 100 DFA aléatoires chacune que le DFA appris a le langage de la cible et autant d'états que `minify()`, et qu'il y a au plus n questions d'équivalence.
14. **`cfg.py`, `pda.py`, `buchi.py` : modules indépendants** des mixins (ni `ExtendedFA` ni `automata-lib` : ce ne sont pas des automates finis). La forme normale de Chomsky suit l'ordre START, TERM, BIN, DEL, UNIT puis suppression des variables inutiles ; les noms frais (`S0`, `T_a`, `S_1`) évitent toute collision (apostrophes). CYK travaille sur la forme normale ; **Earley** travaille sur la grammaire d'origine (avec la correction d'Aycock et Horspool pour les variables annulables) : c'est un oracle indépendant. Les propriétés `hypothesis` comparent CYK, Earley et le PDA sur des grammaires aléatoires.
15. **PDA : recherche bornée en hauteur de pile** (par défaut `len(mot) + 2`). Sans borne, une epsilon-transition qui empile boucle indéfiniment. Pour un PDA issu d'une grammaire en forme normale, la borne ne perd aucun mot (chaque symbole de la pile dérive au moins une lettre du reste du mot) ; pour un PDA quelconque c'est une recherche bornée, documentée dans `find_run`.
16. **Büchi : mots ultimement périodiques et construction de Choueka.** Le langage est testé sur des lassos `prefix . loop^ω` : `accepts_lasso` cherche un arc marqué sur un cycle du graphe des lectures de `loop`. L'intersection utilise un produit à deux drapeaux (la bascule se fait sur l'état source) ; l'union ajoute un état initial neuf.

## 5. Bugs trouvés et corrigés (leçons)

1. **`_wrap_native_result` basé sur `type(self)`** : `concatenate` et `kleene_star` natifs renvoient toujours un NFA, même depuis un DFA. Correction : choisir la classe d'après le type **réel** du résultat natif (`isinstance`). Leçon : tester systématiquement DFA et NFA.
2. **`trim()` sur langage vide** (trouvé par `hypothesis`, aucun des 112 tests écrits à la main ne le détectait) : `useful_states()` vide, donc `induced_subautomaton(set())` impossible. Correction : cas particulier renvoyant un automate à 1 état `__empty_language__` non final. Précision mathématique : un automate de langage vide n'est jamais « trim » au sens strict ; c'est un cas limite assumé.
3. **`distinguishable_states` sur automate partiel** (trouvé par `hypothesis` grâce à Hopcroft comme oracle, c'est du *differential testing*) : une transition manquante était ignorée alors qu'elle équivaut à un saut vers un puits implicite non final. Des états distinguables étaient donc fusionnés par `minimize()` et le langage devenait faux. Correction : sentinelle `SINK` pendant le calcul, retirée du résultat.
4. **Construction finale de Hopcroft** avec DFA partiel : ne remplir les transitions que si les successeurs existent, `allow_partial=True`.
5. **Lemme d'Arden** : distinction `const=None` (langage vide) / `const=''` (mot vide accepté).
6. **Tests faussement verts** : `is_isomorphic` pour alphabets différents passait parce que le nombre d'états était testé avant l'alphabet (corrigé avec deux DFA à 3 états) ; plusieurs tests collés avec nano n'avaient jamais été ajoutés (vérification par `grep -n "^def test_"`).
7. **Code mort** détecté par la couverture et supprimé (garde jamais fausse dans `is_language_infinite`, garde jamais vraie dans `determinize`).
8. **Violation du principe de substitution (Liskov), détectée par mypy** : les wrappers `complement`, `union`, `intersection`, `difference` n'acceptaient pas `retain_names` / `minify` de la méthode native `DFA`. `ExtendedDFA(...).union(x, minify=False)` plantait alors que `DFA.union` l'accepte. Correction : `**kwargs` transmis à la méthode native, vérifié par exécution (résultat `ExtendedDFA` dans les trois cas). C'est un vrai bug de comportement, pas qu'une question de typage.

### Leçons de la publication sur GitHub

- **Historique git pollué** : le venv, les caches et des PNG avaient été versionnés avant l'ajout du `.gitignore` (13 068 fichiers, 156 Mo). Corrigé par `git rm --cached`, `git filter-branch`, `gc` et push forcé : 38 fichiers suivis, `.git` à 1,7 Mo.
- **Dépendance cachée** : `pip install -e ".[dev]"` dans un venv neuf a révélé que les tests de visualisation exigeaient `pygraphviz` et `coloraide`, jamais déclarés (installés à la main sur le Mac). Corrigé par l'extra `visual` et des `skipif`.
- **Fichier orphelin** : un ancien `test_automate.py` à la racine (import de `matplotlib`) était collecté par pytest sur la CI. Corrigé par `testpaths = ["tests"]`.
- **Format** : `ruff format --check` échouait en CI car le formatage n'avait pas été appliqué avant le push.
- **Flakiness** : profil `hypothesis` avec `deadline=None`, car une machine CI plus lente dépassait la limite de temps par exemple.

## 6. Choix techniques détaillés : typage (§4.2)

- Toutes les fonctions publiques et internes sont annotées ; `mypy` est configuré dans `pyproject.toml` (`disallow_untyped_defs`, `warn_unused_ignores`), donc `mypy` seul donne le même résultat.
- **Problème** : un mixin utilise `self.states`, `self.transitions`, etc., fournis seulement par la classe finale ; mypy ne peut pas les vérifier depuis le mixin isolé.
- **Solution** : classe `FAHost` (`fa/mixins/_host.py`), dont héritent tous les mixins. Elle déclare les attributs (`states`, `input_symbols`, `transitions`, `initial_state`, `final_states`) et, sous `TYPE_CHECKING` uniquement, un `__getattr__` renvoyant `Any` pour les méthodes des autres mixins. **Aucun effet à l'exécution** (simples annotations).
- **Compromis assumé** : l'indirection `__getattr__` rend moins strict le contrôle de ces accès dans les mixins (une faute de frappe sur un nom de méthode interne ne serait pas détectée par mypy ; les tests la détectent).
- **Quatre `# type: ignore[misc]`** ciblés : `super().complement`, `union`, `intersection` (opérations) et `super().reverse` (conversions). Dans un mixin isolé, `super()` pointe vers `FAHost` ; à l'exécution, le MRO de `ExtendedDFA` / `ExtendedNFA` atteint bien `DFA` / `NFA`.
- **Retours** : `"ExtendedFA"` pour les méthodes qui construisent un automate (annotation commune évitant des imports circulaires), `Any` pour les wrappers de méthodes natives, qui doivent rester compatibles avec la signature des classes de automata-lib.
- `typing.FrozenSet` est utilisé là où la structure est immuable (grammaires, sous-ensembles de la déterminisation, AST d'union).

## 7. Les 62 algorithmes (par niveau)

**Niveau 1 — bases (41)** : `dfs`, `bfs`, `predecessor_states`, `accessible_states`, `is_accessible`, `reachable_states_from`, `coaccessible_states`, `is_coaccessible`, `useful_states`, `induced_subautomaton`, `trim`, `is_trim`, `strongly_connected_components` (Tarjan), `has_cycle`, `has_cycle_from`, `is_language_empty`, `is_language_infinite`, `accepts_word`, `execution_trace`, `is_complete`, `complete`, `complement`, `cartesian_product`, `language_subset`, `language_equals`, `is_isomorphic`, `is_prefix_closed`, `prefix_closed_sublanguage`, `distinguishable_states`, `myhill_nerode_partition`, `is_minimal`, `minimize`, `is_deterministic`, `epsilon_closure`, `reverse`, `determinize`, `remove_epsilon_transitions`, `is_universal_language`, `eliminate_epsilon_states_normalized`, `export_dot`, `export_svg` / `export_pdf` / `export_tikz`.

**Niveau 2 — opérations sur les langages et conversions (13)** : `union`, `intersection`, `difference`, `concatenate`, `kleene_star`, `left_quotient_word`, `right_quotient_word`, `regex_to_nfa`, `to_regex_state_elimination`, `brzozowski_derivative`, `brzozowski_automaton`, `to_regex_arden`.

**Niveau 3 — grammaires (8)** : `to_grammar` / `grammar_to_automaton`, `derivation_tree`, `arden_lemma` / `solve_equation_system`, `myhill_nerode_language_classes`, `residual_automaton`, `automaton_morphism`, `syntactic_monoid`.

**Extensions différenciantes** : tests par propriétés avec `hypothesis` (16 propriétés, 200 exemples chacune) et `minimize_hopcroft` (algorithme de Hopcroft, validé par differential testing contre `minimize()` : les deux résultats sont isomorphes et minimaux). **Antimirov** (`partial_derivatives`, `antimirov_automaton` : NFA d'au plus n + 1 états, validé contre la construction de Thompson sur tous les mots jusqu'à la longueur 6) et **`ExtendedGNFA`** (élimination d'états pas à pas, ordre au choix).

## 8. Limites connues (honnêtes)

- `is_isomorphic` est rigoureux pour les DFA ; pour un NFA, la comparaison simple de cardinal de successeurs ne suffirait pas (documenté dans la fonction).
- `cartesian_product` ignore les transitions manquantes ; correct avec le prédicat par défaut (intersection), mais pas pour un prédicat arbitraire sur automates partiels.
- `residual_automaton` : O(|Q|³ · |Σ|), car `language_equals` identifie les résiduels.
- `syntactic_monoid` : taille potentiellement exponentielle en |Q| (limite théorique), à réserver aux petits automates.
- `minimize_hopcroft` : la file est une liste Python, donc ses `remove()` sont en O(n) : simplification pédagogique, la complexité O(|Q| log|Q| |Σ|) annoncée est celle de l'algorithme, pas de cette implémentation.
- Typage : voir §6 (`FAHost`, 4 `type: ignore`, retours `Any` sur les wrappers).
- Lignes non couvertes (31 sur 1952) : branches défensives (`base.py:61`), `__eq__` / `__hash__` de l'AST déjà exercés indirectement, cas limites de `syntactic_monoid`.
- Certains tests d'`automaton_morphism` parcourent des branches différentes selon l'ordre d'itération des ensembles (couverture légèrement non déterministe).
- `ExtendedGNFA` n'hérite pas d'`ExtendedFA` (structure différente) : il n'a pas accès aux algorithmes d'analyse des mixins, seulement à ses propres méthodes.
- `PredicateTeacher` : l'équivalence est approchée (test exhaustif jusqu'à `max_length`) ; un langage dont le DFA minimal est grand peut être mal appris si `max_length` est trop petit. Avec `DFATeacher` elle est exacte.
- `PDA.find_run` : recherche bornée en hauteur de pile ; un résultat négatif sur un PDA quelconque n'exclut pas un calcul à pile plus haute. La conversion PDA -> grammaire n'est pas implémentée.
- `earley_accepts` est une version pédagogique (balayage de la colonne d'origine à chaque complétion), pas en O(n³) strict ; `enumerate_words` concatène les terminaux : à réserver aux terminaux d'un caractère.
- Büchi : pas de complémentation (construction de Safra non implémentée), donc ni inclusion ni équivalence de langages ; l'égalité n'est testée que sur des lassos.

## 9. TODO possibles (par ordre de valeur)

1. Rendre déterministes les tests d'`automaton_morphism` (entrées fixes, ordre trié).
2. Tests ciblés sur les lignes non couvertes les plus simples (`regex_ast.py`, 13 lignes).
3. ~~Intégration continue GitHub Actions~~ : **fait**, voir §2.
4. ~~Antimirov, `ExtendedGNFA`, export TikZ~~ : **faits**, voir §3.
5. Extensions plus ambitieuses : L\* d'Angluin, CYK / forme normale de Chomsky, automates à pile, automates de Büchi (**faits**, voir §3) ; restent : simulateur HTML animé, complémentation de Büchi (Safra), conversion PDA -> grammaire.
6. Avant le rendu : relire le README, ajouter un petit notebook d'exemples (la vérification de `pip install -e .` dans un venv propre est **faite**) ; envisager de passer le dépôt en public pour que le badge CI soit visible de tous ; matrice Python 3.10–3.12 dans la CI.

## 10. Contexte implicite et mémoire de travail

- **Méthode de collaboration** : l'étudiant exécute les commandes et colle les sorties ; rien n'est vérifié par l'assistant hors de ces sorties. Toujours **une commande par collage** (un `rm` a déjà été collé avec une autre commande par erreur).
- **Modifications de fichiers** : les `nano` / `sed` manuels ont causé plusieurs erreurs (indentation à 8 au lieu de 4 espaces, fonctions dupliquées, tests jamais ajoutés). Remplacée depuis par des **scripts Python de remplacement** qui comptent les occurrences attendues et affichent `PROBLEME` en cas d'écart, suivis de `ruff`, `mypy`, `pytest`.
- **macOS** : `sed -i ''` (guillemets obligatoires), `cat -e -t` (pas `cat -A`).
- **Imports relatifs** : compter les niveaux depuis `fa/mixins/` : `..dfa`, `..nfa`, `...regex_ast`, `...grammar.grammar`.
- **Imports locaux dans les fonctions** : servent à éviter les cycles (`fa.base` ↔ `fa.dfa` / `fa.nfa`) ; ne pas les remonter en tête de fichier.

## 11. Guide de reprise

```bash
cd ~/Documents/automate
source automate-env/bin/activate
pip install -e ".[dev,visual]"            # `visual` : pygraphviz + coloraide (Graphviz requis)
pytest -q                                   # attendu : 270 passed (3 tests de visualisation ignorés sans l'extra visual, 1 test de compilation ignoré sans pdflatex)
pytest --cov=automata_extensions --cov-report=term-missing -q   # attendu : 98 %
ruff check automata_extensions tests        # attendu : All checks passed!
ruff format --check automata_extensions tests
mypy                                        # attendu : Success: no issues found in 21 source files
git log --oneline | head
```

Pour reprendre dans un nouveau chat : coller ce document, joindre `pyproject.toml`, et le(s) fichier(s) concerné(s) par la tâche.

## 12. Glossaire

- **Mixin** : classe de méthodes réutilisables, sans état propre, combinée par héritage multiple.
- **MRO** : ordre de résolution des méthodes en héritage multiple (détermine ce que `super()` atteint).
- **Wrapper** : méthode qui délègue à automata-lib puis ré-enveloppe le résultat en `Extended*`.
- **Accessible / coaccessible / utile / émondé (trim)** : état atteignable depuis l'initial / depuis lequel on atteint un final / les deux / automate dont tous les états sont utiles.
- **Myhill-Nerode** : équivalence de comportement entre états (partition) ou entre mots (quotients du langage, un par état du DFA minimal).
- **Dérivée de Brzozowski** : quotient à gauche d'une expression régulière par un symbole.
- **Lemme d'Arden** : solution de X = A·X + B par X = A\*·B (A sans mot vide).
- **Puits implicite** : état non final virtuel vers lequel mène toute transition manquante d'un automate partiel.
- **Differential testing** : comparer deux implémentations indépendantes du même algorithme (ici `minimize` et `minimize_hopcroft`).
- **Property-based testing** : tester une propriété mathématique sur de nombreuses entrées générées aléatoirement (`hypothesis`).
- **Principe de Liskov** : une sous-classe doit accepter tout ce que sa classe parente accepte.
