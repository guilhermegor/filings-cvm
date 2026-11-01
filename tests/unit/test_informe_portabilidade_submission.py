"""Unit tests for the Informe de Portabilidade submission writer.

The expected tag lists are typed from PadraoXMLInfoPortabilidade.asp, not derived from the
code under test.
"""

import contextlib
from pathlib import Path
import re

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformePortabilidade,
	InformePortabilidadeDocument,
	PortabilidadeHeader,
	PortabilidadeInform,
)


VALID_CNPJ = "11222333000181"
MASKED_CNPJ = "11.222.333/0001-81"

# Typed from the spec page, in page order.
HEADER_TAGS = ["COD_DOC", "VERSAO", "DT_COMPT", "DT_GERAC_ARQ"]
INFORM_TAGS = [
	"CNPJ_PARTIC",
	"DT_EVENT",
	"QTDE_SOLICIT_ORIG",
	"QTDE_SOLICIT_DEST",
	"QTDE_CANC",
	"ATEND_PRAZO_REGUL",
	"ATEND_PRAZO_ESTEND",
	"QTDE_RECUS",
]


def _inform(**overrides: object) -> PortabilidadeInform:
	"""Build a valid INFORM block, overridden per test."""
	fields: dict[str, object] = {
		"cnpj_partic": VALID_CNPJ,
		"dt_event": "09/2026",
		"qtde_solicit_orig": 10,
		"qtde_solicit_dest": 20,
		"qtde_canc": 3,
		"atend_prazo_regul": 15,
		"atend_prazo_estend": 4,
		"qtde_recus": 8,
	}
	fields.update(overrides)
	return PortabilidadeInform(**fields)


def _header(**overrides: object) -> PortabilidadeHeader:
	"""Build a valid header."""
	fields: dict[str, object] = {"dt_compt": "09/2026", "dt_gerac_arq": "05/10/2026"}
	fields.update(overrides)
	return PortabilidadeHeader(**fields)


def _doc(*informs: PortabilidadeInform) -> InformePortabilidadeDocument:
	"""Wrap informs in a document with a valid header."""
	return InformePortabilidadeDocument(header=_header(), informs=list(informs) or [_inform()])


def _tags(xml: str, block: str) -> list[str]:
	"""Child tag names of the first ``block`` element."""
	body = re.search(rf"<{block}>(.*?)</{block}>", xml, re.S)
	assert body is not None
	return re.findall(r"<([A-Z_]+)>", body.group(1))


def test_export_header_block_tags_match_spec() -> None:
	"""Export header block tags match spec."""
	assert _tags(InformePortabilidade().export(_doc()), "CAB_INFORM") == HEADER_TAGS


@pytest.mark.parametrize(
	"fragment",
	[
		"<COD_DOC>478</COD_DOC>",
		"<VERSAO>1.0</VERSAO>",
		"<DT_COMPT>09/2026</DT_COMPT>",
		"<DT_GERAC_ARQ>05/10/2026</DT_GERAC_ARQ>",
	],
)
def test_export_header_block_carries_value(fragment: str) -> None:
	"""Export header block carries each constant and date."""
	assert fragment in InformePortabilidade().export(_doc())


def test_export_inform_block_tags_match_spec() -> None:
	"""Export inform block tags match spec."""
	assert _tags(InformePortabilidade().export(_doc()), "INFORM") == INFORM_TAGS


@pytest.mark.parametrize(
	"fragment",
	[
		f"<CNPJ_PARTIC>{VALID_CNPJ}</CNPJ_PARTIC>",
		"<DT_EVENT>09/2026</DT_EVENT>",
		"<QTDE_SOLICIT_ORIG>10</QTDE_SOLICIT_ORIG>",
		"<QTDE_SOLICIT_DEST>20</QTDE_SOLICIT_DEST>",
		"<QTDE_CANC>3</QTDE_CANC>",
		"<ATEND_PRAZO_REGUL>15</ATEND_PRAZO_REGUL>",
		"<ATEND_PRAZO_ESTEND>4</ATEND_PRAZO_ESTEND>",
		"<QTDE_RECUS>8</QTDE_RECUS>",
	],
)
def test_export_inform_block_carries_value(fragment: str) -> None:
	"""Export inform block carries each value."""
	assert fragment in InformePortabilidade().export(_doc())


def test_export_declaration_is_windows_1252() -> None:
	"""Export declaration is windows 1252."""
	xml = InformePortabilidade().export(_doc())
	assert xml.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')


def test_export_root_carries_namespace() -> None:
	"""Export root carries namespace."""
	assert '<DOC_ARQ xmlns="urn:portab">' in InformePortabilidade().export(_doc())


def test_export_one_inform_per_entry() -> None:
	"""Export one inform per entry."""
	other = _inform(cnpj_partic="00000000000191", dt_event="08/2026")
	assert InformePortabilidade().export(_doc(_inform(), other)).count("<INFORM>") == 2


def test_export_informs_keep_entry_order() -> None:
	"""Export informs keep entry order."""
	other = _inform(cnpj_partic="00000000000191", dt_event="08/2026")
	xml = InformePortabilidade().export(_doc(_inform(), other))
	assert xml.index(VALID_CNPJ) < xml.index("00000000000191")


def test_export_masked_cnpj_is_written_bare() -> None:
	"""Export masked cnpj is written bare."""
	xml = InformePortabilidade().export(_doc(_inform(cnpj_partic=MASKED_CNPJ)))
	assert f"<CNPJ_PARTIC>{VALID_CNPJ}</CNPJ_PARTIC>" in xml


def test_export_zero_counts_are_kept() -> None:
	"""Export zero counts are kept."""
	xml = InformePortabilidade().export(_doc(_inform(qtde_canc=0)))
	assert "<QTDE_CANC>0</QTDE_CANC>" in xml


def test_export_to_file_returns_none(tmp_path: Path) -> None:
	"""Export to file returns none."""
	assert InformePortabilidade().export(_doc(), output_path=str(tmp_path / "out.xml")) is None


def test_export_file_is_windows_1252(tmp_path: Path) -> None:
	"""Export file is windows 1252."""
	target = tmp_path / "out.xml"
	InformePortabilidade().export(_doc(), output_path=str(target))
	assert target.read_bytes().startswith(b'<?xml version="1.0" encoding="windows-1252"?>')


def _unencodable_doc() -> InformePortabilidadeDocument:
	"""Document built past validation holding text windows-1252 cannot encode."""
	return InformePortabilidadeDocument.model_construct(
		header=PortabilidadeHeader.model_construct(
			cod_doc=478, versao="1.0", dt_compt="09/2026", dt_gerac_arq="中"
		),
		informs=[_inform()],
	)


def test_export_unencodable_text_raises(tmp_path: Path) -> None:
	"""Export unencodable text raises."""
	with pytest.raises(ValueError, match="cannot be serialised"):
		InformePortabilidade().export(_unencodable_doc(), output_path=str(tmp_path / "out.xml"))


def test_export_unencodable_text_leaves_existing_file_intact(tmp_path: Path) -> None:
	"""Export unencodable text leaves existing file intact."""
	target = tmp_path / "out.xml"
	target.write_bytes(b"previous")
	with contextlib.suppress(ValueError):
		InformePortabilidade().export(_unencodable_doc(), output_path=str(target))
	assert target.read_bytes() == b"previous"


@pytest.mark.parametrize(
	"value", ["13/2026", "00/2026", "9/2026", "09/26", "09/1800", "09/2026\n", "٠٩/2026"]
)
def test_header_dt_compt_rejects_bad_month(value: str) -> None:
	"""Header dt compt rejects bad month."""
	with pytest.raises(ValidationError):
		_header(dt_compt=value)


@pytest.mark.parametrize(
	"value", ["31/02/2026", "5/10/2026", "05/10/1800", "05/10/2026\n", "2026-10-05"]
)
def test_header_dt_gerac_arq_rejects_impossible_or_malformed_date(value: str) -> None:
	"""Header dt gerac arq rejects impossible or malformed date."""
	with pytest.raises(ValidationError):
		_header(dt_gerac_arq=value)


@pytest.mark.parametrize(("field", "value"), [("cod_doc", 1), ("versao", "2.0")])
def test_header_rejects_wrong_doc_code_and_version(field: str, value: object) -> None:
	"""Header rejects wrong doc code and version."""
	with pytest.raises(ValidationError):
		_header(**{field: value})


@pytest.mark.parametrize("value", ["13/2026", "9/2026", "09/2026\n"])
def test_inform_dt_event_rejects_bad_month(value: str) -> None:
	"""Inform dt event rejects bad month."""
	with pytest.raises(ValidationError):
		_inform(dt_event=value)


@pytest.mark.parametrize(
	"value",
	["11222333000182", "1122233300018", "11222333000181\n", "11.222.333/0001-8", "abc", ""],
)
def test_inform_rejects_bad_cnpj(value: str) -> None:
	"""Inform rejects bad cnpj."""
	with pytest.raises(ValidationError):
		_inform(cnpj_partic=value)


@pytest.mark.parametrize(
	"field",
	[
		"qtde_solicit_orig",
		"qtde_solicit_dest",
		"qtde_canc",
		"atend_prazo_regul",
		"atend_prazo_estend",
		"qtde_recus",
	],
)
@pytest.mark.parametrize("value", [-1, 1.5, 2.0, "5", True, None])
def test_inform_counts_reject_negative_float_str_bool_none(field: str, value: object) -> None:
	"""Inform counts reject negative float str bool none."""
	with pytest.raises(ValidationError):
		_inform(**{field: value})


def test_inform_missing_field_is_rejected() -> None:
	"""Inform missing field is rejected."""
	with pytest.raises(ValidationError):
		PortabilidadeInform(cnpj_partic=VALID_CNPJ, dt_event="09/2026")


def test_document_requires_at_least_one_inform() -> None:
	"""Document requires at least one inform."""
	with pytest.raises(ValidationError):
		InformePortabilidadeDocument(header=_header(), informs=[])


@pytest.mark.parametrize(
	("make", "field", "value"),
	[
		(_inform, "qtde_canc", -1),
		(_inform, "dt_event", "13/2026"),
		(_inform, "cnpj_partic", "11222333000182"),
		(_header, "dt_compt", "0/2026"),
		(_header, "dt_gerac_arq", "31/02/2026"),
	],
)
def test_models_reject_invalid_assignment(make: object, field: str, value: object) -> None:
	"""Assigning an invalid value after construction is refused like at construction."""
	model = make()
	with pytest.raises(ValidationError):
		setattr(model, field, value)
