import importlib.util

import pytest

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


def test_export_tikz_raises_not_implemented():
    dfa = make_simple_dfa()
    import pytest

    with pytest.raises(NotImplementedError):
        dfa.export_tikz()
