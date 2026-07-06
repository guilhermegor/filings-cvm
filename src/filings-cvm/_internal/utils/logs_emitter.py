"""Rich, context-aware log emitter — a ready-made default sink for stateful helpers.

The base :class:`LogEmitter` (``retry.py``) is a deliberately minimal, dependency-free seam:
with no logger injected it prints a bare ``[LEVEL] message``. This subclass routes through the
project's :class:`CreateLog` printer instead, so the out-of-the-box line carries a timestamp,
level, and reconstructed ``{Class} [method]`` caller context — while remaining a drop-in
``LogEmitter`` any consumer can override by injecting their own emitter. This is exactly the
"subclass ``LogEmitter`` and inject it" seam that ``retry.py`` documents; wire it as the default
sink of any stateful helper that wants rich output out of the box.
"""

from __future__ import annotations

import logging
from typing import cast

from filings-cvm._internal.utils.logs import CreateLog, LogLevel
from filings-cvm._internal.utils.retry import LogEmitter


# The levels the rich printer accepts; an unrecognised level degrades to ``warning`` so the
# emitter stays as forgiving as the bare base :class:`LogEmitter` (never raises on odd input).
_VALID_LOG_LEVELS: frozenset[str] = frozenset({"info", "warning", "error", "critical"})


class LogsEmitter(LogEmitter):
	""":class:`LogEmitter` backed by the project's rich :class:`CreateLog` printer.

	With no logger injected the rich line is printed to the screen; with a logger injected the
	message is routed there, prefixed with the reconstructed caller context. Callers depend only
	on ``log_message`` and may inject any replacement, so the seam stays overridable.
	"""

	def __init__(self, cls_logger: logging.Logger | None = None) -> None:
		"""Build a rich emitter, optionally over an injected logger.

		Parameters
		----------
		cls_logger : logging.Logger, optional
			The standard-library logger to route to. When ``None`` (the default) the rich line
			is printed to the screen instead.
		"""
		super().__init__(cls_logger)
		self._cls_create_log = CreateLog()

	def log_message(self, str_message: str, str_level: str) -> None:
		"""Emit ``str_message`` at ``str_level`` through the rich printer.

		Parameters
		----------
		str_message : str
			The message to emit.
		str_level : str
			The level name; an unrecognised level falls back to ``"warning"`` (mirroring the
			forgiving behaviour of the base :class:`LogEmitter`).
		"""
		str_normalized = str_level.lower()
		log_level = cast(
			LogLevel, str_normalized if str_normalized in _VALID_LOG_LEVELS else "warning"
		)
		self._cls_create_log.log_message(self._cls_logger, str_message, log_level)
