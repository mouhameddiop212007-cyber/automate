import importlib.util
import shutil
import subprocess

import pytest

from automata_extensions.fa.dfa import ExtendedDFA
from automata_extensions.fa.nfa import ExtendedNFA
from tests.conftest import make_simple_dfa

needs_graphviz = pytest.mark.skipif(
    importlib.util.find_spec("pygraphviz") is None
    or importlib.util.find_spec("coloraide") is None,
    reason="pygraphviz et coloraide requis (pip install .[visual])",
)


@needs_graphviz
def test_export_dot_returns_nonempty_string():
    dfa = make_simple_dfa()
    dot_source = dfa.export_dot()
    assert isinstance(dot_source, str)
    assert len(dot_source) > 0
    assert "digraph" in dot_source or "->" in dot_source


@needs_graphviz
def test_export_svg_creates_file(tmp_path):
    dfa = make_simple_dfa()
    filename = str(tmp_path / "automate.svg")
    result = dfa.export_svg(filename)
    assert result == filename
    assert (tmp_path / "automate.svg").exists()


@needs_graphviz
def test_export_pdf_creates_file(tmp_path):
    dfa = make_simple_dfa()
    filename = str(tmp_path / "automate.pdf")
    result = dfa.export_pdf(filename)
    assert result == filename
    assert (tmp_path / "automate.pdf").exists()


def even_a():
    """Nombre pair de 'a'."""
    return ExtendedDFA(
        states={"p", "i"},
        input_symbols={"a", "b"},
        transitions={
            "p": {"a": "i", "b": "p"},
            "i": {"a": "p", "b": "i"},
        },
        initial_state="p",
        final_states={"p"},
    )


def test_export_tikz_declares_states():
    lines = even_a().export_tikz().splitlines()
    assert r"  \node[state, initial, accepting] (q0) at (0,0) {p};" in lines
    assert r"  \node[state] (q1) at (3,0) {i};" in lines


def test_export_tikz_draws_loops_and_bent_edges():
    lines = even_a().export_tikz().splitlines()
    assert r"  \path (q0) edge[loop above] node {b} (q0);" in lines
    assert r"  \path (q0) edge[bend left] node {a} (q1);" in lines
    assert r"  \path (q1) edge[bend left] node {a} (q0);" in lines
    assert r"  \path (q1) edge[loop above] node {b} (q1);" in lines


def test_export_tikz_is_a_closed_environment():
    code = even_a().export_tikz()
    assert code.startswith("% Requires")
    assert r"\begin{tikzpicture}" in code
    assert code.endswith("\\end{tikzpicture}\n")


def test_export_tikz_merges_parallel_labels():
    dfa = ExtendedDFA(
        states={"p"},
        input_symbols={"a", "b"},
        transitions={"p": {"a": "p", "b": "p"}},
        initial_state="p",
        final_states={"p"},
    )
    assert r"\path (q0) edge[loop above] node {a, b} (q0);" in (
        dfa.export_tikz()
    )


def test_export_tikz_writes_epsilon_as_varepsilon():
    nfa = ExtendedNFA(
        states={"q0", "q1"},
        input_symbols={"a"},
        transitions={"q0": {"": {"q1"}}, "q1": {}},
        initial_state="q0",
        final_states={"q1"},
    )
    assert r"\path (q0) edge node {$\varepsilon$} (q1);" in nfa.export_tikz()


def test_export_tikz_escapes_latex_special_characters():
    dfa = ExtendedDFA(
        states={"a_b", "{x}"},
        input_symbols={"a"},
        transitions={"a_b": {"a": "{x}"}, "{x}": {"a": "{x}"}},
        initial_state="a_b",
        final_states={"{x}"},
    )
    code = dfa.export_tikz()
    assert r"{a\_b};" in code
    assert r"{\{x\}};" in code


def test_export_tikz_standalone_is_a_full_document():
    code = even_a().export_tikz(standalone=True)
    assert code.startswith("\\documentclass")
    assert "\\usetikzlibrary{automata}" in code
    assert code.endswith("\\end{document}\n")


def test_export_tikz_writes_file_and_places_unreachable_states_last(
    tmp_path,
):
    dfa = ExtendedDFA(
        states={"p", "z"},
        input_symbols={"a"},
        transitions={"p": {"a": "p"}, "z": {"a": "z"}},
        initial_state="p",
        final_states={"p"},
    )
    target = tmp_path / "automate.tex"
    code = dfa.export_tikz(str(target))
    assert target.read_text(encoding="utf-8") == code
    assert r"(q1) at (3,0) {z};" in code


def test_export_tikz_avoids_obsolete_arrow_tip_syntax():
    assert "stealth'" not in even_a().export_tikz()


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex requis")
def test_export_tikz_standalone_compiles_with_pdflatex(tmp_path):
    source = tmp_path / "automate.tex"
    even_a().export_tikz(str(source), standalone=True)
    result = subprocess.run(
        [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            source.name,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-800:]
    assert (tmp_path / "automate.pdf").exists()
