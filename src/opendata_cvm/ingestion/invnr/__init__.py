"""CVM open-data `Investidor Não Residente` readers (`INVNR/`).

Mirrors the `dados.cvm.gov.br/dados/INVNR/` portal branch — one sibling among the portal's other
roots. It publishes only a registry (`INVNR/CAD`, :mod:`opendata_cvm.ingestion.invnr.cad`) of the
representatives of non-resident investors CVM supervises, split into natural and legal persons.
"""

from opendata_cvm.ingestion.invnr.cad import (
	InvnrRepresPfReader,
	InvnrRepresPjReader,
	MetaInvnrRepresReader,
)


__all__ = [
	"InvnrRepresPfReader",
	"InvnrRepresPjReader",
	"MetaInvnrRepresReader",
]
