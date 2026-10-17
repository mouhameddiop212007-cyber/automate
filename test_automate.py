import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from automata_extensions.fa.dfa import ExtendedDFA

# ---- REMPLACE CE BLOC PAR TON AUTOMATE MODIFIÉ ----
automate = ExtendedDFA(
    states={'q0', 'q1', 'q2', 'q3'},
    input_symbols={'a', 'b'},
    transitions={
        'q0': {'a': 'q1', 'b': 'q2'},
        'q1': {'a': 'q3', 'b': 'q3'},
        'q2': {'a': 'q3', 'b': 'q3'},
        'q3': {'a': 'q3', 'b': 'q3'},
    },
    initial_state='q0',
    final_states={'q3'},
)
# ---------------------------------------------------

mini = automate.minimize()

print("Original :", len(automate.states), "états")
print("Minimal  :", len(mini.states), "états")

# Génère les deux images
automate.show_diagram().draw("original.png", prog="dot")
mini.show_diagram().draw("minimal.png", prog="dot")

# Une seule figure avec deux sous-graphiques
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].imshow(mpimg.imread("original.png"))
axes[0].set_title(f"Automate non minimal ({len(automate.states)} états)")
axes[0].axis("off")

axes[1].imshow(mpimg.imread("minimal.png"))
axes[1].set_title(f"Automate minimisé ({len(mini.states)} états)")
axes[1].axis("off")

plt.tight_layout()
plt.savefig("comparaison.png", dpi=150)
plt.show()

