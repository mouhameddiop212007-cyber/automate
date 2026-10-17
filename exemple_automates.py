# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 21:24:57 2026

@author: kanyf
"""

from IPython.display import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

# Définition d'un DFA qui accepte les mots se terminant par "a"
automate_fig_3_1_a = DFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2', 'b': '3'},
        '2': {'a': '2', 'b': '3'},
        '3': {'a': '3', 'b': '3'}
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_3_1_b = DFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2', 'b': '1'},
        '2': {'a': '3', 'b': '2'},
        '3': {'a': '3', 'b': '3'}
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_3_1_c = NFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2'},
        '2': {'a': '3'},
        '3': {'a': '3', 'b': '3'}
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_3_1_d = DFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2', 'b': '1'},
        '2': {'a': '3', 'b': '2'},
        '3': {'a': '1', 'b': '3'}
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_3_1_e = NFA(
    states={'1', '2', '3'},
    input_symbols={'a'},
    transitions={
        '1': {'a': '2'},
        '2': {'a': '3'},
        '3': {'a': '1'}
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_3_1_f = NFA(
    states={'1', '2', '3'},
    input_symbols={'a', 'b'},
    transitions={
        '1': {'a': '2', 'b':'3'},
        '2': {'a': '3', 'b':'1'},
        '3': {'a': '1', 'b':'2'}
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_4_1_a = NFA(
    states={'0', '1', '2'},
    input_symbols={'a', 'b'},
    transitions={
        '0': {'a': '2', 'b':'1'},
        '1': {'a': '0','b':'0'},
        '2': {'a': '1'}
    },
    initial_state='0',
    final_states={'0'}
)

automate_fig_4_1_b = NFA(
    states={'0'},
    input_symbols={'a', 'b'},
    transitions={
        '0': {'b':'0'}
    },
    initial_state='0',
    final_states={'0'}
)

automate_fig_4_1_c = NFA(
    states={'0'},
    input_symbols={'a', 'b'},
    transitions={
        '0': {'a':'0'}
    },
    initial_state='0',
    final_states={'0'}
)

automate_table_6_1_a = DFA(
    states={'0', '1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '0': {'a': '0', 'b': '1'},
        '1': {'a': '2', 'b': '3'},
        '2': {'a': '2', 'b': '3'},
        '3': {'a': '2', 'b': '4'},
        '4': {'a': '0', 'b': '1'}
    },
    initial_state='0',
    final_states={'3'}
)

automate_table_6_1_b = DFA(
    states={'1', '2', '3', '4', '5', '6', '7', '8'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '3', 'b': '8'},
        '2': {'a': '3', 'b': '1'},
        '3': {'a': '8', 'b': '2'},
        '4': {'a': '5', 'b': '6'},
        '5': {'a': '6', 'b': '2'},
        '6': {'a': '7', 'b': '8'},
        '7': {'a': '6', 'b': '4'},
        '8': {'a': '5', 'b': '8'}
    },
    initial_state='1',
    final_states={'4'}
)

automate_table_6_1_c = DFA(
    states={'0', '1', '2', '3', '4', '5'},
    input_symbols={'a','b'},
    transitions={
        '0': {'a': '1', 'b': '3'},
        '1': {'a': '2', 'b': '3'},
        '2': {'a': '5', 'b': '2'},
        '3': {'a': '4', 'b': '1'},
        '4': {'a': '5', 'b': '4'},
        '5': {'a': '5', 'b': '5'},
    },
    initial_state='0',
    final_states={'0', '2', '4'}
)

automate_fig_6_1_a = DFA(
    states={'1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '2', 'b': '1'},
        '2': {'a': '2', 'b': '3'},
        '3': {'a': '4', 'b': '3'},
        '4': {'a': '4', 'b': '3'}
    },
    initial_state='1',
    final_states={'3','4'}
)

automate_fig_6_1_b = DFA(
    states={'1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '2', 'b': '1'},
        '2': {'a': '2', 'b': '4'},
        '3': {'a': '3', 'b': '1'},
        '4': {'a': '3', 'b': '4'}
    },
    initial_state='1',
    final_states={'1','4'}
)

automate_fig_6_2_a = NFA(
    states={'1', '2', '3', '4', '5'},
    input_symbols={'0','1'},
    transitions={
        '1': {'1': '2'},
        '2': {'0': '5', '1': '3'},
        '3': {},
        '4': {'0': '5'},
        '5': {'0': '3', '1':'4'},
    },
    initial_state='1',
    final_states={'1','5'}
)

automate_fig_6_2_b = NFA(
    states={'0', '1', '2'},
    input_symbols={'0','1'},
    transitions={
        '0': {'1': '1'},
        '1': {'0': '0', '1': '2'},
        '2': {}
    },
    initial_state='0',
    final_states={'0'}
)

automate_fig_6_3_a = DFA(
    states={'1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '3', 'b': '2'},
        '2': {'a': '1', 'b': '1'},
        '3': {'a': '2', 'b': '4'},
        '4': {'a': '4', 'b': '4'}
    },
    initial_state='1',
    final_states={'2', '3', '4'}
)

automate_fig_6_3_b = NFA(
    states={'1', '2', '3', '4', '5'},
    input_symbols={'0','1'},
    transitions={
        '1': {'1': '2'},
        '2': {'0': '5', '1': '3'},
        '3': {},
        '4': {'0': '5'},
        '5': {'0': '3', '1':'4'}
    },
    initial_state='1',
    final_states={'1','5'}
)

automate_table_7_1_a = NFA(
    states={'0', '1', '2', '3', '4', '5'},
    input_symbols={'a','b'},
    transitions={
        '0': {'a': {'1','2','3','4','5'}},
        '1': {'a': {'2','3'}, 'b': '4'},
        '2': {'a': {'0','1','4'}, 'b': {'1','2','3'}},
        '3': {'a': '0', 'b': {'1','2','5'}},
        '4': {'a': '1'},
        '5': {'a': '2', 'b': {'2','3','5'}},
    },
    initial_state='0',
    final_states={'4'}
)

automate_table_7_1_b = NFA(
    states={'0', '1', '2', '3', '4', '5'},
    input_symbols={'a','b'},
    transitions={
        '0': {'a': {'1','2'}},
        '1': {'b': '3'},
        '2': {'b': '4'},
        '3': {'a': '5'},
        '4': {},
        '5': {'b': '0'},
    },
    initial_state='0',
    final_states={'0','3','4'}
)

automate_fig_7_1_a = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': {'1','2'},  'b':'1'},
        '2': {'a': '3', 'b': '3'},
        '3': {}
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_7_1_b = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'b': {'2','3'}},
        '2': {'a': '1', 'b':'3'},
        '3': {}
    },
    initial_state='1',
    final_states={'1'}
)

automate_fig_7_1_c = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': {'1','2'}},
        '2': {'b': {'2','3'}},
        '3': {}
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_7_2_a = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '3', 'b': '2'},
        '2': {'b': '3', 'a': {'1','3'}},
        '3': {'a': '3', 'b': '3'}
    },
    initial_state='1',
    final_states={'1'}
)

automate_fig_7_2_b = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'b': {'2', '3'}},
        '2': {'b': '3', 'a': '1'},
        '3': {}
    },
    initial_state='1',
    final_states={'1'}
)

automate_fig_7_2_c = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': {'1', '2'}},
        '2': {'b': {'2', '3'}},
        '3': {}
    },
    initial_state='1',
    final_states={'3'}
)


automate_fig_7_3_a = NFA(
    states={'1', '2'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': {'1','2'}, 'b':'1'},
        '2': {'a': '2', 'b':'2'},
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_7_3_b = DFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a': '2', 'b':'3'},
        '2': {'a': '3', 'b':'1'},
        '3': {'a': '1', 'b':'3'},
    },
    initial_state='1',
    final_states={'1'}
)

automate_fig_7_3_c = NFA(
    states={'a', 'b'},
    input_symbols={'a','b'},
    transitions={
        'a': {'a': {'a','b'}, 'b': {'a', 'b'}},
        'b': {'a': {'a','b'}, 'b': {'a', 'b'}},
    },
    initial_state='a',
    final_states={'a','b'}
)

automate_fig_8_1_a = NFA(
    states={'0', '1', '2', '3', '4'},
    input_symbols={'a','b','ϵ'},
    transitions={
        '0': {'a': '1', 'ϵ':'3'},
        '1': {'a': '2', 'b':'0'},
        '2': {'b':'1'},
        '3': {'a': '4'},
        '4': {'b': '3', 'ϵ':'2'},
    },
    initial_state='0',
    final_states={'1','2','3','4'}
)

automate_fig_8_1_b = NFA(
    states={'1', '2', '3', '4'},
    input_symbols={'a','b','c','ϵ'},
    transitions={
        '1': {'a': {'1','4'}, 'b':{'2','4'}, 'ϵ':{'1'}},
        '2': {'a':{'2'},'b': {'2','4'},'c':{'2'},'ϵ':{'4'}},
        '3': {'c': '3'},
        '4': {'a':{'3','4'},'b': '4', 'c':'4'},
    },
    initial_state='1',
    final_states={'1','2','3'}
)

automate_fig_10_1_a = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'b':'2'},
        '2': {'a':'3'},
        '3': {'a': '3','b':'3'},
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_10_1_b = NFA(
    states={'1', '2'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a':'2','b':'1'},
        '2': {'a':'1','b':'2'},
    },
    initial_state='1',
    final_states={'1'}
)

automate_fig_10_1_c = NFA(
    states={'1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a':{'1','2'},'b':{'1'}},
        '2': {'b':{'3'}},
        '3': {'b':{'4'}},
        '4': {},
    },
    initial_state='1',
    final_states={'4'}
)

automate_fig_10_1_d = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a':'3','b':'2'},
        '2': {'a':'1','b':'3'},
        '3': {'a':'2','b':'1'},
    },
    initial_state='1',
    final_states={'2'}
)

automate_fig_10_2_a = NFA(
    states={'0', '1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '0': {'b':'0','a':'1'},
        '1': {'a':'1','b':'2'},
        '2': {'a':'3','b':'0'},
        '3': {'a':'3','b':'3'},
    },
    initial_state='0',
    final_states={'0','1','2'}
)

automate_fig_10_2_b = NFA(
    states={'0', '1', '2', '3', '4'},
    input_symbols={'a','b'},
    transitions={
        '0': {'b':'0','a':'1'},
        '1': {'a':'1','b':'2'},
        '2': {'a':'3','b':'0'},
        '3': {'a':'4','b':'1'},
        '4': {'a':'4','b':'4'},
    },
    initial_state='0',
    final_states={'0','1','2','3'}
)

automate_fig_10_2_c = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a':'2','b':'1'},
        '2': {'a':'3','b':'1'},
        '3': {'a':'3','b':'2'},
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_10_2_d = NFA(
    states={'1', '2', '3'},
    input_symbols={'a','b'},
    transitions={
        '1': {'a':'2','b':'3'},
        '2': {'a':'1','b':'3'},
        '3': {'a':'2','b':'1'},
    },
    initial_state='1',
    final_states={'3'}
)

automate_fig_73_a = NFA(
    states={'i', '0', '1', '2', '3', '4', '5', '6'},
    input_symbols={'a','b','ϵ'},
    transitions={
        'i': {'a':'4','b':'i','ϵ':'0'},
        '0': {'a':'1'},
        '1': {'b':'2'},
        '2': {'a':'3'},
        '3': {'a':'3','b':'3'},
        '4': {'b':'5'},
        '5': {'a':'4','b':'6'},
        '6': {'a':'6','b':'6'},
    },
    initial_state='i',
    final_states={'2','5'}
)

automate_fig_73_b = NFA(
    states={'0', '1', '2', '3', '4', '5'},
    input_symbols={'a','b','ϵ'},
    transitions={
        '0': {'a':'4','ϵ':'1'},
        '1': {'a':'2'},
        '2': {'b':'3'},
        '3': {'a':'3'},
        '4': {'b':'5'},
        '5': {'b':'5'},
    },
    initial_state='0',
    final_states={'2'}
)

automates = {
    name.replace("automate_", ""): value
    for name, value in globals().items()
    if name.startswith("automate_")
}

for nom,automate in automates.items():
    fig = automate.show_diagram() 
    fig.draw(f"{nom}.png", prog="dot")
    #fig.draw(f"{nom}.svg", prog="dot", format="svg")
    #fig.write(f"{nom}.dot")
    #Image(filename=f"{nom}.png")
    #"""
    img = mpimg.imread(f"{nom}.png")
    plt.figure(figsize=(8, 8))
    plt.imshow(img)
    plt.axis("off")
    plt.title(nom)
    #"""