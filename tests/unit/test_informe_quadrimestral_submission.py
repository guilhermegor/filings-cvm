"""Unit tests for the Informe Quadrimestral V2 submission writer.

The expected tag lists are typed from the CVM page's sample file, not derived from the models,
so a field declared out of order or under the wrong name fails here.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError
import pytest

from filings_cvm.submission import (
	InformeQuadrimestral,
	InformeQuadrimestralDocument,
	InformeQuadrimestralHeader,
)


NS = "{urn:inftrim}"
VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"

HEADER_TAGS = ["COD_DOC", "DT_COMPT", "DT_GERAC_ARQ", "VERSAO"]
INFORM_TAGS = [
	"NR_PF_PJ_FDO",
	"ENTID_INVEST",
	"PUBLICO_ALVO",
	"VL_PL_FDO",
	"VL_CAPITAL_COMPROM",
	"QTD_COTAS_SUBSCR",
	"VL_TOT_CAPITAL_SUBSCR",
	"QTD_COTAS_INTEGR",
	"VL_TOT_CAPITAL_INTEGR",
	"VL_TOT_COTAS_OUTROS_FIP",
	"LISTA_COTST_CATEG",
	"LISTA_CLASSE_COTAS",
]
LISTA_CATEG_TAGS = ["COTST_CATEG", "TOT_COTST_SUBSCR", "TX_NUM_TOT_COT"]
CATEG_TAGS = ["COD_CATEG", "QTD_COTST_SUBSCR", "PR_COTAS_SUBSCR"]
CLASSE_TAGS = [
	"NUM_CLASSE",
	"NUM_COTST_SUBS",
	"QTD_ATUAL_COTAS_SUBS",
	"QTD_ATUAL_COTAS_INTEG",
	"VL_ATUAL_COTA",
	"DIREITO_POLIT_ESPECIAL",
	"DIREITO_DIST_ECON_FINAN",
]


def _inform(cnpj: str = VALID_CNPJ, **over: object) -> dict:
	base = {
		"nr_pf_pj_fdo": cnpj,
		"entid_invest": "S",
		"publico_alvo": 2,
		"vl_pl_fdo": "1000.5",
		"vl_capital_comprom": "5000",
		"qtd_cotas_subscr": "100",
		"vl_tot_capital_subscr": "4000",
		"qtd_cotas_integr": "50",
		"vl_tot_capital_integr": "2000",
		"vl_tot_cotas_outros_fip": "0",
		"lista_cotst_categ": {
			"cotst_categ": [
				{"cod_categ": "001", "qtd_cotst_subscr": 3, "pr_cotas_subscr": "40.25"},
				{"cod_categ": "015", "qtd_cotst_subscr": 2, "pr_cotas_subscr": "59.75"},
			],
			"tot_cotst_subscr": 5,
			"tx_num_tot_cot": "100",
		},
		"lista_classe_cotas": {
			"classe_cotas": [
				{
					"num_classe": 1,
					"num_cotst_subs": 5,
					"qtd_atual_cotas_subs": "100",
					"qtd_atual_cotas_integ": "50",
					"vl_atual_cota": "12.12345678",
					"direito_polit_especial": "N",
					"direito_dist_econ_finan": "S",
				}
			]
		},
	}
	base.update(over)
	return base


def _doc(*informs: dict, dt_compt: str = "04/2026") -> InformeQuadrimestralDocument:
	return InformeQuadrimestralDocument(
		header={"dt_compt": dt_compt, "dt_gerac_arq": "15/05/2026"},
		informs=list(informs) or [_inform()],
	)


def _xml(doc: InformeQuadrimestralDocument) -> ET.Element:
	text = InformeQuadrimestral().export(doc)
	assert text is not None
	return ET.fromstring(text.encode("windows-1252"))  # noqa: S314


def _tags(el: ET.Element) -> list[str]:
	return [c.tag.removeprefix(NS) for c in el]


def test_export_returns_declaration_namespace_and_root() -> None:
	"""Export returns declaration namespace and root."""
	text = InformeQuadrimestral().export(_doc())
	assert text.startswith('<?xml version="1.0" encoding="windows-1252"?>\n')
	root = ET.fromstring(text.encode("windows-1252"))  # noqa: S314
	assert root.tag == f"{NS}DOC_ARQ"
	assert _tags(root) == ["CAB_INFORM", "LISTA_INFORM"]


def test_header_block_tags_and_values() -> None:
	"""Header block tags and values."""
	header = _xml(_doc())[0]
	assert _tags(header) == HEADER_TAGS
	assert [c.text for c in header] == ["51", "04/2026", "15/05/2026", "2.0"]


def test_inform_block_tags_in_page_order_and_values() -> None:
	"""Inform block tags in page order and values."""
	inform = _xml(_doc())[1][0]
	assert _tags(inform) == INFORM_TAGS
	values = {c.tag.removeprefix(NS): c.text for c in inform}
	assert values["NR_PF_PJ_FDO"] == VALID_CNPJ
	assert values["ENTID_INVEST"] == "S"
	assert values["PUBLICO_ALVO"] == "2"
	assert values["VL_PL_FDO"] == "1000,50000000"
	assert values["VL_TOT_COTAS_OUTROS_FIP"] == "0,00000000"


def test_category_block_tags_repetition_totals_and_codes() -> None:
	"""Category block tags repetition totals and codes."""
	lista = _xml(_doc())[1][0].find(f"{NS}LISTA_COTST_CATEG")
	assert _tags(lista) == ["COTST_CATEG", "COTST_CATEG", "TOT_COTST_SUBSCR", "TX_NUM_TOT_COT"]
	first = lista[0]
	assert _tags(first) == CATEG_TAGS
	assert [c.text for c in first] == ["001", "3", "40,25000000"]
	assert lista[1][0].text == "015"
	assert (lista[2].text, lista[3].text) == ("5", "100,00000000")
	assert LISTA_CATEG_TAGS[1:] == [lista[2].tag.removeprefix(NS), lista[3].tag.removeprefix(NS)]


def test_class_block_tags_and_values() -> None:
	"""Class block tags and values."""
	lista = _xml(_doc())[1][0].find(f"{NS}LISTA_CLASSE_COTAS")
	assert _tags(lista) == ["CLASSE_COTAS"]
	classe = lista[0]
	assert _tags(classe) == CLASSE_TAGS
	assert [c.text for c in classe] == [
		"1",
		"5",
		"100,00000000",
		"50,00000000",
		"12,12345678",
		"N",
		"S",
	]


def test_multiple_funds_are_repeated_informs() -> None:
	"""Multiple funds are repeated informs."""
	informs = _xml(_doc(_inform(), _inform(OTHER_CNPJ)))[1]
	assert _tags(informs) == ["INFORM", "INFORM"]


def test_masked_cnpj_is_written_bare() -> None:
	"""Masked cnpj is written bare."""
	doc = _doc(_inform("11.222.333/0001-81"))
	assert _xml(doc)[1][0][0].text == VALID_CNPJ


def test_extra_decimal_places_are_truncated_not_rounded() -> None:
	"""Extra decimal places are truncated not rounded."""
	doc = _doc(_inform(vl_pl_fdo="1.999999999"))
	assert doc.informs[0].vl_pl_fdo == Decimal("1.99999999")


def test_negative_net_worth_allowed() -> None:
	"""Negative net worth allowed."""
	assert _doc(_inform(vl_pl_fdo="-5")).informs[0].vl_pl_fdo == Decimal(-5)


@pytest.mark.parametrize("field", ["vl_pl_fdo", "qtd_cotas_subscr", "vl_capital_comprom"])
def test_float_decimal_is_refused(field: str) -> None:
	"""Float decimal is refused."""
	with pytest.raises(ValidationError):
		_doc(_inform(**{field: 1.5}))


@pytest.mark.parametrize(
	("field", "bad"),
	[
		("qtd_cotas_subscr", "-1"),
		("vl_capital_comprom", "-0.01"),
		("vl_tot_capital_subscr", "-1"),
		("qtd_cotas_integr", "-1"),
		("vl_tot_capital_integr", "-1"),
		("vl_tot_cotas_outros_fip", "-1"),
		("vl_pl_fdo", "NaN"),
		("vl_pl_fdo", "1" + "0" * 12),
		("entid_invest", "s"),
		("entid_invest", "X"),
		("publico_alvo", 1),
		("publico_alvo", "2"),
		("nr_pf_pj_fdo", "11222333000182"),
		("nr_pf_pj_fdo", " 11222333000181"),
		("nr_pf_pj_fdo", "11222333000181\n"),
	],
)
def test_invalid_inform_values_rejected(field: str, bad: object) -> None:
	"""Invalid inform values rejected."""
	with pytest.raises(ValidationError):
		_doc(_inform(**{field: bad}))


def _with_categ(**over: object) -> dict:
	lista = _inform()["lista_cotst_categ"]
	lista = {**lista, **over}
	return _inform(lista_cotst_categ=lista)


def test_category_rules() -> None:
	"""Category rules."""
	good = {"cod_categ": "002", "qtd_cotst_subscr": 1, "pr_cotas_subscr": "1"}
	bad_inputs = [
		[{**good, "cod_categ": "016"}],
		[{**good, "cod_categ": "1"}],
		[{**good, "qtd_cotst_subscr": -1}],
		[{**good, "qtd_cotst_subscr": True}],
		[{**good, "qtd_cotst_subscr": 1.0}],
		[{**good, "pr_cotas_subscr": "100.0001"}],
		[{**good, "pr_cotas_subscr": "-1"}],
		[good, good],
		[],
	]
	for categs in bad_inputs:
		with pytest.raises(ValidationError):
			_doc(_with_categ(cotst_categ=categs))
	with pytest.raises(ValidationError):
		_doc(_with_categ(tot_cotst_subscr=-1))
	with pytest.raises(ValidationError):
		_doc(_with_categ(tx_num_tot_cot="101"))


def test_all_fifteen_categories_accepted() -> None:
	"""All fifteen categories accepted."""
	categs = [
		{"cod_categ": f"{n:03d}", "qtd_cotst_subscr": 1, "pr_cotas_subscr": "1"}
		for n in range(1, 16)
	]
	doc = _doc(_with_categ(cotst_categ=categs))
	assert len(_xml(doc)[1][0].find(f"{NS}LISTA_COTST_CATEG").findall(f"{NS}COTST_CATEG")) == 15


def _classe(**over: object) -> dict:
	return {**_inform()["lista_classe_cotas"]["classe_cotas"][0], **over}


def test_class_rules() -> None:
	"""Class rules."""
	bad_lists = [
		[],
		[_classe(num_classe=0)],
		[_classe(num_classe=1), _classe(num_classe=1)],
		[_classe(num_cotst_subs=-1)],
		[_classe(qtd_atual_cotas_subs="-1")],
		[_classe(qtd_atual_cotas_integ=2.5)],
		[_classe(direito_polit_especial="Y")],
		[_classe(direito_dist_econ_finan="")],
	]
	for classes in bad_lists:
		with pytest.raises(ValidationError):
			_doc(_inform(lista_classe_cotas={"classe_cotas": classes}))


def test_two_classes_repeat() -> None:
	"""Two classes repeat."""
	classes = [_classe(num_classe=1), _classe(num_classe=2)]
	doc = _doc(_inform(lista_classe_cotas={"classe_cotas": classes}))
	lista = _xml(doc)[1][0].find(f"{NS}LISTA_CLASSE_COTAS")
	assert _tags(lista) == ["CLASSE_COTAS", "CLASSE_COTAS"]


@pytest.mark.parametrize("missing", ["lista_cotst_categ", "lista_classe_cotas", "vl_pl_fdo"])
def test_required_blocks_and_fields(missing: str) -> None:
	"""Required blocks and fields."""
	data = _inform()
	del data[missing]
	with pytest.raises(ValidationError):
		_doc(data)


@pytest.mark.parametrize("month", ["04", "08", "12"])
def test_competence_closing_a_quadrimester_accepted(month: str) -> None:
	"""Competence closing a quadrimester accepted."""
	assert _doc(dt_compt=f"{month}/2026").header.dt_compt == f"{month}/2026"


@pytest.mark.parametrize(
	"bad", ["01/2026", "13/2026", "4/2026", "04/26", "00/2026", "12/1899", "04/2026\n", "٠٤/2026"]
)
def test_competence_rejected(bad: str) -> None:
	"""Competence rejected."""
	with pytest.raises(ValidationError):
		_doc(dt_compt=bad)


@pytest.mark.parametrize("bad", ["31/02/2026", "00/01/2026", "1/1/2026", "01/01/0001", "x"])
def test_generation_date_must_be_a_real_date(bad: str) -> None:
	"""Generation date must be a real date."""
	with pytest.raises(ValidationError):
		InformeQuadrimestralHeader(dt_compt="04/2026", dt_gerac_arq=bad)


def test_header_literals_are_fixed() -> None:
	"""Header literals are fixed."""
	with pytest.raises(ValidationError):
		InformeQuadrimestralHeader(cod_doc=50, dt_compt="04/2026", dt_gerac_arq="01/05/2026")
	with pytest.raises(ValidationError):
		InformeQuadrimestralHeader(versao="1.0", dt_compt="04/2026", dt_gerac_arq="01/05/2026")


def test_document_rules() -> None:
	"""Document rules."""
	header = {"dt_compt": "04/2026", "dt_gerac_arq": "15/05/2026"}
	with pytest.raises(ValidationError):
		InformeQuadrimestralDocument(header=header, informs=[])
	with pytest.raises(ValidationError):
		InformeQuadrimestralDocument(header=header, informs=[_inform(), _inform()])
	funds = [_inform(f"{n:08d}000100") for n in range(101)]
	with pytest.raises(ValidationError):
		InformeQuadrimestralDocument(header=header, informs=funds)


def test_unknown_field_rejected() -> None:
	"""Unknown field rejected."""
	with pytest.raises(ValidationError):
		_doc(_inform(extra="x"))


def test_export_to_file_returns_none_and_writes_windows_1252(tmp_path: Path) -> None:
	"""Export to file returns none and writes windows 1252."""
	out = tmp_path / "iq.xml"
	assert InformeQuadrimestral().export(_doc(), str(out)) is None
	raw = out.read_bytes()
	assert raw.startswith(b'<?xml version="1.0" encoding="windows-1252"?>')
	ET.fromstring(raw)  # noqa: S314


def test_unencodable_text_never_wipes_existing_file(tmp_path: Path) -> None:
	"""Unencodable text never wipes existing file."""
	out = tmp_path / "iq.xml"
	out.write_bytes(b"keep me")
	doc = _doc()
	object.__setattr__(doc.informs[0], "entid_invest", "中")
	with pytest.raises(ValueError, match="windows-1252"):
		InformeQuadrimestral().export(doc, str(out))
	assert out.read_bytes() == b"keep me"
