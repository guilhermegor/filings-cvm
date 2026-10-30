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

_NAV_PAGE = re.compile(r"([\w./-]+\.md)\s*$")


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
			continue
		if in_block and line and not line[0].isspace():
			break
		if in_block and line.strip() and not line.strip().startswith("#"):
			patterns.append(line.strip())
	return patterns


def _is_excluded(rel: str, patterns: list[str]) -> bool:
	"""Whether a docs-relative path matches an ``exclude_docs`` pattern (dir/ or filename)."""
	for pat in patterns:
		if pat.endswith("/"):
			if rel.startswith(pat) or f"/{pat}" in f"/{rel}":
				return True
		elif rel == pat or rel.endswith(f"/{pat}"):
			return True
	return False


def _headings(path: pathlib.Path) -> set[str]:
	"""Return the level-2 heading texts of a markdown file."""
	return {
		line[3:].strip()
		for line in path.read_text(encoding="utf-8").splitlines()
		if line.startswith("## ")
	}


def check_docs(docs_dir: pathlib.Path, mkdocs_text: str) -> list[str]:
	"""Return the list of violations for a docs tree (empty when clean)."""
	errors: list[str] = []
	nav = _nav_pages(mkdocs_text)
	patterns = _excluded(mkdocs_text)

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


if __name__ == "__main__":
	problems = check_docs(pathlib.Path("docs"), pathlib.Path("mkdocs.yml").read_text("utf-8"))
	for problem in problems:
		print(f"❌ {problem}")
	sys.exit(1 if problems else 0)
