"""Grammaires, arbres de dérivation, équations rationnelles, monoïde syntaxique."""


class GrammaireMixin:
    """Regroupe les algorithmes liés aux grammaires régulières."""

    def to_grammar(self):
        """Convertit l'automate en grammaire régulière équivalente.

        Construction directe (#55) : un non-terminal par état, une règle
        state -> symbole . target pour chaque transition, et
        state -> ε pour chaque état final.

        Returns
        -------
        RegularGrammar

        Complexity
        ----------
        O(|Q| + |E|)
        """
        from ...grammar.grammar import RegularGrammar

        rules = {state: [] for state in self.states}
        for state in self.states:
            for symbol in self.transitions.get(state, {}):
                for target in self._successors(state, symbol):
                    rules[state].append((symbol, target))
            if state in self.final_states:
                rules[state].append(())

        return RegularGrammar(
            variables=set(self.states),
            terminals=set(self.input_symbols),
            rules=rules,
            start_variable=self.initial_state,
        )

    @classmethod
    def grammar_to_automaton(cls, grammar):
        """Convertit une grammaire régulière en automate équivalent (#55).

        Construction inverse de to_grammar : un état par non-terminal, une
        transition state --symbole--> target pour chaque règle
        state -> symbole target, et state devient final s'il a une règle
        state -> ε. Un nouvel état "accepteur" est ajouté pour les règles
        state -> symbole (sans second non-terminal), qui terminent le mot.

        Parameters
        ----------
        grammar : RegularGrammar

        Returns
        -------
        ExtendedNFA
        """
        from ..nfa import ExtendedNFA

        accept_state = "__accept__"
        while accept_state in grammar.variables:
            accept_state += "_"

        states = set(grammar.variables) | {accept_state}
        transitions = {s: {} for s in states}
        final_states = {accept_state}

        for var, prods in grammar.rules.items():
            for prod in prods:
                if len(prod) == 0:
                    final_states.add(var)
                elif len(prod) == 1:
                    symbol = prod[0]
                    transitions[var].setdefault(symbol, set()).add(accept_state)
                else:
                    symbol, target = prod
                    transitions[var].setdefault(symbol, set()).add(target)

        return ExtendedNFA(
            states=states,
            input_symbols=set(grammar.terminals),
            transitions=transitions,
            initial_state=grammar.start_variable,
            final_states=final_states,
        )

    def derivation_tree(self, word):
        """Construit l'arbre (chaîne) de dérivation d'un mot, via la
        grammaire régulière associée à l'automate (#56).

        Suppose que self est déterministe (DFA) : à chaque étape, au plus
        une règle de la grammaire correspond au symbole lu, ce qui rend
        la dérivation unique.

        Parameters
        ----------
        word : str

        Returns
        -------
        Node
            La racine de la chaîne de dérivation.

        Raises
        ------
        ValueError
            Si le mot n'est pas reconnu par l'automate.
        """
        from ...grammar.parse_tree import Node, Leaf

        if not self.accepts_input(word):
            raise ValueError(f"le mot {word!r} n'est pas reconnu par l'automate")

        current = self.initial_state
        nodes = []
        for symbol in word:
            successors = self._successors(current, symbol)
            target = next(iter(successors))
            nodes.append((current, symbol))
            current = target
        nodes.append((current, None))  # dernière étape : current est final

        root = None
        for variable, symbol in reversed(nodes):
            if symbol is None:
                root = Node(variable)
            else:
                root = Node(variable, leaf=Leaf(symbol), child=root)
        return root

    def myhill_nerode_language_classes(self):
        """Calcule les classes de résiduels du langage (quotients à gauche
        distincts), #59 — à ne pas confondre avec myhill_nerode_partition
        (#30), qui classe les ÉTATS d'un automate donné.

        Par le théorème de Myhill-Nerode, ces classes sont en bijection
        avec les états du DFA minimal : chaque classe est représentée ici
        par le plus court mot (trouvé par BFS) qui, lu depuis l'état
        initial du DFA minimal, atteint l'état correspondant.

        Returns
        -------
        dict
            mot représentatif (le plus court) -> automate ExtendedDFA
            reconnaissant ce quotient (left_quotient_word(mot)).

        Complexity
        ----------
        O(|Q|^2 . |Σ|) (dominé par minimize()).
        """
        from collections import deque

        minimal = self.minimize()

        shortest_word = {minimal.initial_state: ""}
        queue = deque([minimal.initial_state])
        while queue:
            state = queue.popleft()
            for symbol in sorted(minimal.input_symbols):
                for target in minimal._successors(state, symbol):
                    if target not in shortest_word:
                        shortest_word[target] = shortest_word[state] + symbol
                        queue.append(target)

        return {
            word: self.left_quotient_word(word)
            for word in shortest_word.values()
        }

    def residual_automaton(self):
        """Construit l'automate résiduel : un état par résiduel distinct
        du langage (mot représentatif le plus court), transitions données
        par la lecture d'un symbole supplémentaire (#60).

        Returns
        -------
        ExtendedDFA
            Isomorphe au DFA minimal, mais avec des états nommés par leur
            mot représentatif plutôt que par des identifiants arbitraires.

        Complexity
        ----------
        O(|Q|^2 . |Σ|)
        """
        classes = self.myhill_nerode_language_classes()
        words = list(classes.keys())

        # associe chaque résiduel (par valeur d'automate) à son mot le
        # plus court, pour retrouver l'état cible de chaque transition
        residual_to_word = {}
        for word in words:
            residual_to_word[word] = word  # le mot EST déjà le nom canonique

        transitions = {word: {} for word in words}
        final_words = set()

        for word in words:
            residual = classes[word]
            if residual.accepts_input(""):
                final_words.add(word)
            for symbol in self.input_symbols:
                target_residual = residual.left_quotient_word(symbol)
                # cherche, parmi les résiduels connus, lequel a le même langage
                for other_word in words:
                    if classes[other_word].language_equals(target_residual):
                        transitions[word][symbol] = other_word
                        break

        return type(self)(
            states=set(words),
            input_symbols=set(self.input_symbols),
            transitions=transitions,
            initial_state="",
            final_states=final_words,
            allow_partial=True,
        )

    def automaton_morphism(self, other, mapping):
        """Vérifie si `mapping` est un morphisme d'automates valide de self
        vers other : une application entre les états qui préserve les
        transitions (#61).

        Un morphisme doit satisfaire : pour tout état p et tout symbole a,
        si p --a--> q dans self, alors mapping(p) --a--> mapping(q) dans
        other. On vérifie aussi que l'état initial et les états finaux
        sont respectés.

        Parameters
        ----------
        other : automate
        mapping : dict
            état de self -> état de other.

        Returns
        -------
        bool

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if mapping.get(self.initial_state) != other.initial_state:
            return False

        for state in self.states:
            if state not in mapping:
                return False
            is_final_self = state in self.final_states
            is_final_other = mapping[state] in other.final_states
            if is_final_self != is_final_other:
                return False

            for symbol in self.transitions.get(state, {}):
                for target in self._successors(state, symbol):
                    if target not in mapping:
                        return False
                    expected = mapping[target]
                    actual_targets = other._successors(mapping[state], symbol)
                    if expected not in actual_targets:
                        return False
        return True
