"""CVM open-data **registry** readers for non-resident-investor representatives (`INVNR/CAD`).

The two members of the `cad_invnr_repres.zip` snapshot — natural-person representatives
(:class:`~opendata_cvm.ingestion.invnr.cad.invnr_repres_pf.InvnrRepresPfReader`) and representative
firms (:class:`~opendata_cvm.ingestion.invnr.cad.invnr_repres_pj.InvnrRepresPjReader`) — over a
shared private base (`_base_invnr_repres_reader`), plus the dataset's META reader. Re-exported
flat at the package root.
"""

from opendata_cvm.ingestion.invnr.cad.invnr_repres_pf import InvnrRepresPfReader
from opendata_cvm.ingestion.invnr.cad.invnr_repres_pj import InvnrRepresPjReader
from opendata_cvm.ingestion.invnr.cad.meta import MetaInvnrRepresReader


__all__ = [
	"InvnrRepresPfReader",
	"InvnrRepresPjReader",
	"MetaInvnrRepresReader",
]
