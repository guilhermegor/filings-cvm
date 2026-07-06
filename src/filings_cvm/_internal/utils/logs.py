"""Logging module — self-contained in-repo logging seam.

One home for the project's logging, so no external logging dependency is needed:

- :class:`CreateLog` — configures a file logger (:meth:`CreateLog.basic_conf`) and emits messages
  with caller context (:meth:`CreateLog.log_message`); the message is prefixed with
  ``[ClassName.method_name]``, reconstructed by walking the call stack.
- :func:`log_message` — the shared entry point every model/view/controller calls, holding a
  single ``CreateLog`` instance so callers never instantiate their own.
- :func:`initiate_logging` — bootstraps a run's logging: ensures the log parent directory exists
  and records the run's start datetime (stdlib UTC) and operator.

Layout-agnostic: ships into both MVC (``utils``) and DDD (``chassis``) skeletons.
"""

from datetime import datetime
from getpass import getuser
import inspect
import logging
import os
import time
from typing import TYPE_CHECKING, Literal
from zoneinfo import ZoneInfo


# Runtime type-checking engine — layout-agnostic (utils.typing in MVC, chassis.typing in
# DDD; always injected, just at different paths). mypy reads the single TYPE_CHECKING
# import (no redefinition); at runtime the try/except picks whichever layout shipped.
if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import TypeChecker, type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import TypeChecker, type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import TypeChecker, type_checker


# Frame modules skipped when reconstructing the caller context: the stdlib logging and inspect
# machinery, pydantic and typing internals, the project's own runtime type-checker, and the
# logging seam itself (logs, logs emitter, retry) whose wrapper frames would otherwise mask the
# real caller. Matched on the module name's last dotted component (see the walker below), so a
# package-qualified name still matches its final segment where a prefix match would not.
_SET_SKIP_MODULES = frozenset(
	{"pydantic", "typing", "inspect", "logging", "logs", "logs_emitter", "retry"}
)

# The severities a message may carry — shared by ``CreateLog.log_message`` and the module-level
# ``log_message`` seam so the two never drift (mypy checks the forwarded argument against this).
LogLevel = Literal["info", "warning", "error", "critical"]


class CreateLog(metaclass=TypeChecker):
	"""Create and manage log files with a customizable format and caller context."""

	def _validate_path(self, path: str) -> None:
		"""Validate a path string.

		Parameters
		----------
		path : str
			Path to validate.

		Raises
		------
		ValueError
			If ``path`` is empty or not a string.
		"""
		if not path:
			raise ValueError("Path cannot be empty")
		if not isinstance(path, str):
			raise ValueError("Path must be a string")

	def creating_parent_folder(self, new_path: str) -> bool:
		"""Create the parent folder if it does not already exist.

		Parameters
		----------
		new_path : str
			Directory path to create.

		Returns
		-------
		bool
			``True`` if the folder was created, ``False`` if it already existed.
		"""
		self._validate_path(new_path)
		if not os.path.exists(new_path):
			os.makedirs(new_path)
			return True
		return False

	def basic_conf(
		self, complete_path: str, basic_level: Literal["info", "debug"] = "info"
	) -> logging.Logger:
		"""Configure a file logger.

		Parameters
		----------
		complete_path : str
			Full path to the log file.
		basic_level : Literal['info', 'debug']
			Logging level (default: ``"info"``).

		Returns
		-------
		logging.Logger
			The configured logger instance.

		Raises
		------
		ValueError
			If an invalid logging level is provided.
		"""
		self._validate_path(complete_path)

		dict_level_mapping = {"info": logging.INFO, "debug": logging.DEBUG}

		try:
			int_level = dict_level_mapping[basic_level]
		except KeyError as err:
			raise ValueError("Level was not properly defined in basic config of logging") from err

		logger = logging.getLogger(__name__)
		logger.setLevel(int_level)
		handler = logging.FileHandler(complete_path)
		handler.setFormatter(
			logging.Formatter(
				"%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s",
				datefmt="%Y-%m-%d,%H:%M:%S",
			)
		)
		logger.handlers.clear()
		logger.addHandler(handler)
		return logger

	def log_message(
		self,
		logger: logging.Logger | None,
		message: str,
		log_level: LogLevel,
	) -> None:
		"""Log a message with reconstructed caller context.

		Parameters
		----------
		logger : logging.Logger | None
			Logger instance, or ``None`` to print to the console.
		message : str
			Message to log.
		log_level : LogLevel
			Logging level — one of ``"info"`` / ``"warning"`` / ``"error"`` / ``"critical"``.

		Raises
		------
		ValueError
			If ``log_level`` is empty or not a valid logger method.
		"""
		if not log_level:
			raise ValueError("log_level cannot be empty")

		frame = inspect.currentframe()
		str_class_name = "UnknownClass"
		str_method_name = "unknown_method"

		while frame:
			frame = frame.f_back
			if not frame:
				break
			str_module_name = frame.f_globals.get("__name__", "UnknownModule")
			# Match on the module name's last dotted component so a package-qualified module
			# still matches its final segment. A prefix match silently failed for the nested,
			# distributable layout and misattributed the caller class.
			if str_module_name.rsplit(".", 1)[-1] in _SET_SKIP_MODULES:
				continue
			self_potential_cls = frame.f_locals.get("self")
			if self_potential_cls is not None and not isinstance(
				self_potential_cls, self.__class__
			):
				str_class_name = self_potential_cls.__class__.__name__
				str_method_name = frame.f_code.co_name
				break
			str_method_name = frame.f_code.co_name

		str_formatted = f"[{str_class_name}.{str_method_name}] {message}"

		if logger is not None:
			fn_log = getattr(logger, log_level, None)
			if fn_log is None:
				raise ValueError(f"Invalid log level: {log_level}")
			fn_log(str_formatted)
		else:
			str_level = log_level.upper()
			str_timestamp = (
				f"{time.strftime('%Y-%m-%d,%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d}"
			)
			str_line = (
				f"{str_timestamp} {str_level} {{{str_class_name}}} [{str_method_name}] {message}"
			)
			print(str_line)


_CLS_LOG = CreateLog()


@type_checker
def log_message(
	logger: logging.Logger | None, str_message: str, str_level: LogLevel = "info"
) -> None:
	"""Log ``str_message`` at ``str_level`` through the shared logger.

	Parameters
	----------
	logger : logging.Logger | None
		Destination logger; when ``None`` the message is printed with a timestamp.
	str_message : str
		The message to log.
	str_level : LogLevel, optional
		One of ``"info"``, ``"warning"``, ``"error"``, ``"critical"``; default ``"info"``.
	"""
	_CLS_LOG.log_message(logger, str_message, str_level)


@type_checker
def _validate_path_log(path_log: str | None) -> None:
	"""Validate the log path.

	Parameters
	----------
	path_log : str | None
		Path for the log-file directory.

	Raises
	------
	ValueError
		If ``path_log`` is an empty string.
	"""
	if path_log == "":
		raise ValueError("Log path cannot be an empty string")


@type_checker
def initiate_logging(logger: logging.Logger, path_log: str | None = None) -> None:
	"""Initialise logging with directory creation and operator information.

	Parameters
	----------
	logger : logging.Logger
		Logger instance for the run.
	path_log : str | None
		Path for the log-file directory (default: ``None``).

	Raises
	------
	RuntimeError
		If an unexpected dispatch value is returned from directory creation.
	"""
	_validate_path_log(path_log)

	cls_create_log = CreateLog()

	if path_log is not None:
		bool_dispatch = cls_create_log.creating_parent_folder(path_log)
		cls_create_log.log_message(logger, f"Logs parent directory: {path_log}", "info")
		if bool_dispatch is True:
			cls_create_log.log_message(
				logger, "Logs parent directory created successfully.", "info"
			)
		elif bool_dispatch is False:
			cls_create_log.log_message(
				logger, "Logs parent directory could not be created.", "info"
			)
		else:
			raise RuntimeError(f"Unexpected dispatch value: {bool_dispatch}") from None

	dt_now = datetime.now(tz=ZoneInfo("UTC"))
	cls_create_log.log_message(logger, f"Routine started at {dt_now}", "info")
	cls_create_log.log_message(logger, f"Routine operator {getuser()}", "info")
