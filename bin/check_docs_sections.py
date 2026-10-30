"""Enforce the structural skeleton of ``docs/`` — never its prose.

Three invariants, all keyed on file slugs / configured labels, not on localized nav titles:

1. The canonical pages (``index, usage, api, faq, contributing, changelog``) exist and are
   registered in the ``mkdocs.yml`` ``nav:``.
2. Every published ``docs/**/*.md`` (i.e. not matched by ``exclude_docs``) is in the ``nav:``.
3. Each page of a declared family carries that family's required ``## `` sections. Pages that
   predate the rule sit on a named allowlist: a NEW page must comply, and an allowlisted page
   that becomes compliant FAILS until it is removed from the list (so the list only shrinks).

``mkdocs.yml`` is read as text (it carries ``!!python/name`` tags a safe YAML load rejects).
Every violation is a hard error (exit 1).
"""

import pathlib
import re
import sys


CANONICAL_SLUGS = ("index", "usage", "api", "faq", "contributing", "changelog")

# Family glob (relative to docs/) -> required level-2 headings. Labels are repo config (pt-BR,
# matching mkdocs.yml ``theme.language``). ``index.md`` is an overview, not a family member.
FAMILIES: dict[str, tuple[str, ...]] = {
	"ingestion/*.md": ("Descrição", "Tipagem", "Política de retry", "Exemplos"),
}
FAMILY_EXEMPT = frozenset({"ingestion/index.md"})

# Pages that predate the section rule. Remove a page once it complies (the gate forces it).
LEGACY_NONCOMPLIANT: frozenset[str] = frozenset(
	{
		"ingestion/adm_cart.md",
		"ingestion/adm_fii.md",
		"ingestion/agente_auton.md",
		"ingestion/agente_fiduc.md",
		"ingestion/auditor.md",
		"ingestion/cad_fi_hist.md",
		"ingestion/cadastro_fi.md",
		"ingestion/cda.md",
		"ingestion/cgvn_cia_aberta.md",
		"ingestion/cia_aberta_cad.md",
		"ingestion/cia_estrang.md",
		"ingestion/cia_incent.md",
		"ingestion/consultor_vlmob.md",
		"ingestion/contract_drift.md",
		"ingestion/coord_oferta.md",
		"ingestion/crowdfunding.md",
		"ingestion/dfin_fii.md",
		"ingestion/dfp_cia_aberta.md",
		"ingestion/eventual_fi.md",
		"ingestion/extrato_fi.md",
		"ingestion/fca_cia_aberta.md",
		"ingestion/fie.md",
		"ingestion/fre_cia_aberta.md",
		"ingestion/inf_anual_fii.md",
		"ingestion/inf_fip.md",
		"ingestion/inf_mensal_cra.md",
		"ingestion/inf_mensal_cri.md",
		"ingestion/inf_mensal_fiagro.md",
		"ingestion/inf_mensal_fidc.md",
		"ingestion/inf_mensal_fii.md",
		"ingestion/inf_mensal_ots.md",
		"ingestion/inf_trimestral_fii.md",
		"ingestion/informe_diario.md",
		"ingestion/intermed.md",
		"ingestion/invnr.md",
		"ingestion/ipe_cia_aberta.md",
		"ingestion/itr_cia_aberta.md",
		"ingestion/lamina.md",
		"ingestion/lamina_carteira.md",
		"ingestion/meta.md",
		"ingestion/oferta_distrib.md",
		"ingestion/perfil_mensal_fi.md",
		"ingestion/portal_completeness.md",
		"ingestion/recompra_acoes.md",
		"ingestion/registro.md",
		"ingestion/securit_cepac_flat.md",
		"ingestion/vlmo_cia_aberta.md",
	}
)

_NAV_PAGE = re.compile(r"""([\w./-]+\.md)['"]?\s*$""")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def _nav_pages(mkdocs_text: str) -> set[str]:
	"""Return every ``.md`` path listed under the top-level ``nav:`` key."""
	pages: set[str] = set()
	in_nav = False
	for line in mkdocs_text.splitlines():
		if line.startswith("nav:"):
			in_nav = True
			continue
		if in_nav and line and not line[0].isspace() and not line.startswith("#"):
			break
		# YAML comments begin at line start or after whitespace, never inside a path.
		line = re.sub(r"(^|\s)#.*$", "", line)
		if in_nav and (m := _NAV_PAGE.search(line)):
			pages.add(m.group(1))
	return pages


def _excluded(mkdocs_text: str) -> list[str]:
	"""Return the ``exclude_docs`` patterns (comments and blanks dropped)."""
	patterns: list[str] = []
	in_block = False
	for line in mkdocs_text.splitlines():
		if line.startswith("exclude_docs:"):
			in_block = True
			inline = line.partition(":")[2].strip().lstrip("|>+-").strip()
			if inline:
				patterns.append(inline)
			continue
		if in_block and line and not line[0].isspace():
			break
		if in_block and line.strip() and not line.strip().startswith("#"):
			patterns.append(line.strip())
	return patterns


def _is_excluded(rel: str, patterns: list[str]) -> bool:
	"""Whether MkDocs excludes a docs-relative path.

	Dot-files/dirs are excluded implicitly; patterns apply in order and the last match wins,
	so a later ``!pattern`` re-includes. Only the ``dir/`` and bare-name forms are handled (all
	this repo uses); ``check_docs`` rejects a wildcard pattern rather than misread it.
	"""
	excluded = any(part.startswith(".") for part in rel.split("/"))
	for pat in patterns:
		negate = pat.startswith("!")
		body = pat[1:] if negate else pat
		if body.endswith("/"):
			hit = rel.startswith(body) or f"/{body}" in f"/{rel}"
		else:
			hit = rel == body or rel.endswith(f"/{body}")
		if hit:
			excluded = not negate
	return excluded


def _headings(path: pathlib.Path) -> set[str]:
	"""Return the level-2 heading texts of a markdown file.

	Text that does not render as a heading is skipped: a fenced block, closed only by the same
	symbol at the same length (the ``pymdownx.superfences`` rule), and an HTML comment.
	"""
	found: set[str] = set()
	fence: str | None = None
	in_comment = False
	for line in path.read_text(encoding="utf-8").splitlines():
		if in_comment:
			in_comment = "-->" not in line
		elif fence:
			fence = None if line.strip() == fence else fence
		elif m := _FENCE.match(line):
			fence = m.group(1)
		elif line.startswith("## "):
			found.add(line[3:].strip())
		elif "<!--" in line:
			in_comment = "-->" not in line.rsplit("<!--", 1)[1]
	return found


def check_docs(docs_dir: pathlib.Path, mkdocs_text: str) -> list[str]:
	"""Return the list of violations for a docs tree (empty when clean)."""
	errors: list[str] = []
	nav = _nav_pages(mkdocs_text)
	patterns = _excluded(mkdocs_text)

	for pat in patterns:
		if set(pat) & set("*?["):
			errors.append(f"exclude_docs pattern {pat!r} uses a wildcard this gate cannot read")

	for slug in CANONICAL_SLUGS:
		if not (docs_dir / f"{slug}.md").is_file():
			errors.append(f"canonical page docs/{slug}.md is missing")
		if f"{slug}.md" not in nav:
			errors.append(f"canonical page {slug}.md is not registered in mkdocs.yml nav")

	for path in sorted(docs_dir.rglob("*.md")):
		rel = path.relative_to(docs_dir).as_posix()
		if not _is_excluded(rel, patterns) and rel not in nav:
			errors.append(f"docs/{rel} is published but missing from mkdocs.yml nav")

	for glob, required in FAMILIES.items():
		for path in sorted(docs_dir.glob(glob)):
			rel = path.relative_to(docs_dir).as_posix()
			if rel in FAMILY_EXEMPT:
				continue
			missing = [s for s in required if s not in _headings(path)]
			if missing and rel not in LEGACY_NONCOMPLIANT:
				errors.append(f"docs/{rel} lacks required section(s): {', '.join(missing)}")
			elif not missing and rel in LEGACY_NONCOMPLIANT:
				errors.append(f"docs/{rel} is now compliant: remove it from LEGACY_NONCOMPLIANT")
	return errors


def stale_allowlist(docs_dir: pathlib.Path) -> list[str]:
	"""Return an error for each ``LEGACY_NONCOMPLIANT`` entry whose page no longer exists."""
	return [
		f"docs/{rel} no longer exists: remove it from LEGACY_NONCOMPLIANT"
		for rel in sorted(LEGACY_NONCOMPLIANT)
		if not (docs_dir / rel).is_file()
	]


if __name__ == "__main__":
	docs = pathlib.Path("docs")
	problems = check_docs(docs, pathlib.Path("mkdocs.yml").read_text("utf-8"))
	problems += stale_allowlist(docs)
	for problem in problems:
		print(f"❌ {problem}")
	sys.exit(1 if problems else 0)
