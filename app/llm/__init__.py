"""LLM-assisted variants (DESIGN §2.5, STRUCTURE §4.3b).

The package is deliberately inert at import time: the generators import
``app.llm.spec`` for the scenario catalogue, so eagerly importing the provider client here
would create an import cycle. Names are resolved lazily (PEP 562) instead.
"""

from __future__ import annotations

import importlib

_LAZY: dict[str, tuple[str, str]] = {
    "Given": ("app.llm.spec", "Given"),
    "Spec": ("app.llm.spec", "Spec"),
    "SpecError": ("app.llm.spec", "SpecError"),
    "ScenarioSpec": ("app.llm.spec", "ScenarioSpec"),
    "SCENARIOS": ("app.llm.spec", "SCENARIOS"),
    "LLMClient": ("app.llm.client", "LLMClient"),
    "ProviderConfig": ("app.llm.client", "ProviderConfig"),
    "SpecFetch": ("app.llm.client", "SpecFetch"),
    "fetch_variant_specs": ("app.llm.client", "fetch_variant_specs"),
    "fetch_variant_specs_report": ("app.llm.client", "fetch_variant_specs_report"),
    "spec_to_item": ("app.generators.physics.variants", "spec_to_item"),
    "generate_variants": ("app.llm.variants", "generate_variants"),
    "template_items": ("app.llm.variants", "template_items"),
}

__all__ = sorted(_LAZY)


def __getattr__(name: str):
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = target
    value = getattr(importlib.import_module(module), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return __all__
