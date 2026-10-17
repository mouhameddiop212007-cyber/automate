"""
Script de setup propre pour un environnement conda avec manim + automata-lib.

Objectif : éviter le conflit DLL de PyAV (`av`) sous Windows. Deux causes
distinctes ont été identifiées et corrigées ici :

1. Résolution des paquets en une seule commande `conda create`, avec
   `--override-channels -c conda-forge`. Installer d'abord juste Python
   puis ajouter les paquets dans un second `conda install` peut amener le
   solveur à piocher certaines dépendances transitives (codecs FFmpeg
   comme x264/x265/aom/opus) depuis les canaux `defaults` déjà configurés
   globalement, au lieu de conda-forge, ce qui peut en faire manquer
   certaines silencieusement.

2. Un fichier `sitecustomize.py` est déposé dans l'environnement pour
   précharger les DLL FFmpeg dans le bon ordre de dépendance dès le
   démarrage de Python. En effet, un kernel Jupyter est lancé directement
   via son `kernel.json` (juste `python.exe -m ipykernel_launcher`), sans
   passer par les scripts d'activation conda (`activate.d`) qui préparent
   normalement le PATH et l'ordre de résolution des DLL. Résultat observé :
   `import av` fonctionne parfaitement en ligne de commande après
   `conda activate`, mais échoue dans un notebook avec
   `ImportError: DLL load failed ... La procédure spécifiée est introuvable`
   sur `avcodec`/`avformat`/`avfilter`/`avdevice` — pas parce qu'une DLL
   manque, mais parce que leurs dépendances (x264, x265, aom, cairo, zlib...)
   ne sont pas chargées dans le bon ordre avant elles dans ce contexte.
   `sitecustomize.py` s'exécute automatiquement à chaque lancement de
   Python dans l'environnement (kernel Jupyter inclus), donc ce correctif
   s'applique sans rien changer à la façon dont Jupyter est lancé.

Utilisation :
    python setup_manim_automata.py

Prérequis : conda (ou miniconda/miniforge) doit être installé et accessible
depuis le terminal où vous lancez ce script.
"""

import os
import subprocess
import sys

ENV_NAME = "automate-env-clean"
PYTHON_VERSION = "3.11"

# Ordre de préchargement des DLL FFmpeg/codecs, déterminé empiriquement :
# les bibliothèques bas niveau d'abord, puis celles qui en dépendent, puis
# les libs FFmpeg elles-mêmes dans leur ordre de dépendance interne. Les
# noms de fichiers correspondent aux builds conda-forge win-64 actuels ; en
# cas de montée de version, `dir Library\bin\*.dll` permet de les ajuster.
DLL_PRELOAD_ORDER = [
    "zlib.dll", "libpng16.dll", "aom.dll", "libx264-164.dll", "libx265.dll",
    "opus.dll", "libmp3lame.DLL", "SvtAv1Enc.dll", "dav1d.dll", "openh264-7.dll",
    "glib-2.0-0.dll", "gobject-2.0-0.dll", "cairo.dll",
    "avutil-61.dll", "swresample-7.dll", "swscale-10.dll",
    "avcodec-63.dll", "avformat-63.dll", "avfilter-12.dll", "avdevice-63.dll",
]

SITECUSTOMIZE_TEMPLATE = '''"""
Genere automatiquement par setup_manim_automata.py.

Precharge les DLL FFmpeg/codecs dans le bon ordre de dependance des le
demarrage de Python dans cet environnement. Necessaire car un kernel
Jupyter ne passe pas par les scripts d'activation conda (activate.d) qui
preparent normalement le PATH et l'ordre de resolution des DLL sous
Windows -- sans ce prechargement, `import av` peut echouer avec
"ImportError: DLL load failed ... La procedure specifiee est introuvable"
dans un notebook, alors que la meme commande fonctionne en ligne de
commande apres `conda activate`.
"""

import os
import sys

if sys.platform.startswith("win"):
    _library_bin = os.path.join(sys.prefix, "Library", "bin")
    if os.path.isdir(_library_bin):
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(_library_bin)

        _preload_order = {preload_order!r}

        import ctypes
        for _dll in _preload_order:
            _path = os.path.join(_library_bin, _dll)
            if os.path.exists(_path):
                try:
                    ctypes.WinDLL(_path)
                except OSError:
                    # Non bloquant : si une DLL de la liste n'est plus
                    # necessaire ou a change de nom entre deux versions de
                    # ffmpeg/manim, on continue plutot que de faire
                    # planter le demarrage de Python dans son ensemble.
                    pass
'''


def get_env_python(conda_base, env_name):
    """
    Retourne le chemin direct vers l'exécutable Python de l'environnement.
    Sous Windows, `conda run` peut parfois invoquer le mauvais interpréteur
    (bug connu lié au PATH) : appeler python.exe directement est plus fiable.
    """
    candidate = os.path.join(conda_base, "envs", env_name, "python.exe")
    if os.path.exists(candidate):
        return candidate
    # Fallback pour Linux/Mac (pas de .exe)
    candidate = os.path.join(conda_base, "envs", env_name, "bin", "python")
    if os.path.exists(candidate):
        return candidate
    return None


def get_conda_base():
    """Récupère le répertoire de base de l'installation conda active."""
    result = subprocess.run(
        ["conda", "info", "--base"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def get_site_packages(env_python):
    """
    Demande à l'interpréteur de l'environnement lui-même où se trouve son
    dossier site-packages (plus fiable que de reconstruire le chemin à la
    main, qui varie selon l'OS et la version de Python).
    """
    result = subprocess.run(
        [env_python, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def run(cmd, description):
    """Exécute une commande shell et affiche le résultat en direct."""
    print(f"\n{'='*70}")
    print(f"ÉTAPE : {description}")
    print(f"Commande : {' '.join(cmd)}")
    print("=" * 70)
    result = subprocess.run(cmd, shell=False)
    if result.returncode != 0:
        print(f"\n❌ Échec à l'étape : {description}")
        print("Le script s'arrête ici. Corrigez l'erreur ci-dessus puis relancez.")
        sys.exit(1)
    print(f"✅ OK : {description}")


def main():
    print(f"Création d'un environnement conda propre : {ENV_NAME}")
    print("Ce script va :")
    print("  1. Supprimer l'ancien environnement s'il existe (optionnel, demandé)")
    print("  2. Créer l'environnement ET installer tous les paquets (dont")
    print("     matplotlib) en UNE SEULE résolution conda-forge (pas de")
    print("     mélange avec les canaux 'defaults')")
    print("  3. Installer automata-lib via pip (pur Python, pas de soucis)")
    print("  4. Installer Jupyter + déposer un sitecustomize.py qui précharge")
    print("     les DLL FFmpeg dans le bon ordre (nécessaire pour les kernels)")
    print("  5. Vérifier que tout s'importe correctement, y compris dans des")
    print("     conditions proches d'un kernel Jupyter")

    # Étape 0 : proposer de supprimer l'ancien env
    reponse = input(
        f"\nSupprimer l'environnement conda '{ENV_NAME}' s'il existe déjà ? [o/N] : "
    ).strip().lower()
    if reponse == "o":
        run(
            ["conda", "env", "remove", "-n", ENV_NAME, "-y"],
            f"Suppression de l'environnement existant '{ENV_NAME}'",
        )

    # Étape 1 : créer l'environnement ET installer tous les paquets en une
    # seule commande `conda create`, avec `--override-channels -c conda-forge`.
    #
    # Pourquoi une seule commande plutôt que create-puis-install : si votre
    # configuration conda globale (.condarc) inclut aussi les canaux
    # `defaults` (repo.anaconda.com), un `conda install` fait APRÈS coup
    # peut résoudre certaines dépendances transitives des paquets demandés
    # (par exemple des codecs FFmpeg comme x264/x265/aom/opus, qui ne sont
    # pas demandés explicitement mais requis par `ffmpeg`) depuis un canal
    # incohérent avec le reste, voire les omettre silencieusement. Une
    # résolution atomique avec `--override-channels -c conda-forge` force
    # TOUT le graphe de dépendances, y compris les transitives, à venir du
    # même canal cohérent.
    run(
        [
            "conda", "create", "-n", ENV_NAME,
            "-c", "conda-forge", "--override-channels",
            f"python={PYTHON_VERSION}",
            "matplotlib", "manim", "av", "ffmpeg", "pygraphviz", "coloraide", "-y",
        ],
        f"Création de '{ENV_NAME}' + installation matplotlib/manim/av/ffmpeg/"
        f"pygraphviz/coloraide (résolution atomique conda-forge)",
    )

    # Résolution du chemin direct vers l'interpréteur Python de l'env.
    # On l'utilise pour les étapes suivantes au lieu de `conda run`, qui
    # peut invoquer le mauvais python.exe sous Windows (bug connu).
    conda_base = get_conda_base()
    env_python = get_env_python(conda_base, ENV_NAME)
    if env_python is None:
        print(f"\n❌ Impossible de trouver python.exe pour l'environnement '{ENV_NAME}'.")
        print(f"   Cherché dans : {conda_base}\\envs\\{ENV_NAME}\\")
        sys.exit(1)
    print(f"\nInterpréteur Python de l'environnement détecté : {env_python}")

    # Étape 3 : installer automata-lib via pip, en appelant le pip
    # associé à cet interpréteur précis (python -m pip, pas conda run).
    run(
        [env_python, "-m", "pip", "install", "automata-lib"],
        "Installation de automata-lib (pip, pur Python)",
    )

    # Étape 4 : installer Jupyter DANS cet environnement (et pas juste un
    # kernel pointant dessus). Si Jupyter est lancé depuis un autre env
    # (ex: base), le PATH hérité par le processus kernel peut contenir un
    # autre Library\bin avec des DLL FFmpeg d'une version différente, ce
    # qui provoque exactement l'erreur "DLL load failed" sur `av`, même si
    # les paquets sont correctement installés. Avoir Jupyter dans le même
    # env garantit un PATH cohérent au lancement.
    run(
        [env_python, "-m", "pip", "install", "jupyterlab", "ipykernel"],
        "Installation de jupyterlab + ipykernel (dans l'env, pour un PATH cohérent)",
    )
    run(
        [
            env_python, "-m", "ipykernel", "install", "--user",
            "--name", ENV_NAME,
            "--display-name", f"Python ({ENV_NAME})",
        ],
        f"Enregistrement du kernel Jupyter '{ENV_NAME}'",
    )

    # Étape 4bis (Windows uniquement) : déposer un sitecustomize.py qui
    # précharge les DLL FFmpeg dans le bon ordre à chaque démarrage de
    # Python dans cet environnement.
    #
    # Pourquoi c'est nécessaire même après l'étape 1 : un kernel Jupyter
    # est lancé directement via son kernel.json (juste
    # `python.exe -m ipykernel_launcher`), sans passer par les scripts
    # d'activation conda (activate.d) qui préparent normalement le PATH.
    # Résultat observé en pratique : `import av` fonctionne parfaitement
    # en ligne de commande après `conda activate`, mais échoue dans un
    # notebook avec "DLL load failed ... La procédure spécifiée est
    # introuvable" sur avcodec/avformat/avfilter/avdevice — leurs
    # dépendances (x264, x265, aom, cairo, zlib...) existent bien mais ne
    # sont pas chargées dans le bon ordre avant elles dans ce contexte.
    # sitecustomize.py s'exécute automatiquement à l'interpréteur, donc ce
    # correctif s'applique quelle que soit la façon dont Jupyter est lancé
    # par la suite, sans rien à changer dans les notebooks eux-mêmes.
    if sys.platform.startswith("win"):
        site_packages = get_site_packages(env_python)
        sitecustomize_path = os.path.join(site_packages, "sitecustomize.py")
        sitecustomize_content = SITECUSTOMIZE_TEMPLATE.format(
            preload_order=DLL_PRELOAD_ORDER
        )
        with open(sitecustomize_path, "w", encoding="utf-8") as f:
            f.write(sitecustomize_content)
        print(f"\n✅ OK : sitecustomize.py écrit dans {sitecustomize_path}")

    # Étape 5 : vérification finale.
    # On lance ce test avec `subprocess.run` depuis CE script Python (donc
    # sans hériter d'un terminal où `conda activate` aurait déjà préparé le
    # PATH), pour se rapprocher des conditions réelles d'un kernel Jupyter
    # plutôt que de valider uniquement le cas le plus favorable.
    verif_code = (
        "import manim; import automata.fa.dfa as dfa; "
        "import pygraphviz; import coloraide; import matplotlib; "
        "print('manim version :', manim.__version__); "
        "print('DFA importe avec succes :', dfa.DFA); "
        "print('pygraphviz et coloraide OK'); "
        "print('matplotlib version :', matplotlib.__version__)"
    )
    run(
        [env_python, "-c", verif_code],
        "Vérification des imports (manim + automata.fa.dfa), sans activation préalable",
    )

    print("\n" + "=" * 70)
    print("🎉 Terminé !")
    print(f"   conda activate {ENV_NAME}")
    print(f"   jupyter notebook   (ou jupyter lab)")
    print(f"\n   Dans Jupyter, sélectionnez le kernel : Python ({ENV_NAME})")
    print(f"   (Interpréteur direct si besoin : {env_python})")
    if sys.platform.startswith("win"):
        print(
            "\n   Le préchargement des DLL FFmpeg (sitecustomize.py) est actif :"
            "\n   `import av` doit maintenant fonctionner aussi bien dans un"
            "\n   notebook qu'en ligne de commande, même si Jupyter est lancé"
            "\n   sans passer explicitement par `conda activate` au préalable."
        )
    env_root = os.path.dirname(env_python)
    dot_exe = os.path.join(env_root, "Library", "bin", "dot.exe")
    print("\n   Rappel : manim + pygraphviz importés dans le MÊME processus")
    print("   peuvent crasher au rendu (conflit natif observé précédemment).")
    print("   Utilise dot.exe en sous-processus pour le rendu des diagrammes :")
    print(f'   subprocess.run([r"{dot_exe}", "-Tpng", ...])')
    print("=" * 70)


if __name__ == "__main__":
    main()
