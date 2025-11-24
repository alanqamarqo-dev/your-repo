from typing import Any, Callable, Dict


class IntegrationRegistry:
    """
    Service locator/registry to register and resolve shared integration services.
    - Supports both instances and lazy factories (callables).
    - Prevents duplicate keys unless `override=True`.
    """
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}

    def register(self, key: str, service: Any, *, override: bool = False) -> None:
        # Make registration idempotent: if the key is already present and override
        # is False, quietly return without raising. Tests and bootstrap code may
        # attempt repeated registration in the same process; tolerating that
        # avoids noisy 'registry rejected' symptoms.
        if not override and (key in self._services or key in self._factories):
            return
        self._services[key] = service
        if key in self._factories:
            del self._factories[key]

    def register_factory(self, key: str, factory: Callable[[], Any], *, override: bool = False) -> None:
        # Idempotent behaviour for factories as well.
        if not override and (key in self._services or key in self._factories):
            return
        self._factories[key] = factory
        if key in self._services:
            del self._services[key]

    def resolve(self, key: str) -> Any:
        if key in self._services:
            return self._services[key]
        if key in self._factories:
            instance = self._factories[key]()
            # cache instance for future resolves
            self._services[key] = instance
            del self._factories[key]
            return instance
        raise KeyError(f"Service '{key}' not found in IntegrationRegistry.")

    def has(self, key: str) -> bool:
        return key in self._services or key in self._factories

    def clear(self) -> None:
        """Clear all registered services and factories (useful for tests)."""
        self._services.clear()
        self._factories.clear()

    def keys(self):
        return list(set(self._services.keys()) | set(self._factories.keys()))


# --- Registry singleton proxy (backwards-compatible signatures) ---
_internal_registry = IntegrationRegistry()


class _RegistryProxy:
    """Light proxy that accepts multiple register signatures for backwards compatibility.

    Delegates to a real IntegrationRegistry instance while supporting calls like:
    - register(name=..., engine=...)
    - register(key=..., service=...)
    - register(name, engine)
    - register(engine_instance)  # uses engine.name or class name
    """
    def register(self, *args, **kwargs):
        override = kwargs.get("override", False)
        # signature: register(name=..., engine=...)
        if "name" in kwargs and "engine" in kwargs:
            return _internal_registry.register(kwargs["name"], kwargs["engine"], override=override)
        # signature: register(key=..., service=...)
        if "key" in kwargs and "service" in kwargs:
            return _internal_registry.register(kwargs["key"], kwargs["service"], override=override)
        # positional (name, service)
        if len(args) == 2:
            return _internal_registry.register(args[0], args[1], override=override)
        # single positional: register(engine_instance)
        if len(args) == 1:
            eng = args[0]
            n = getattr(eng, "name", eng.__class__.__name__)
            return _internal_registry.register(n, eng, override=override)
        raise TypeError("Unsupported register signature")

    def register_factory(self, *args, **kwargs):
        return _internal_registry.register_factory(*args, **kwargs)

    def resolve(self, key: str) -> Any:
        return _internal_registry.resolve(key)

    def has(self, key: str) -> bool:
        return _internal_registry.has(key)

    def keys(self):
        return _internal_registry.keys()

    def list_names(self):
        return _internal_registry.keys()

    def add_engine(self, name, engine):
        # convenience alias
        return _internal_registry.register(name, engine, override=True)

    def add(self, name, engine):
        return _internal_registry.register(name, engine, override=True)

    def alias(self, alias_name: str, target_name: str):
        """Create an alias in the registry so `alias_name` resolves to the same
        service/factory as `target_name`. If the target is already resolved, the
        instance is registered under the alias. If the target is a factory, the
        alias will register a lazy factory that resolves the original on first use.
        """
        if _internal_registry.has(alias_name):
            # don't override existing alias unless explicitly requested via register
            raise KeyError(f"Alias '{alias_name}' conflicts with existing service")
        # if target is a concrete service, copy it
        if target_name in _internal_registry._services:
            _internal_registry._services[alias_name] = _internal_registry._services[target_name]
            return
        # if target is a factory, create a wrapper factory
        if target_name in _internal_registry._factories:
            def _alias_factory(tn=target_name):
                return _internal_registry.resolve(tn)
            _internal_registry._factories[alias_name] = _alias_factory
            return
        raise KeyError(f"Target '{target_name}' not found for aliasing")

    def get(self, name, default=None):
        try:
            return _internal_registry.resolve(name)
        except KeyError:
            return default

    def clear(self):
        """Clear the underlying singleton registry (tests can call registry.clear())."""
        _internal_registry.clear()

    def __contains__(self, name):
        return _internal_registry.has(name)


# singleton instance for importers
registry = _RegistryProxy()
