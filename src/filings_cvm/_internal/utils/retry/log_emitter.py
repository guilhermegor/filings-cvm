"""``LogEmitter`` — the injectable log sink the retry seam writes warnings to."""

from __future__ import annotations

import logging

from filings_cvm._internal.utils.typing import TypeChecker


_LOGGER: logging.Logger = logging.getLogger(__name__)


class LogEmitter(metaclass=TypeChecker):
	"""Sink the retry executors write each retry warning to (injectable).

	The default implementation forwards to a standard-library :class:`logging.Logger`. A
	caller that wants richer routing (e.g. the project's ``utils.logs`` formatting) injects
	its own :class:`LogEmitter` subclass — the retry seam then depends only on the
	``log_message`` method, never on any concrete logging module, so it stays
	dependency-free for a distributable library.
	"""

	def __init__(self, cls_logger: logging.Logger | None = None) -> None:
		"""Build an emitter over ``cls_logger`` (defaults to this module's logger).

		Parameters
		----------
		cls_logger : logging.Logger, optional
			The standard-library logger to write to; defaults to the logger for this module.
		"""
		self._cls_logger = cls_logger if cls_logger is not None else _LOGGER

	def log_message(self, str_message: str, str_level: str) -> None:
		"""Emit ``str_message`` at the named level.

		Parameters
		----------
		str_message : str
			The message to log.
		str_level : str
			The level name (e.g. ``"warning"``, ``"info"``); falls back to ``warning`` when
			the underlying logger has no method of that name.
		"""
		fn_emit = getattr(self._cls_logger, str_level.lower(), self._cls_logger.warning)
		fn_emit(str_message)
