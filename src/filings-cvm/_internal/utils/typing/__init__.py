"""Runtime type-checking helpers (BlueprintX chassis).

Apply :class:`TypeChecker` as a class metaclass to validate every public method's
annotated argument types at call time, or :func:`type_checker` as a decorator on a
standalone function. :class:`ABCTypeCheckerMeta` and :class:`ProtocolTypeCheckerMeta`
combine the same checking with ``abc.ABCMeta`` / ``Protocol``. These complement —
they do not replace — static checking (mypy + ruff ANN).

Single source of truth: ``templates/python-common/optional/typing/``. The DDD
skeletons receive it at ``src/chassis/typing/`` (this ``chassis.typing`` import
prefix); the MVC skeletons receive it at ``src/utils/typing/`` with the prefix
rewritten to ``utils.typing`` on copy (mirrors the webhook seam).
"""

from __future__ import annotations

from filings-cvm._internal.utils.typing.abc_type_checker import ABCTypeCheckerMeta
from filings-cvm._internal.utils.typing.decorators import type_checker
from filings-cvm._internal.utils.typing.protocol_type_checker import ProtocolTypeCheckerMeta
from filings-cvm._internal.utils.typing.type_checker import TypeChecker
from filings-cvm._internal.utils.typing.validate import validate_type


__all__ = [
	"ABCTypeCheckerMeta",
	"ProtocolTypeCheckerMeta",
	"TypeChecker",
	"type_checker",
	"validate_type",
]
