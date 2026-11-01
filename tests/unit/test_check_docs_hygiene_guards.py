"""Synthetic probes for the docs and hygiene guards imported from BlueprintX (#295).

Each guard passes on the real tree, so only a deliberately broken tree proves it is not a
placebo. ``bin/`` is not a package, so the scripts are loaded by path.
"""

import importlib.util
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[2]


def _load(str_name: str):  # noqa: ANN202 - a dynamically loaded module has no static type
	"""Load ``bin/<str_name>.py`` as a module."""
	spec = importlib.util.spec_from_file_location(str_name, _ROOT / "bin" / f"{str_name}.py")
	assert spec is not None and spec.loader is not None
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


refs = _load("check_docs_code_refs")
gap = _load("check_docs_gap")
mask = _load("check_identifier_masking")


def _project(tmp_path: Path, str_doc: str) -> Path:
	"""Build a tiny project: one real package under src/ and one docs page."""
	(tmp_path / "src" / "pkg").mkdir(parents=True)
	(tmp_path / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
	(tmp_path / "src" / "pkg" / "real.py").write_text("def thing() -> None: ...\n", "utf-8")
	(tmp_path / "docs").mkdir()
	(tmp_path / "docs" / "index.md").write_text(str_doc, encoding="utf-8")
	return tmp_path


def test_docs_code_refs_accepts_a_real_import(tmp_path: Path) -> None:
	"""An import of a symbol that exists resolves cleanly."""
	path_root = _project(tmp_path, "```python\nfrom pkg.real import thing\n```\n")
	assert refs.main(["--root", str(path_root)]) == 0


def test_docs_code_refs_rejects_a_deleted_module(tmp_path: Path) -> None:
	"""A page citing a module that is gone fails."""
	path_root = _project(tmp_path, "```python\nfrom pkg.gone import thing\n```\n")
	assert refs.main(["--root", str(path_root)]) == 1


def test_docs_code_refs_rejects_a_renamed_symbol(tmp_path: Path) -> None:
	"""A page citing a name the module no longer defines fails."""
	path_root = _project(tmp_path, "```python\nfrom pkg.real import renamed\n```\n")
	assert refs.main(["--root", str(path_root)]) == 1


def test_docs_code_refs_honours_the_escape_hatch(tmp_path: Path) -> None:
	"""A reasoned ``docs-refs-ok`` marker exempts a deliberately wrong block."""
	str_doc = "<!-- docs-refs-ok: before example -->\n```python\nfrom pkg.gone import x\n```\n"
	path_root = _project(tmp_path, str_doc)
	assert refs.main(["--root", str(path_root)]) == 0


def _docs_tree(tmp_path: Path, list_nav: list[str], list_pages: list[str]) -> Path:
	"""Build a docs tree whose nav lists ``list_nav`` and whose disk holds ``list_pages``."""
	(tmp_path / "docs").mkdir()
	[(tmp_path / "docs" / str_page).write_text("# x\n", "utf-8") for str_page in list_pages]
	str_nav = "".join(f"  - P{i}: {p}\n" for i, p in enumerate(list_nav))
	(tmp_path / "mkdocs.yml").write_text(f"docs_dir: docs\nnav:\n{str_nav}", encoding="utf-8")
	return tmp_path


def test_docs_gap_accepts_a_fully_registered_tree(tmp_path: Path) -> None:
	"""Every published page in the nav is clean."""
	path_root = _docs_tree(tmp_path, ["index.md"], ["index.md"])
	assert gap.main(["--root", str(path_root)]) == 0


def test_docs_gap_rejects_an_orphan_page(tmp_path: Path) -> None:
	"""A page MkDocs builds but the nav omits fails."""
	path_root = _docs_tree(tmp_path, ["index.md"], ["index.md", "lost.md"])
	assert gap.main(["--root", str(path_root)]) == 1


def test_docs_gap_rejects_a_nav_over_the_ceiling(tmp_path: Path) -> None:
	"""More top-level nav entries than the ceiling fails."""
	list_pages = [f"p{i}.md" for i in range(gap.INT_NAV_TOP_LEVEL_CEILING + 1)]
	path_root = _docs_tree(tmp_path, list_pages, list_pages)
	assert gap.main(["--root", str(path_root)]) == 1


def test_docs_gap_fails_when_docs_is_missing(tmp_path: Path) -> None:
	"""Discovery collapsing to nothing must not read as clean."""
	(tmp_path / "mkdocs.yml").write_text("docs_dir: docs\nnav: []\n", encoding="utf-8")
	assert gap.main(["--root", str(tmp_path)]) == 1


@pytest.mark.parametrize(
	"str_line",
	[
		"query = \"SELECT 1 WHERE cnpj = '12.345.678/0001-95'\"\n",
		'ok = row.cpf == "123.456.789-01"\n',
		'frame.filter_by(cnpj="12.345.678/0001-95")\n',
	],
)
def test_identifier_masking_rejects_a_masked_literal(
	tmp_path: Path, str_line: str, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A masked CPF/CNPJ compared directly matches zero rows, so the gate fails."""
	(tmp_path / "src").mkdir()
	(tmp_path / "src" / "m.py").write_text(str_line, encoding="utf-8")
	monkeypatch.chdir(tmp_path)
	assert mask.main() == 1


def test_identifier_masking_accepts_an_unmasked_literal(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The unmasked form is what the column stores, so it is fine."""
	(tmp_path / "src").mkdir()
	(tmp_path / "src" / "m.py").write_text('ok = row.cnpj == "12345678000195"\n', "utf-8")
	monkeypatch.chdir(tmp_path)
	assert mask.main() == 0


def test_identifier_masking_honours_the_escape_hatch(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A reasoned ``identifier-mask-ok`` marker exempts the line."""
	(tmp_path / "src").mkdir()
	str_line = 'ok = row.cpf == "123.456.789-01"  # identifier-mask-ok: fixture\n'
	(tmp_path / "src" / "m.py").write_text(str_line, encoding="utf-8")
	monkeypatch.chdir(tmp_path)
	assert mask.main() == 0


def test_identifier_masking_rejects_a_bare_marker(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A marker with no reason is not a decision anyone made on purpose."""
	(tmp_path / "src").mkdir()
	str_line = 'ok = row.cpf == "123.456.789-01"  # identifier-mask-ok:\n'
	(tmp_path / "src" / "m.py").write_text(str_line, encoding="utf-8")
	monkeypatch.chdir(tmp_path)
	assert mask.main() == 1
