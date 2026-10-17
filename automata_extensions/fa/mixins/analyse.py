"""Algorithmes d'analyse structurelle : parcours, accessibilité, coaccessibilité, cycles, SCC..."""

from collections import deque


class AnalyseMixin:
    """Regroupe les algorithmes de parcours et d'analyse structurelle."""

    def dfs(self, start=None):
        """Parcours en profondeur (itératif, via une pile).

        Parameters
        ----------
        start : optional
            État de départ. Si None, utilise self.initial_state.

        Returns
        -------
        list
            Les états dans l'ordre de leur première visite.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if start is None:
            start = self.initial_state

        visited = set()
        order = []
        stack = [start]

        while stack:
            state = stack.pop()
            if state not in visited:
                visited.add(state)
                order.append(state)
                for symbol in self.transitions.get(state,{}):
                    for next_state in self._successors(state, symbol):
                        if next_state not in visited:
                            stack.append(next_state)

        return order

    def bfs(self, start=None):
        """Parcours en largeur (via une file).

        Parameters
        ----------
        start : optional
            État de départ. Si None, utilise self.initial_state.

        Returns
        -------
        list
            Les états dans l'ordre de leur première visite (par niveaux).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        if start is None:
            start = self.initial_state

        visited = {start}
        order = []
        queue = deque([start])

        while queue:
            state = queue.popleft()
            order.append(state)
            for symbol in self.transitions.get(state,{}):
                for next_state in self._successors(state, symbol):
                    if next_state not in visited:
                        visited.add(next_state)
                        queue.append(next_state)

        return order

    def predecessor_states(self, state):
        """Calcule les prédécesseurs d'un état (parcours inverse des transitions).

        Parameters
        ----------
        state
            L'état dont on cherche les prédécesseurs.

        Returns
        -------
        set
            Ensemble des états ayant au moins une transition vers `state`.

        Complexity
        ----------
        O(|E|)
        """
        preds = set()
        for source_state in self.states:
            for symbol in self.transitions.get(source_state, {}):
                if state in self._successors(source_state, symbol):
                    preds.add(source_state)
        return preds

    def accessible_states(self):
        """Calcule les états accessibles depuis l'état initial.

        Returns
        -------
        set
            Ensemble des états atteignables depuis self.initial_state.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return set(self.dfs())

    def is_accessible(self, state):
        """Teste si un état est accessible depuis l'état initial.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return state in self.accessible_states()

    def reachable_states_from(self, state):
        """Calcule les états atteignables depuis un état donné (pas forcément l'initial).

        Parameters
        ----------
        state
            État de départ du parcours.

        Returns
        -------
        set
            Ensemble des états atteignables depuis `state`.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return set(self.dfs(start=state))

    def coaccessible_states(self):
        """Calcule les états coaccessibles (états depuis lesquels on peut
        atteindre un état final).

        Implémentation : les états coaccessibles de self sont exactement
        les états accessibles de self.reverse() (en ignorant le nouvel état
        initial artificiel ajouté par reverse).

        Returns
        -------
        set
            Ensemble des états coaccessibles.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        reversed_automaton = self.reverse()
        accessible_in_reversed = reversed_automaton.accessible_states()
        # on retire le nouvel état initial artificiel créé par reverse(),
        # qui n'existe pas dans self.states
        return accessible_in_reversed & set(self.states)

    def is_coaccessible(self, state):
        """Teste si un état est coaccessible.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return state in self.coaccessible_states()

    def useful_states(self):
        """Calcule les états utiles (accessibles ET coaccessibles).

        Returns
        -------
        set
            Intersection des états accessibles et coaccessibles.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return self.accessible_states() & self.coaccessible_states()

    def induced_subautomaton(self, states_subset, initial_state=None):
        """Renvoie un nouvel automate restreint à un sous-ensemble d'états.

        Les transitions vers des états hors du sous-ensemble sont retirées.

        Parameters
        ----------
        states_subset : set
            Sous-ensemble des états à conserver.
        initial_state : optional
            État initial du sous-automate. Par défaut, self.initial_state
            (doit alors appartenir à states_subset). Permet de construire
            un sous-automate "vu depuis" un autre état que l'initial
            d'origine (utile pour has_cycle_from par exemple).

        Returns
        -------
        Un nouvel automate du même type que self (DFA reste DFA, NFA reste NFA).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        from automata.fa.dfa import DFA

        states_subset = set(states_subset)
        if initial_state is None:
            initial_state = self.initial_state
        if initial_state not in states_subset:
            raise ValueError(
                "L'état initial du sous-automate doit appartenir au "
                "sous-ensemble d'états."
            )

        new_transitions = {}
        for state in states_subset:
            new_transitions[state] = {}
            for symbol in self.transitions.get(state, {}):
                targets = self._successors(state, symbol) & states_subset
                if targets:
                    original_value = self.transitions[state][symbol]
                    if isinstance(original_value, (set, frozenset)):
                        new_transitions[state][symbol] = targets
                    else:
                        new_transitions[state][symbol] = next(iter(targets))

        kwargs = dict(
            states=states_subset,
            input_symbols=set(self.input_symbols),
            transitions=new_transitions,
            initial_state=initial_state,
            final_states=set(self.final_states) & states_subset,
        )
        if isinstance(self, DFA):
            # émonder peut rendre le DFA partiel (états retirés = transitions
            # manquantes) : c'est un résultat légitime, pas une erreur.
            kwargs["allow_partial"] = True

        return type(self)(**kwargs)


    def trim(self):
        """Renvoie un nouvel automate émondé (restreint aux états utiles).

        Cas particulier : si aucun état n'est utile (langage vide), on ne
        peut pas construire un automate à 0 état (un état initial est
        obligatoire) — on renvoie alors un automate minimal à 1 état,
        non final, qui reconnaît bien le langage vide.

        Returns
        -------
        Un nouvel automate ne contenant que les états accessibles et
        coaccessibles (ou un automate à 1 état si le langage est vide).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        useful = self.useful_states()
        if not useful:
            from automata.fa.dfa import DFA
            trap = "__empty_language__"
            kwargs = dict(
                states={trap},
                input_symbols=set(self.input_symbols),
                transitions={trap: {s: trap for s in self.input_symbols}},
                initial_state=trap,
                final_states=set(),
            )
            if isinstance(self, DFA):
                kwargs["allow_partial"] = True
            return type(self)(**kwargs)
        return self.induced_subautomaton(useful)


    def is_trim(self):
        """Teste si l'automate est déjà émondé (tous les états sont utiles).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return self.useful_states() == set(self.states)

    def strongly_connected_components(self):
        """Calcule les composantes fortement connexes (algorithme de Tarjan).

        Une SCC est un ensemble maximal d'états mutuellement atteignables
        les uns depuis les autres.

        Returns
        -------
        list of set
            Liste des composantes fortement connexes (chaque composante
            est un ensemble d'états).

        Complexity
        ----------
        O(|Q| + |E|)

        References
        ----------
        Tarjan, R. E. (1972). Depth-first search and linear graph algorithms.
        """
        index_counter = [0]
        index = {}       # état -> ordre de découverte
        lowlink = {}     # état -> plus petit index atteignable
        on_stack = set()
        stack = []
        sccs = []

        def strongconnect(state):
            index[state] = index_counter[0]
            lowlink[state] = index_counter[0]
            index_counter[0] += 1
            stack.append(state)
            on_stack.add(state)

            for symbol in self.transitions.get(state, {}):
                for successor in self._successors(state, symbol):
                    if successor not in index:
                        strongconnect(successor)
                        lowlink[state] = min(lowlink[state], lowlink[successor])
                    elif successor in on_stack:
                        lowlink[state] = min(lowlink[state], index[successor])

            # state est une racine de SCC : on dépile toute la composante
            if lowlink[state] == index[state]:
                scc = set()
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    scc.add(member)
                    if member == state:
                        break
                sccs.append(scc)

        for state in self.states:
            if state not in index:
                strongconnect(state)

        return sccs


    def has_cycle(self):
        """Détecte l'existence d'un cycle dans l'automate.

        Un cycle existe si une composante fortement connexe contient
        plusieurs états, ou un seul état avec une boucle sur lui-même.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        for scc in self.strongly_connected_components():
            if len(scc) > 1:
                return True
            # SCC de taille 1 : vérifier une éventuelle boucle sur soi-même
            (state,) = scc
            for symbol in self.transitions.get(state, {}):
                if state in self._successors(state, symbol):
                    return True
        return False

    def has_cycle_from(self, state):
        """Détecte l'existence d'un cycle accessible depuis un état donné.

        Restreint la détection au sous-automate induit par les états
        atteignables depuis `state`.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        reachable = self.reachable_states_from(state)
        sub = self.induced_subautomaton(reachable, initial_state=state)
        return sub.has_cycle()

    def is_language_empty(self):
        """Décide si le langage reconnu est vide.

        Le langage est vide si aucun état accessible n'est final.

        Complexity
        ----------
        O(|Q| + |E|)
        """
        return len(self.accessible_states() & set(self.final_states)) == 0

    def is_language_infinite(self):
        """Décide si le langage reconnu est infini.

        Le langage est infini s'il existe un cycle à la fois accessible
        et coaccessible (un mot peut alors être "pompé" indéfiniment tout
        en restant accepté).

        Complexity
        ----------
        O(|Q| + |E|)
        """
        useful = self.useful_states()
        if not useful:
            return False
        # useful non vide implique nécessairement que l'état initial en
        # fait partie : tout état utile est atteignable depuis l'état
        # initial, qui peut donc lui aussi atteindre le même final.
        sub = self.induced_subautomaton(useful, initial_state=self.initial_state)
        return sub.has_cycle()

    def accepts_word(self, word):
        """Teste si un mot est reconnu par l'automate.

        Wrapper autour de accepts_input() de automata-lib (ne réimplémente
        rien : automata-lib fournit déjà cet algorithme).

        Complexity
        ----------
        O(|w| . |Q|)
        """
        return self.accepts_input(word)

    def execution_trace(self, word):
        """Calcule la trace d'exécution d'un mot : la suite des (ensembles
        d')états visités au fil de la lecture.

        Parameters
        ----------
        word : str
            Le mot à exécuter.

        Returns
        -------
        list
            Liste des états (ou ensembles d'états pour un NFA) visités,
            en commençant par l'état initial.

        Complexity
        ----------
        O(|w| . |Q|)
        """
        from automata.fa.dfa import DFA

        if isinstance(self, DFA):
            trace = [self.initial_state]
            current = self.initial_state
            for symbol in word:
                successors = self._successors(current, symbol)
                if not successors:
                    # mot rejeté : plus de transition possible
                    trace.append(None)
                    return trace
                current = next(iter(successors))
                trace.append(current)
            return trace
        else:
            # NFA : on suit l'ensemble des états actifs à chaque étape
            current_set = self.epsilon_closure(self.initial_state)
            trace = [current_set]
            for symbol in word:
                next_set = set()
                for state in current_set:
                    next_set |= self._successors(state, symbol)
                current_set = self.epsilon_closure(next_set) if next_set else set()
                trace.append(current_set)
            return trace
