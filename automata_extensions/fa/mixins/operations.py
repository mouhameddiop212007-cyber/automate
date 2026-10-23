"""Relations entre automates et opérations ensemblistes sur les langages."""


class OperationsMixin:
    """Relations entre automates et opérations sur les langages."""

    def is_complete(self):
        """Teste si l'automate est complet (DFA uniquement) : chaque état a
        une transition pour chaque symbole de l'alphabet.

        Complexity
        ----------
        O(|Q| . |Σ|)
        """
        for state in self.states:
            for symbol in self.input_symbols:
                if symbol not in self.transitions.get(state, {}):
                    return False
        return True

    def complete(self):
        """Renvoie un nouveau DFA complet, en ajoutant un état puits et les
        transitions manquantes si nécessaire.

        Returns
        -------
        ExtendedDFA
            Un DFA complet équivalent (même langage).

        Complexity
        ----------
        O(|Q| . |Σ|)
        """
        if self.is_complete():
            return type(self)(
                states=set(self.states),
                input_symbols=set(self.input_symbols),
                transitions={
                    state: dict(paths)
                    for state, paths in self.transitions.items()
                },
                initial_state=self.initial_state,
                final_states=set(self.final_states),
            )

        sink = "__sink__"
        while sink in self.states:
            sink += "_"

        new_states = set(self.states) | {sink}
        new_transitions = {
            state: dict(self.transitions.get(state, {}))
            for state in new_states
        }
        for state in new_states:
            for symbol in self.input_symbols:
                if symbol not in new_transitions[state]:
                    new_transitions[state][symbol] = sink

        return type(self)(
            states=new_states,
            input_symbols=set(self.input_symbols),
            transitions=new_transitions,
            initial_state=self.initial_state,
            final_states=set(self.final_states),
        )

    def complement(self, **kwargs):
        """Renvoie le complémentaire du langage reconnu.

        Wrapper autour de complement() natif de automata-lib (déjà présent
        dans les versions récentes de la bibliothèque, contrairement à ce
        qu'indiquait initialement le sujet — vérifié par introspection).
        Le résultat natif est ré-enveloppé en ExtendedDFA pour rester
        chaînable avec nos propres algorithmes.

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib.
        """
        native_result = super().complement(**kwargs)
        return self._wrap_native_result(native_result)

    def cartesian_product(self, other, final_predicate=None):
        """Construit le produit synchronisé de deux automates (construction
        paresseuse : seuls les couples d'états accessibles sont visités).

        Aucune méthode équivalente n'existe nativement dans automata-lib
        sous ce nom — implémentation propre.

        Parameters
        ----------
        other : automate
            Doit partager le même alphabet que self.
        final_predicate : callable, optional
            (état1, état2) -> bool. Par défaut : les deux doivent être
            finaux (construit l'intersection). Changer ce prédicat permet
            de réutiliser cette même construction pour d'autres opérations.

        Returns
        -------
        ExtendedDFA

        Complexity
        ----------
        O(|Q1| . |Q2|) dans le pire cas.
        """
        if set(self.input_symbols) != set(other.input_symbols):
            raise ValueError(
                "Les deux automates doivent partager le même alphabet."
            )

        def both_final(s1, s2):
            return s1 in self.final_states and s2 in other.final_states

        if final_predicate is None:
            final_predicate = both_final

        initial_pair = (self.initial_state, other.initial_state)
        new_states = {initial_pair}
        new_transitions = {}
        stack = [initial_pair]

        while stack:
            pair = stack.pop()
            if pair in new_transitions:
                continue
            s1, s2 = pair
            new_transitions[pair] = {}
            for symbol in self.input_symbols:
                t1_set = self._successors(s1, symbol)
                t2_set = other._successors(s2, symbol)
                if not t1_set or not t2_set:
                    continue
                target = (next(iter(t1_set)), next(iter(t2_set)))
                new_transitions[pair][symbol] = target
                if target not in new_states:
                    new_states.add(target)
                    stack.append(target)

        state_names = {pair: f"({pair[0]},{pair[1]})" for pair in new_states}

        return type(self)(
            states=set(state_names.values()),
            input_symbols=set(self.input_symbols),
            transitions={
                state_names[pair]: {
                    symbol: state_names[target]
                    for symbol, target in trans.items()
                }
                for pair, trans in new_transitions.items()
            },
            initial_state=state_names[initial_pair],
            final_states={
                state_names[pair]
                for pair in new_states
                if final_predicate(*pair)
            },
            allow_partial=True,
        )

    def language_subset(self, other):
        """Teste l'inclusion de langage : L(self) ⊆ L(other).

        Réduction classique : L(self) ⊆ L(other) ssi
        L(self) ∩ complement(L(other)) est vide (§4.1, #24 du sujet).

        Complexity
        ----------
        O(|Q1| . |Q2|)
        """
        other_complement = other.complement()
        product = self.cartesian_product(other_complement)
        return product.is_language_empty()

    def language_equals(self, other):
        """Égalité de langages, par double test d'inclusion (§4.1, #25).

        Complexity
        ----------
        O(|Q1| . |Q2|)
        """
        return self.language_subset(other) and other.language_subset(self)

    def is_isomorphic(self, other):
        """Teste l'existence d'un isomorphisme entre self et other : une
        bijection entre les états qui préserve exactement la structure des
        transitions, l'état initial et les états finaux.

        Plus fort qu'une simple équivalence de langage (language_equals) :
        deux automates isomorphes ont nécessairement le même nombre d'états.

        Implémentation : BFS synchronisé sur les deux automates, en
        construisant la correspondance état-à-état au fur et à mesure et en
        vérifiant qu'elle reste cohérente à chaque étape.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if len(self.states) != len(other.states):
            return False
        if set(self.input_symbols) != set(other.input_symbols):
            return False

        mapping = {self.initial_state: other.initial_state}
        reverse_mapping = {other.initial_state: self.initial_state}
        queue = [self.initial_state]

        while queue:
            s1 = queue.pop(0)
            s2 = mapping[s1]

            if (s1 in self.final_states) != (s2 in other.final_states):
                return False

            for symbol in self.input_symbols:
                targets1 = self._successors(s1, symbol)
                targets2 = other._successors(s2, symbol)

                if len(targets1) != len(targets2):
                    return False
                if not targets1:
                    continue

                # DFA : un seul successeur ; pour un NFA, cette comparaison
                # simple ne suffirait pas en toute rigueur (il faudrait
                # apparier les ensembles), mais on se limite ici au cas DFA
                # comme le sujet le suggère pour l'isomorphisme (§4.1, #26).
                t1 = next(iter(targets1))
                t2 = next(iter(targets2))

                if t1 in mapping:
                    if mapping[t1] != t2:
                        return False
                elif t2 in reverse_mapping:
                    return False
                else:
                    mapping[t1] = t2
                    reverse_mapping[t2] = t1
                    queue.append(t1)

        return True

    def is_prefix_closed(self):
        """Teste si le langage reconnu est préfixe clos.

        Caractérisation (cf. sujet §4.1, #27) : le langage est préfixe clos
        si et seulement si tous les états utiles sont finaux (un état utile
        non final impliquerait qu'un mot menant à cet état est rejeté, alors
        qu'un mot plus long le prolongeant est accepté — violation directe
        de la clôture par préfixe).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        useful = self.useful_states()
        return useful.issubset(set(self.final_states))

    def prefix_closed_sublanguage(self):
        """Renvoie un nouvel automate reconnaissant le plus grand
        sous-langage préfixe clos inclus dans le langage de self.

        Construction : on ne conserve, en partant de l'état initial, que les
        chemins qui ne traversent jamais un état non final (dès qu'un état
        non final est atteint, tout mot le prolongeant a un préfixe
        rejeté — il est donc exclu du sous-langage préfixe clos, quel que
        soit ce qui suit).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if self.initial_state not in self.final_states:
            # même l'état initial est non final : le sous-langage préfixe
            # clos est vide (le mot vide lui-même serait déjà rejeté, et
            # c'est un préfixe de tout mot).
            trap = "__empty_language__"
            return type(self)(
                states={trap},
                input_symbols=set(self.input_symbols),
                transitions={trap: {s: trap for s in self.input_symbols}},
                initial_state=trap,
                final_states=set(),
                allow_partial=True,
            )

        good_states = {self.initial_state}
        new_transitions = {self.initial_state: {}}
        stack = [self.initial_state]

        while stack:
            state = stack.pop()
            for symbol in self.input_symbols:
                for target in self._successors(state, symbol):
                    if target in self.final_states:
                        new_transitions[state][symbol] = target
                        if target not in good_states:
                            good_states.add(target)
                            new_transitions[target] = {}
                            stack.append(target)
                    # sinon : transition ignorée, le chemin s'arrête ici

        return type(self)(
            states=good_states,
            input_symbols=set(self.input_symbols),
            transitions=new_transitions,
            initial_state=self.initial_state,
            final_states=set(good_states),  # tous les états gardés sont finaux
            allow_partial=True,
        )

    def distinguishable_states(self):
        """Calcule l'ensemble des paires d'états distinguables (algorithme
        classique de remplissage de table).

        Deux états p, q sont distinguables s'il existe un mot w tel que
        lire w depuis p mène à un état final et depuis q à un état non
        final (ou réciproquement).

        Une transition manquante (automate partiel, par exemple après
        trim()) est interprétée comme un saut vers un état puits implicite,
        non final : ce puits est représenté ici par une sentinelle, présente
        pendant le calcul puis retirée du résultat.

        Returns
        -------
        set of frozenset
            Chaque élément est une paire {p, q} d'états RÉELS distinguables.

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        SINK = object()  # état puits implicite (transitions manquantes)
        states = list(self.states) + [SINK]

        def successor(state, symbol):
            if state is SINK:
                return SINK
            targets = self._successors(state, symbol)
            return next(iter(targets)) if targets else SINK

        def is_final(state):
            return state is not SINK and state in self.final_states

        distinguishable = set()

        # initialisation : un final et un non-final sont distinguables
        for i, p in enumerate(states):
            for q in states[i + 1 :]:
                if is_final(p) != is_final(q):
                    distinguishable.add(frozenset({p, q}))

        # remplissage itératif jusqu'à stabilité
        changed = True
        while changed:
            changed = False
            for i, p in enumerate(states):
                for q in states[i + 1 :]:
                    pair = frozenset({p, q})
                    if pair in distinguishable:
                        continue
                    for symbol in self.input_symbols:
                        pt = successor(p, symbol)
                        qt = successor(q, symbol)
                        if (
                            pt is not qt
                            and pt != qt
                            and frozenset({pt, qt}) in distinguishable
                        ):
                            distinguishable.add(pair)
                            changed = True
                            break

        # on retire les paires impliquant la sentinelle : le puits implicite
        # n'est pas un état de l'automate
        return {pair for pair in distinguishable if SINK not in pair}

    def myhill_nerode_partition(self):
        """Calcule les classes d'équivalence de Myhill-Nerode sur les états
        (partition des états non deux-à-deux distinguables).

        Returns
        -------
        list of set
            Les classes d'équivalence.

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        distinguishable = self.distinguishable_states()
        states = list(self.states)
        assigned = {}
        classes = []

        for state in states:
            if state in assigned:
                continue
            new_class = {state}
            for other in states:
                if other == state or other in assigned:
                    continue
                if frozenset({state, other}) not in distinguishable:
                    new_class.add(other)
            for member in new_class:
                assigned[member] = True
            classes.append(new_class)

        return classes

    def is_minimal(self):
        """Teste si l'automate est minimal : accessible et toutes les
        classes de Myhill-Nerode sont des singletons.

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        if self.accessible_states() != set(self.states):
            return False
        return all(len(cls) == 1 for cls in self.myhill_nerode_partition())

    def minimize(self):
        """Renvoie un nouveau DFA minimal équivalent.

        Implémentation pédagogique via les classes de Myhill-Nerode
        (#29/#30), conformément à l'esprit du sujet — automata-lib propose
        déjà une minimisation native optimisée (minify(), Hopcroft), mais
        le sujet demande explicitement de construire la version classique
        par fusion des états équivalents.

        L'automate est d'abord trim (états inutiles retirés).

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        trimmed = self.trim()
        classes = trimmed.myhill_nerode_partition()

        representative = {}
        class_name = {}
        for cls in classes:
            rep = next(iter(cls))
            name = str(sorted(cls))
            for member in cls:
                representative[member] = rep
                class_name[member] = name

        new_states = set(class_name.values())
        new_transitions = {name: {} for name in new_states}
        for state in trimmed.states:
            for symbol in trimmed.input_symbols:
                targets = trimmed._successors(state, symbol)
                if targets:
                    target = next(iter(targets))
                    new_transitions[class_name[state]][symbol] = class_name[
                        target
                    ]

        return type(trimmed)(
            states=new_states,
            input_symbols=set(trimmed.input_symbols),
            transitions=new_transitions,
            initial_state=class_name[trimmed.initial_state],
            final_states={class_name[s] for s in trimmed.final_states},
            allow_partial=True,
        )

    def is_deterministic(self):
        """Teste si la fonction de transition est déterministe : au plus un
        successeur par symbole, et aucune transition epsilon.

        Complexity
        ----------
        O(|Q| . |Σ|)
        """
        for state in self.states:
            paths = self.transitions.get(state, {})
            if "" in paths:
                return False
            for symbol, target in paths.items():
                if isinstance(target, (set, frozenset)) and len(target) > 1:
                    return False
        return True

    def union(self, other, **kwargs):
        """Union des deux langages reconnus.

        Wrapper autour de union() natif de automata-lib (déjà présent sur
        DFA et NFA), ré-enveloppé pour rester chaînable.

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib.
        """
        native_result = super().union(other, **kwargs)
        return self._wrap_native_result(native_result)

    def intersection(self, other, **kwargs):
        """Intersection des deux langages reconnus.

        Wrapper autour de intersection() natif de automata-lib (déjà
        présent sur DFA et NFA).

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib.
        """
        native_result = super().intersection(other, **kwargs)
        return self._wrap_native_result(native_result)

    def difference(self, other, **kwargs):
        """L(self) privé de L(other).

        difference() n'existe nativement que sur DFA (vérifié par
        introspection). Si l'un des deux automates est un NFA, on le
        détermine d'abord (determinize), puis on wrappe la version native.

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib (après
        déterminisation éventuelle).
        """
        from automata.fa.dfa import DFA

        self_dfa = self if isinstance(self, DFA) else self.determinize()
        other_dfa = other if isinstance(other, DFA) else other.determinize()

        native_result = DFA.difference(self_dfa, other_dfa, **kwargs)
        return self_dfa._wrap_native_result(native_result)

    def concatenate(self, other):
        """Concaténation des deux langages : L(self) . L(other).

        Wrapper autour de concatenate() natif de automata-lib (NFA
        uniquement). Si self ou other est un DFA, il est d'abord vu comme
        NFA (pas de perte d'information : tout DFA est un NFA particulier).

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib.
        """
        from automata.fa.nfa import NFA

        self_nfa = self if isinstance(self, NFA) else NFA.from_dfa(self)
        other_nfa = other if isinstance(other, NFA) else NFA.from_dfa(other)

        native_result = NFA.concatenate(self_nfa, other_nfa)
        return self._wrap_native_result(native_result)

    def kleene_star(self):
        """Étoile de Kleene du langage reconnu.

        Wrapper autour de kleene_star() natif de automata-lib (NFA
        uniquement). Si self est un DFA, il est d'abord vu comme NFA.

        Complexity
        ----------
        Celle de l'implémentation native de automata-lib.
        """
        from automata.fa.nfa import NFA

        self_nfa = self if isinstance(self, NFA) else NFA.from_dfa(self)
        native_result = NFA.kleene_star(self_nfa)
        return self._wrap_native_result(native_result)

    def left_quotient_word(self, word):
        """Quotient à gauche du langage par un mot : {u : word.u ∈ L(self)}.

        Nommée avec le suffixe _word (plutôt que left_quotient) car
        automata-lib définit déjà left_quotient(other) sur NFA avec un
        AUTOMATE en argument, pas un mot — même situation que predecessors.

        Implémentation : les états atteints après lecture de `word` (avec
        epsilon-fermeture si NFA) deviennent les nouveaux états initiaux.

        Complexity
        ----------
        O(|w| . |Q|)
        """
        from automata.fa.dfa import DFA

        if isinstance(self, DFA):
            current = self.initial_state
            for symbol in word:
                successors = self._successors(current, symbol)
                if not successors:
                    # mot non reconnu en cours de route : quotient vide
                    trap = "__empty__"
                    return type(self)(
                        states={trap},
                        input_symbols=set(self.input_symbols),
                        transitions={
                            trap: {s: trap for s in self.input_symbols}
                        },
                        initial_state=trap,
                        final_states=set(),
                        allow_partial=True,
                    )
                current = next(iter(successors))
            return type(self)(
                states=set(self.states),
                input_symbols=set(self.input_symbols),
                transitions={s: dict(p) for s, p in self.transitions.items()},
                initial_state=current,
                final_states=set(self.final_states),
                allow_partial=getattr(self, "allow_partial", False),
            )

        # NFA : on suit l'ensemble d'états actifs, avec epsilon-fermeture
        current_set = self.epsilon_closure(self.initial_state)
        for symbol in word:
            next_set = set()
            for state in current_set:
                next_set |= self._successors(state, symbol)
            current_set = self.epsilon_closure(next_set) if next_set else set()

        new_initial = "__quotient_initial__"
        while new_initial in self.states:
            new_initial += "_"

        new_states = set(self.states) | {new_initial}
        new_transitions = {s: dict(p) for s, p in self.transitions.items()}
        new_transitions[new_initial] = (
            {"": set(current_set)} if current_set else {}
        )

        from ..nfa import ExtendedNFA

        return ExtendedNFA(
            states=new_states,
            input_symbols=set(self.input_symbols),
            transitions=new_transitions,
            initial_state=new_initial,
            final_states=set(self.final_states),
        )

    def right_quotient_word(self, word):
        """Quotient à droite du langage par un mot : {u : u.word ∈ L(self)}.

        Implémentation via le renversement (§4.7 : réutiliser plutôt que
        dupliquer) : le quotient à droite de L par w est le renversé du
        quotient à gauche de reverse(L) par le mot renversé w^R.

        Complexity
        ----------
        O(|w| . |Q|)
        """
        reversed_word = word[::-1]
        return self.reverse().left_quotient_word(reversed_word).reverse()

    def syntactic_monoid(self):
        """Calcule le monoïde syntaxique de l'automate : l'ensemble des
        transformations d'états induites par les mots de l'alphabet
        (modulo égalité de comportement), muni de la composition (#62).

        Construction par clôture : on part de l'identité et des
        transformations "lire un symbole", puis on compose jusqu'à
        stabilité (aucune nouvelle transformation ne peut être obtenue).

        Returns
        -------
        set of tuple
            Chaque élément est une transformation, représentée comme un
            tuple des images de chaque état (dans un ordre fixé), ce qui
            la rend hashable et comparable.

        Complexity
        ----------
        O(|monoïde résultant| . |Q| . |Σ|), le monoïde pouvant être de
        taille exponentielle en |Q| dans le pire cas théorique — à
        réserver aux petits automates.
        """
        states = tuple(sorted(self.states, key=str))
        index = {s: i for i, s in enumerate(states)}

        def transform_of_symbol(symbol):
            images = []
            for s in states:
                successors = self._successors(s, symbol)
                images.append(next(iter(successors)) if successors else None)
            return tuple(images)

        def compose(t1, t2):
            # applique t1 puis t2 (lire un mot puis un autre)
            result = []
            for img in t1:
                if img is None:
                    result.append(None)
                else:
                    result.append(t2[index[img]])
            return tuple(result)

        identity = tuple(states)
        generators = {transform_of_symbol(s) for s in self.input_symbols}

        monoid = {identity} | generators
        frontier = set(monoid)

        while frontier:
            new_frontier = set()
            for t1 in frontier:
                for t2 in generators:
                    composed = compose(t1, t2)
                    if composed not in monoid:
                        monoid.add(composed)
                        new_frontier.add(composed)
            frontier = new_frontier

        return monoid

    def minimize_hopcroft(self):
        """Minimise l'automate par l'algorithme de Hopcroft (1971),
        alternative à minimize() : même résultat (DFA minimal équivalent),
        mais en O(|Q| . log|Q| . |Σ|) au lieu de O(|Q|^2 . |Σ|).

        Principe : raffine itérativement une partition des états, en
        partant de {finaux, non-finaux}. Pour chaque "séparateur" (bloc,
        symbole) restant à traiter, chaque bloc de la partition ayant des
        états qui se comportent différemment vis-à-vis de ce séparateur
        est éclaté en deux. L'astuce qui donne la complexité O(n log n) :
        après un éclatement, seule la PLUS PETITE des deux moitiés est
        ajoutée à la file d'attente des séparateurs à traiter (l'autre
        moitié, plus grande, n'a pas besoin de l'être : elle sera
        indirectement affinée si nécessaire par d'autres séparateurs).

        Returns
        -------
        ExtendedDFA

        Complexity
        ----------
        O(|Q| . log|Q| . |Σ|)

        References
        ----------
        Hopcroft, J. E. (1971). An n log n algorithm for minimizing
        states in a finite automaton.
        """
        trimmed = self.trim()
        if trimmed.is_language_empty():
            return trimmed  # déjà minimal (1 seul état)

        states = set(trimmed.states)
        finals = set(trimmed.final_states)
        non_finals = states - finals

        # prédécesseurs inversés : (état, symbole) -> ensemble d'états sources
        preimage = {
            (s, sym): set() for s in states for sym in trimmed.input_symbols
        }
        for s in states:
            for sym in trimmed.input_symbols:
                for target in trimmed._successors(s, sym):
                    preimage[(target, sym)].add(s)

        partition = [b for b in (finals, non_finals) if b]
        # file d'attente de séparateurs (bloc, symbole) à traiter
        queue = [(b, sym) for b in partition for sym in trimmed.input_symbols]

        block_id = {}
        for i, b in enumerate(partition):
            for s in b:
                block_id[s] = i

        while queue:
            separator, sym = queue.pop()
            # états ayant une transition par sym vers un état de `separator`
            affected = set()
            for s in separator:
                affected |= preimage.get((s, sym), set())

            touched_blocks = {}
            for s in affected:
                touched_blocks.setdefault(block_id[s], set()).add(s)

            for bid, in_block in touched_blocks.items():
                whole_block = partition[bid]
                out_block = whole_block - in_block
                if not out_block:
                    continue  # le bloc entier est affecté, pas de scission

                # scission : le plus petit morceau devient un nouveau bloc
                smaller, larger = (
                    (in_block, out_block)
                    if len(in_block) <= len(out_block)
                    else (out_block, in_block)
                )

                partition[bid] = larger
                new_id = len(partition)
                partition.append(smaller)
                for s in smaller:
                    block_id[s] = new_id

                for s2 in trimmed.input_symbols:
                    if (whole_block, s2) in queue:
                        queue.remove((whole_block, s2))
                        queue.append((larger, s2))
                        queue.append((smaller, s2))
                    else:
                        queue.append((smaller, s2))

        # construction du DFA minimal à partir de la partition finale
        rep_name = {}
        for i, block in enumerate(partition):
            name = "{" + ",".join(sorted(block)) + "}"
            for s in block:
                rep_name[s] = name

        new_transitions = {}
        new_final_states = set()
        for block in partition:
            representative = next(iter(block))
            name = rep_name[representative]
            new_transitions[name] = {}
            for sym in trimmed.input_symbols:
                successors = trimmed._successors(representative, sym)
                if successors:
                    new_transitions[name][sym] = rep_name[
                        next(iter(successors))
                    ]
            if representative in trimmed.final_states:
                new_final_states.add(name)

        return type(trimmed)(
            states=set(rep_name.values()),
            input_symbols=set(trimmed.input_symbols),
            transitions=new_transitions,
            initial_state=rep_name[trimmed.initial_state],
            final_states=new_final_states,
            allow_partial=True,
        )
