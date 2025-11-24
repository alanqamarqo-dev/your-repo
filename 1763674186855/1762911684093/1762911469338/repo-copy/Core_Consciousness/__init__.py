"""Core Consciousness package (C-Layer) - lightweight implementations.

This module now exposes a safe factory `create_engine` that constructs a
composed `ConsciousnessService`. Imports are done locally inside the factory
to avoid import cycles and the factory tolerates a missing memory bridge so it
is safe to call early in boot/CI.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

# Export convenient class names expected by tests/importers
try:
	from .Self_Model import SelfModel
except Exception:
	# fall back to module name if direct class import fails
	SelfModel = None
try:
	from .Perception_Loop import PerceptionLoop
except Exception:
	PerceptionLoop = None
try:
	from .Intent_Generator import IntentGenerator
except Exception:
	IntentGenerator = None
try:
	from .State_Logger import StateLogger
except Exception:
	StateLogger = None

@dataclass
class ConsciousnessService:
	self_model: Any
	perception_loop: Any
	intent_generator: Any
	state_logger: Any
	bridge: Any

	def start(self) -> None:
		"""
		Run a short safe conscious cycle if components expose familiar APIs.
		This method intentionally tries multiple method names so it works with
		lightweight/test implementations and with the production ones.
		"""
		try:
			snapshot = None
			# perception: prefer run_once, fallback to step
			if hasattr(self.perception_loop, "run_once"):
				snapshot = self.perception_loop.run_once()
			elif hasattr(self.perception_loop, "step"):
				try:
					snapshot = self.perception_loop.step()
				except Exception:
					snapshot = None

			# intent: prefer decide(snapshot)
			intent = None
			if snapshot is not None and hasattr(self.intent_generator, "decide"):
				try:
					intent = self.intent_generator.decide(snapshot)
				except Exception:
					intent = None
			elif hasattr(self.intent_generator, "propose"):
				try:
					intent = self.intent_generator.propose()
				except Exception:
					intent = None

			# state logging: prefer log(snapshot, intent)
			if hasattr(self.state_logger, "log"):
				try:
					# Some implementations accept (snapshot, intent)
					if snapshot is not None:
						self.state_logger.log(snapshot, intent)
					else:
						# best effort
						self.state_logger.log({}, intent or {})
				except Exception:
					pass
			elif hasattr(self.state_logger, "flush"):
				try:
					self.state_logger.flush()
				except Exception:
					pass
		except Exception:
			# never raise from start() — keep boot tolerant
			pass


def create_engine(config: Optional[dict] = None,
				  bridge: Optional[Any] = None,
				  registry: Optional[Any] = None) -> ConsciousnessService:
	"""
	Safe factory to construct a composed ConsciousnessService.
	- Imports are local to avoid import cycles.
	- If the memory bridge isn't available the factory still returns a
	  usable service (components may operate in degraded/test mode).
	- The factory adapts to the existing constructors in this package so it
	  is resilient to small API differences.
	"""
	# Local imports to avoid import cycles
	from importlib import import_module

	# try to obtain bridge singleton if not provided
	if bridge is None:
		try:
			get_bridge = import_module("Core_Memory.bridge_singleton").get_bridge
			bridge = get_bridge()
		except Exception:
			bridge = None

	# load classes
	Self_Model = import_module("Core_Consciousness.Self_Model").SelfModel
	Perception_Loop = import_module("Core_Consciousness.Perception_Loop").PerceptionLoop
	Intent_Generator = import_module("Core_Consciousness.Intent_Generator").IntentGenerator
	State_Logger = import_module("Core_Consciousness.State_Logger").StateLogger

	# initialize components with conservative signatures
	cfg = config or {}
	try:
		sm = Self_Model(cfg.get("goal", "keep_system_healthy"))
	except TypeError:
		# fallback: call without args
		sm = Self_Model()

	# PerceptionLoop expects self_model and optional interval/sample_scope
	interval = cfg.get("interval", 2.0)
	sample_scope = cfg.get("sample_scope", "stm")
	try:
		pl = Perception_Loop(self_model=sm, interval=interval, sample_scope=sample_scope)
	except TypeError:
		# fallback to positional if signature differs
		try:
			pl = Perception_Loop(sm)
		except Exception:
			pl = Perception_Loop(sm, interval)

	try:
		ig = Intent_Generator()
	except TypeError:
		ig = Intent_Generator

	try:
		sl = State_Logger()
	except TypeError:
		sl = State_Logger

	service = ConsciousnessService(
		self_model=sm,
		perception_loop=pl,
		intent_generator=ig,
		state_logger=sl,
		bridge=bridge,
	)

	# optional registry registration
	try:
		if registry is not None and hasattr(registry, "register"):
			try:
				registry.register(name="Core_Consciousness", engine=service)
			except TypeError:
				# some registries expect positional args
				try:
					registry.register("Core_Consciousness", service)
				except Exception:
					pass
	except Exception:
		pass

	return service


__all__ = ["ConsciousnessService", "create_engine"]

# Also expose test-friendly short names if they were successfully imported
for _n in ("SelfModel", "PerceptionLoop", "IntentGenerator", "StateLogger"):
	if globals().get(_n) is not None and _n not in __all__:
		__all__.append(_n)
