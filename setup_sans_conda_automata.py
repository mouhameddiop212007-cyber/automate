"""
Script de setup pip-only (SANS conda) pour manim + automata-lib sous Windows,
avec téléchargement et installation automatique de Graphviz.

Depuis pygraphviz 2.0, PyPI fournit un wheel précompilé win_amd64 (pas de
compilation locale nécessaire). Il faut seulement que la bibliothèque C
Graphviz soit installée sur le système, car pygraphviz s'y lie dynamiquement
au runtime (DLL trouvées via le PATH). Ce script télécharge et installe
Graphviz silencieusement si besoin.

Utilisation :
    python setup_manim_automata_pip.py
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request

VENV_DIR = os.path.join(os.getcwd(), "automate-env-pip")

GRAPHVIZ_VERSION = "16.1.0"
GRAPHVIZ_INSTALL_DIR = r"C:\Program Files\Graphviz"
GRAPHVIZ_INSTALLER_URL = (
    "https://gitlab.com/api/v4/projects/4207231/packages/generic/"
    f"graphviz-releases/{GRAPHVIZ_VERSION}/"
    f"windows_10_cmake_Release_graphviz-install-{GRAPHVIZ_VERSION}-win64.exe"
)


def run(cmd, description, check=True):
    print(f"\n{'='*70}")
    print(f"ÉTAPE : {description}")
    print(f"Commande : {' '.join(cmd)}")
    print("=" * 70)
    result = subprocess.run(cmd, shell=False)
    if check and result.returncode != 0:
        print(f"\n❌ Échec à l'étape : {description}")
        print("Le script s'arrête ici. Corrigez l'erreur ci-dessus puis relancez.")
        sys.exit(1)
    print(f"✅ OK : {description}")
    return result.returncode == 0


def get_venv_python():
    return os.path.join(VENV_DIR, "Scripts", "python.exe")


def check_architecture():
    """pygraphviz ne fournit un wheel PyPI que pour win_amd64 (pas ARM64)."""
    machine = platform.machine()
    print(f"\nArchitecture détectée : {machine}")
    if machine.upper() not in ("AMD64", "X86_64"):
        print(f"⚠️  Attention : {machine} n'a pas de wheel pygraphviz précompilé sur")
        print("   PyPI (seul win_amd64 est disponible). L'installation pourrait")
        print("   nécessiter une compilation locale (Visual C++ Build Tools requis).")
        reponse = input("Continuer quand même ? [o/N] : ").strip().lower()
        if reponse != "o":
            sys.exit(1)
    else:
        print("✅ Architecture compatible avec le wheel précompilé pygraphviz (win_amd64).")


def ensure_graphviz_installed():
    """
    Télécharge et installe silencieusement Graphviz si son dossier bin
    n'est pas déjà présent. Retourne le dossier bin à ajouter au PATH.
    """
    bin_dir = os.path.join(GRAPHVIZ_INSTALL_DIR, "bin")
    dot_exe = os.path.join(bin_dir, "dot.exe")

    if os.path.isfile(dot_exe):
        print(f"\n✅ Graphviz déjà installé : {dot_exe}")
        return bin_dir

    print(f"\nGraphviz introuvable dans {GRAPHVIZ_INSTALL_DIR}, téléchargement en cours...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        installer_path = os.path.join(tmp_dir, "graphviz-install.exe")
        print(f"Téléchargement depuis : {GRAPHVIZ_INSTALLER_URL}")
        try:
            urllib.request.urlretrieve(GRAPHVIZ_INSTALLER_URL, installer_path)
        except Exception as e:
            print(f"\n❌ Échec du téléchargement de Graphviz : {e}")
            print("Télécharge-le manuellement ici : https://graphviz.org/download/")
            sys.exit(1)
        print("✅ Téléchargement terminé.")

        # Installateur NSIS : /S = silencieux, /D=<dir> doit être le DERNIER
        # argument, sans guillemets, chemin absolu.
        run(
            [installer_path, "/S", f"/D={GRAPHVIZ_INSTALL_DIR}"],
            f"Installation silencieuse de Graphviz {GRAPHVIZ_VERSION}",
        )

    if not os.path.isfile(dot_exe):
        print(f"\n❌ L'installation semble avoir échoué : {dot_exe} introuvable.")
        print("Installe Graphviz manuellement : https://graphviz.org/download/")
        sys.exit(1)

    print(f"✅ Graphviz installé avec succès : {dot_exe}")
    return bin_dir


def main():
    print("Setup pip-only (sans conda) pour manim + automata-lib + matplotlib")
    print(f"Environnement virtuel cible : {VENV_DIR}")

    check_architecture()
    graphviz_bin = ensure_graphviz_installed()

    # Étape 0 : proposer de supprimer l'ancien venv s'il existe déjà.
    # Un venv est un simple dossier (contrairement à un env conda enregistré
    # dans un registre global) : "existe déjà" se vérifie donc directement
    # sur le système de fichiers.
    if os.path.isdir(VENV_DIR):
        reponse = input(
            f"\nLe dossier '{VENV_DIR}' existe déjà. Le supprimer avant de "
            "recréer l'environnement ? [o/N] : "
        ).strip().lower()
        if reponse == "o":
            print(f"\nSuppression de {VENV_DIR}...")
            shutil.rmtree(VENV_DIR)
            print("✅ OK : ancien venv supprimé")
        else:
            print(
                "\n⚠️  Le venv existant sera réutilisé/mis à jour par "
                "'python -m venv' plutôt que recréé de zéro."
            )

    # Ajoute le bin de Graphviz au PATH de CE processus (et donc de tous les
    # sous-processus lancés ensuite, comme les vérifications d'import).
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")

    # Étape 1 : créer le venv
    run([sys.executable, "-m", "venv", VENV_DIR], f"Création du venv dans {VENV_DIR}")
    venv_python = get_venv_python()

    # Étape 2 : mettre à jour pip
    run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], "Mise à jour de pip")

    # Étape 3 : manim + av
    # Les wheels PyPI de `av` embarquent leur propre FFmpeg statique, donc
    # pas de conflit avec un FFmpeg système ou conda comme observé précédemment.
    run([venv_python, "-m", "pip", "install", "manim"], "Installation de manim")
    run([venv_python, "-m", "pip", "install", "av"], "Installation de av")

    # Étape 4 : automata-lib + coloraide + matplotlib
    run([venv_python, "-m", "pip", "install", "automata-lib"], "Installation de automata-lib")
    run([venv_python, "-m", "pip", "install", "coloraide"], "Installation de coloraide")
    run([venv_python, "-m", "pip", "install", "matplotlib"], "Installation de matplotlib")

    # Étape 5 : pygraphviz — wheel précompilé win_amd64 depuis pygraphviz 2.0,
    # pas de compilation locale. Graphviz doit juste être sur le PATH (fait
    # à l'étape ci-dessus).
    run([venv_python, "-m", "pip", "install", "pygraphviz"], "Installation de pygraphviz (wheel précompilé)")

    # Étape 6 : Jupyter, dans le même venv (pour un PATH cohérent).
    run(
        [venv_python, "-m", "pip", "install", "jupyterlab", "ipykernel"],
        "Installation de jupyterlab + ipykernel",
    )
    run(
        [
            venv_python, "-m", "ipykernel", "install", "--user",
            "--name", "automate-env-pip",
            "--display-name", "Python (automate-env-pip)",
        ],
        "Enregistrement du kernel Jupyter 'automate-env-pip'",
    )

    # Étape 7 : vérification
    verif_code = (
        "import manim; import automata.fa.dfa as dfa; import coloraide; "
        "import matplotlib; "
        "print('manim version :', manim.__version__); "
        "print('DFA importe avec succes :', dfa.DFA); "
        "print('coloraide OK'); "
        "print('matplotlib version :', matplotlib.__version__)"
    )
    run([venv_python, "-c", verif_code], "Vérification des imports de base")

    run(
        [venv_python, "-c", "import pygraphviz; print('pygraphviz OK')"],
        "Vérification de pygraphviz",
    )

    print("\n" + "=" * 70)
    print("🎉 Terminé ! Pour activer l'environnement :")
    print(f"   {VENV_DIR}\\Scripts\\activate")
    print("   jupyter lab")
    print(f"\n   (Interpréteur direct si besoin : {venv_python})")
    print("   Dans Jupyter, sélectionnez le kernel : Python (automate-env-pip)")
    print(f"\n   Graphviz installé dans : {GRAPHVIZ_INSTALL_DIR}")
    print("   Assure-toi que son dossier 'bin' est dans le PATH système")
    print("   (le script l'a ajouté pour cette session ; pour que ce soit")
    print("   permanent, ajoute-le via les Variables d'environnement Windows")
    print(f"   si ce n'est pas déjà fait : {graphviz_bin}")
    print("\n   Rappel : manim + pygraphviz importés dans le MÊME processus")
    print("   peuvent crasher au rendu (conflit natif observé précédemment).")
    print("   Utilise dot.exe en sous-processus pour le rendu des diagrammes :")
    print(f'   subprocess.run([r"{graphviz_bin}\\dot.exe", "-Tpng", ...])')
    print("=" * 70)


if __name__ == "__main__":
    main()
