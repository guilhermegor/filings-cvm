"""Reference data contract — copy this per real input source, then delete the example.

Declares the columns the file must carry (``tuple_required``) and the columns that must hold
at least one valid CNPJ (``tuple_cnpj_cols``). The model/controller passes this instance to
``utils.tabular_reader.read_table`` / ``read_query``, which raises ``ContractError`` on any
violation before types are applied.
"""

from __future__ import annotations

from filings-cvm._internal.utils.tabular_reader import FileContract


# str_name (human label), str_source_key (routes notifications), tuple_required, tuple_cnpj_cols.
EXAMPLE_SOURCE = FileContract(
	"Example Source",
	"example_source",
	("code", "amount"),
	(),
)
