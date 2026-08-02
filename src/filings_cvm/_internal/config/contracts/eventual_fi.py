"""Data contract for the CVM open-data *EVENTUAL FI* CSV (ingestion).

``eventual_fi_AAAA.csv`` (dataset ``FI/DOC/EVENTUAL``) is the **index of the eventual documents** a
fund or class delivered in a year — one row per delivered document, carrying the fund's identity,
the reference and delivery dates, the document type, and a ``LINK_ARQ`` pointing at the file
itself. It is not the document. Verified against the real ``2025`` file (186.453 rows): the eleven
columns below are exactly as published, in order, and pinned verbatim to
``tests/fixtures/eventual_fi/eventual_fi_header.csv``.

⚠️ **It shares its shape with `DFIN_FII` and not one column name.** Both are yearly plain-CSV
indexes of documents delivered by a fund, and seven of their columns mean the same thing — yet DFIN
spells them ``Tipo_Fundo_Classe`` / ``CNPJ_Fundo_Classe`` / ``Data_Referencia`` / ``Link_Download``
while this one spells them ``TP_FUNDO_CLASSE`` / ``CNPJ_FUNDO_CLASSE`` / ``DT_COMPTC`` /
``LINK_ARQ``. Semantic parallelism is **not** a naming rule anywhere in this portal, so the column
list comes from this dataset's own header.

⚠️ **``ID_DOC`` is declared ``int`` by the dataset's META and is still typed as text**, like every
other identifier here — an identifier is not a quantity, and a numeric type would silently drop a
leading zero (measured on the CGVN's ``Codigo_CVM``, which arrives as ``001023``).

⚠️ **Four columns arrive partially empty in 2025** — ``ID_SUBCLASSE`` (96,8%),
``RESULTADO_AUDITORIA`` (83,5%), ``ID_DOC`` (75,6%) and ``NM_ARQ`` (24,4%). Emptiness is a property
of the year and of the document type, not of the schema: a row describing a link-only filing has no
file name, and only an audited document carries an opinion.

Naming follows the **post-RCVM 175** split (``TP_FUNDO_CLASSE`` / ``CNPJ_FUNDO_CLASSE`` plus
``ID_SUBCLASSE``), like FIAGRO and FIE — not the pre-175 ``CNPJ_FUNDO`` used by this root's older
datasets.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
EVENTUAL_FI = FileContract(
	"EVENTUAL FI — índice dos documentos eventuais",
	"eventual_fi",
	(
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"DENOM_SOCIAL",
		"ID_SUBCLASSE",
		"DT_COMPTC",
		"DT_RECEB",
		"TP_DOC",
		"NM_ARQ",
		"ID_DOC",
		"LINK_ARQ",
		"RESULTADO_AUDITORIA",
	),
	("CNPJ_FUNDO_CLASSE",),
)
