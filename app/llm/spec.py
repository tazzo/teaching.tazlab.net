"""The variant spec: what the model proposes, and the rules that admit it.

The model never produces an answer (DESIGN §2.5). It proposes a *scenario* — which
quantities are given, with which units, and which one is asked — and SymPy derives the
answer. This module owns the spec's shape, its per-scenario declaration (givens, units,
magnitudes) and every check that can reject a proposal *before* any solving happens:

* structural: ``scenario``, ``givens``, ``unknown``, ``ask``, ``result_units``;
* exactness: numbers are rationals (integers, exact decimals, ``"a/b"`` strings) — never
  a ``float``, because a single float leaks into the printed answer (DESIGN §3);
* units: every given carries a unit the unit table knows (``core.units``);
* plausibility: the §2.10 per-scenario magnitude table, magnitude-checked in SI, with
  the speed of sound as the named constant it is (never a random draw);
* a scaleless ask is rejected outright — an exercise whose answer has no unit is not a
  physics exercise.

Nothing here knows about HTTP, providers or LaTeX. The rules are pure data plus pure
functions so a test can drive them without a network or an LLM.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction

from app.core.units import speed_of_sound, to_si


class SpecError(ValueError):
    """A rejected proposal. ``reason`` is machine-readable and lands in the log line."""

    def __init__(self, reason: str, detail: str | None = None) -> None:
        super().__init__(reason if detail is None else f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Given:
    symbol: str
    value: Fraction
    unit: str


@dataclass(frozen=True)
class Spec:
    scenario: str
    givens: tuple[Given, ...]
    unknown: str
    ask: str
    result_units: str

    def given(self, symbol: str) -> Given | None:
        for item in self.givens:
            if item.symbol == symbol:
                return item
        return None

    def as_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "givens": [
                {"symbol": g.symbol, "value": str(g.value), "unit": g.unit} for g in self.givens
            ],
            "unknown": self.unknown,
            "ask": self.ask,
            "result_units": self.result_units,
        }


# --------------------------------------------------------------------- quantities
@dataclass(frozen=True)
class Quantity:
    """One physical quantity of a scenario: its canonical unit and its plausible range.

    ``allowed_units`` are the *other* spellings the model may use; they are converted to
    the canonical unit before anything else happens, so the statement template can print
    one unit and the magnitudes stay comparable.
    """

    symbol: str
    unit: str
    lo: Fraction
    hi: Fraction
    allowed_units: tuple[str, ...] = ()

    @property
    def units(self) -> tuple[str, ...]:
        return (self.unit, *self.allowed_units)


@dataclass(frozen=True)
class ScenarioSpec:
    """The contract of one variant scenario — the constraint that makes N specs similar.

    ``difficulty`` is the shape, not a label: the topic's ``verify()`` branches on it, so
    the scenario *is* the shape (``uniform_graph_reading`` is the hard one). The request's
    ``difficulty`` therefore cannot change it without invalidating the verification.
    """

    id: str
    topic_id: str
    difficulty: str
    ask: str
    brief: str
    givens: tuple[Quantity, ...]
    unknown: Quantity


_SPEED = ("m/s", "km/h")
_LENGTH = ("m", "km", "cm")
_TIME = ("s", "min")
_ACCEL = ("m/s^2",)
_MS = "m/s"


def _q(symbol: str, unit: str, lo, hi, allowed: tuple[str, ...] = ()) -> Quantity:
    return Quantity(symbol, unit, Fraction(lo), Fraction(hi), allowed)


# --------------------------------------------------------------------- catalogue
# One entry per scenario id in the catalog plus the sound scenario (§2.10 "the operator's
# case": the speed of sound is a constant, so it is pinned to exactly 343 m/s).
SCENARIOS: dict[str, ScenarioSpec] = {
    "uniform_one_object": ScenarioSpec(
        id="uniform_one_object",
        topic_id="physics.kinematics.uniform",
        difficulty="easy",
        ask="distance_in_uniform_motion",
        brief="one object in uniform rectilinear motion; the distance travelled in a time",
        givens=(_q("v", _MS, 1, 25, ("km/h",)), _q("t", "s", 1, 60, ("min",))),
        unknown=_q("s", "m", 1, 1500, ("km",)),
    ),
    "uniform_unit_conversion": ScenarioSpec(
        id="uniform_unit_conversion",
        topic_id="physics.kinematics.uniform",
        difficulty="medium",
        ask="distance_after_unit_conversion",
        brief="a speed in km/h and a time; the distance in metres after the conversion",
        givens=(_q("v_kmh", "km/h", 4, 90), _q("t", "s", 1, 60, ("min",))),
        unknown=_q("s", "m", 1, 1500, ("km",)),
    ),
    "uniform_graph_reading": ScenarioSpec(
        id="uniform_graph_reading",
        topic_id="physics.kinematics.uniform",
        difficulty="hard",
        ask="speed_from_two_graph_points",
        brief=(
            "two points read off an s(t) graph of motion started from the origin; the two "
            "points must lie on one straight line through the origin"
        ),
        givens=(
            _q("t1", "s", 1, 30),
            _q("s1", "m", 1, 1500),
            _q("t2", "s", 2, 60),
            _q("s2", "m", 1, 1500),
        ),
        unknown=_q("v", _MS, 1, 25),
    ),
    "uniform_sound_distance": ScenarioSpec(
        id="uniform_sound_distance",
        topic_id="physics.kinematics.uniform",
        difficulty="easy",
        ask="sound_travel_distance",
        brief=(
            "sound travelling through air at 20 °C; use the speed of sound as the fixed "
            "constant c = 343 m/s and give the distance covered in a short time"
        ),
        givens=(
            _q("c", _MS, speed_of_sound(), speed_of_sound()),
            _q("t", "s", Fraction(3, 100), 15),
        ),
        unknown=_q("s", "m", 10, 5000, ("km",)),
    ),
    "accelerated_from_rest": ScenarioSpec(
        id="accelerated_from_rest",
        topic_id="physics.kinematics.accelerated",
        difficulty="easy",
        ask="speed_from_rest",
        brief="one object starting from rest with constant acceleration; its speed after t",
        givens=(_q("a", "m/s^2", 1, 6), _q("t", "s", 2, 12)),
        unknown=_q("v", _MS, 2, 72),
    ),
    "accelerated_with_v0": ScenarioSpec(
        id="accelerated_with_v0",
        topic_id="physics.kinematics.accelerated",
        difficulty="medium",
        ask="braking_time",
        brief="a vehicle moving at v0 that brakes with a *negative* acceleration; its stopping time",
        givens=(_q("v0", _MS, 5, 40, ("km/h",)), _q("a", "m/s^2", -8, Fraction(-1, 2))),
        unknown=_q("t_stop", "s", 1, 30),
    ),
    "accelerated_derive_a": ScenarioSpec(
        id="accelerated_derive_a",
        topic_id="physics.kinematics.accelerated",
        difficulty="hard",
        ask="acceleration_from_two_readings",
        brief=(
            "two speed readings with their instants off a v(t) graph; the acceleration is "
            "the slope Δv/Δt and must come out between 0.1 and 6 m/s²"
        ),
        givens=(
            _q("t1", "s", 1, 30),
            _q("v1", _MS, 1, 100),
            _q("t2", "s", 2, 60),
            _q("v2", _MS, 1, 100),
        ),
        unknown=_q("a", "m/s^2", Fraction(1, 10), 6),
    ),
}

# The speeds of sound is a named constant (DESIGN §2.10): it may never be drawn.
SOUND_SPEED = speed_of_sound()

_SCALELESS = {"", "1", "-", "none", "null", "dimensionless", "unitless", "%", "percent", "rad", "rad/s"}


def scenario(scenario_id: str) -> ScenarioSpec | None:
    return SCENARIOS.get(scenario_id)


# ------------------------------------------------------------------- primitives
def to_exact(raw: object) -> Fraction:
    """A JSON scalar → an exact ``Fraction``, or a rejection. Never a ``float``.

    A float is *not* converted blindly: ``Fraction(0.1)`` is a 17-digit fraction. The
    decimal spelling the model wrote is converted instead (``Fraction("0.1")`` is 1/10),
    so what the model said is what we use, and no binary float ever enters the pipeline.
    """
    if isinstance(raw, bool):
        raise SpecError("non_numeric_value", repr(raw))
    if isinstance(raw, int):
        return Fraction(raw)
    if isinstance(raw, float):
        if not math.isfinite(raw):
            raise SpecError("non_numeric_value", repr(raw))
        return Fraction(str(raw))
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise SpecError("non_numeric_value", repr(raw))
        try:
            return Fraction(text)
        except (ValueError, ZeroDivisionError) as exc:
            raise SpecError("non_numeric_value", text) from exc
    raise SpecError("non_numeric_value", repr(raw))


def unit_factor(unit: object, *, scaleless_reason: str = "unknown_unit") -> Fraction:
    """The SI factor of ``unit``, or a rejection naming the cause."""
    if not isinstance(unit, str) or unit.strip().lower() in _SCALELESS:
        raise SpecError(scaleless_reason, repr(unit))
    text = unit.strip()
    try:
        return to_si(Fraction(1), text)
    except KeyError as exc:
        raise SpecError("unknown_unit", text) from exc


# ------------------------------------------------------------------- structural
def parse_spec(payload: object) -> Spec:
    """Payload → ``Spec``. Structure, exactness and unit *validity* only.

    Magnitudes and the scenario table are checked by :func:`validate_spec`, which knows
    which scenario was asked for.
    """
    if not isinstance(payload, dict):
        raise SpecError("not_an_object", type(payload).__name__)

    scenario_id = payload.get("scenario")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise SpecError("missing_scenario")
    scenario_id = scenario_id.strip()

    raw_givens = payload.get("givens")
    if not isinstance(raw_givens, list) or not raw_givens:
        raise SpecError("missing_givens")

    givens: list[Given] = []
    seen: set[str] = set()
    for raw in raw_givens:
        if not isinstance(raw, dict):
            raise SpecError("malformed_given", repr(raw))
        symbol = raw.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            raise SpecError("missing_symbol")
        symbol = symbol.strip()
        if symbol in seen:
            raise SpecError("duplicate_given", symbol)
        seen.add(symbol)
        value = to_exact(raw.get("value"))
        unit = raw.get("unit")
        unit_factor(unit, scaleless_reason="missing_unit")
        givens.append(Given(symbol, value, unit.strip()))

    unknown = payload.get("unknown")
    if not isinstance(unknown, str) or not unknown.strip():
        raise SpecError("missing_unknown")
    unknown = unknown.strip()
    if unknown in seen:
        raise SpecError("unknown_is_given", unknown)

    ask = payload.get("ask")
    if not isinstance(ask, str) or not ask.strip():
        raise SpecError("missing_ask")
    ask = ask.strip()
    if len(ask) > 200:
        raise SpecError("ask_too_long")

    result_units = payload.get("result_units")
    unit_factor(result_units, scaleless_reason="scaleless_ask")

    return Spec(
        scenario=scenario_id,
        givens=tuple(givens),
        unknown=unknown,
        ask=ask,
        result_units=result_units.strip(),
    )


def validate_spec(spec: Spec, scenario_id: str) -> Spec:
    """Scenario membership, the exact given set, units and the §2.10 magnitudes."""
    declared = SCENARIOS.get(scenario_id)
    if declared is None:
        raise SpecError("unknown_scenario", scenario_id)
    if spec.scenario != scenario_id:
        raise SpecError("scenario_mismatch", f"{spec.scenario} != {scenario_id}")

    if spec.unknown != declared.unknown.symbol:
        raise SpecError("unexpected_unknown", f"{spec.unknown} != {declared.unknown.symbol}")

    quantities = {q.symbol: q for q in declared.givens}
    given_symbols = {g.symbol for g in spec.givens}
    missing = sorted(set(quantities) - given_symbols)
    if missing:
        raise SpecError("missing_givens", ",".join(missing))
    unexpected = sorted(given_symbols - set(quantities))
    if unexpected:
        raise SpecError("unexpected_given", ",".join(unexpected))

    for given in spec.givens:
        quantity = quantities[given.symbol]
        if given.unit not in quantity.units:
            raise SpecError("unexpected_unit", f"{given.symbol}:{given.unit}")
        magnitude = to_si(given.value, given.unit)
        if not (quantity.lo <= magnitude <= quantity.hi):
            raise SpecError(
                "implausible_magnitude",
                f"{given.symbol}={magnitude} not in [{quantity.lo},{quantity.hi}]{quantity.unit}",
            )

    if spec.result_units not in declared.unknown.units:
        raise SpecError("unexpected_unit", f"result_units:{spec.result_units}")
    return spec


def parse_and_validate(payload: object, scenario_id: str) -> Spec:
    return validate_spec(parse_spec(payload), scenario_id)


# --------------------------------------------------------------------- parsing
def _extract_array(text: str) -> tuple[list | None, str | None]:
    """Pull the JSON array out of an LLM answer.

    The provider has no server-side JSON schema (DESIGN §2.5), so the array may arrive
    fenced, prefixed with a sentence, or not at all. Fences are stripped and the outermost
    ``[...]`` is taken; anything else is refused rather than guessed at.
    """
    if not isinstance(text, str) or not text.strip():
        return None, "empty_content"
    body = text.strip()
    if body.startswith("```"):
        first_newline = body.find("\n")
        body = body[first_newline + 1 :] if first_newline != -1 else ""
        strip_at = body.rfind("```")
        if strip_at != -1:
            body = body[:strip_at]
        body = body.strip()
    start = body.find("[")
    end = body.rfind("]")
    candidate = body[start : end + 1] if start != -1 and end > start else body
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return None, f"unparseable_json"
    if isinstance(payload, dict):
        payload = [payload]  # a single object is tolerated; the schema is the array
    if not isinstance(payload, list):
        return None, "not_a_list"
    return payload, None


def parse_specs(text: str, scenario_id: str) -> tuple[list[Spec], list[str]]:
    """Every valid spec plus one machine reason per rejected object."""
    payloads, shape_error = _extract_array(text)
    if shape_error is not None:
        return [], [shape_error]
    specs: list[Spec] = []
    rejected: list[str] = []
    for position, payload in enumerate(payloads):
        try:
            specs.append(parse_and_validate(payload, scenario_id))
        except SpecError as exc:
            rejected.append(f"{position}:{exc.reason}")
    return specs, rejected


def prompt(scenario_id: str, count: int) -> str:
    """The prompt-enforced schema (no provider-side ``json_schema`` exists)."""
    declared = SCENARIOS[scenario_id]
    givens = "\n".join(
        f'  - "{q.symbol}" in {q.unit} (allowed: {", ".join(q.units)}), magnitude between '
        f"{_ascii(q.lo)} and {_ascii(q.hi)} {q.unit}"
        for q in declared.givens
    )
    unknown = declared.unknown
    return (
        "You design physics exercise variants for an Italian teaching service. "
        "Return ONLY a JSON array, no prose and no code fences, of exactly "
        f"{count} independent objects.\n"
        'Each object: {"scenario": string, "givens": [{"symbol": string, "value": number, '
        '"unit": string}], "unknown": string, "ask": string, "result_units": string}\n'
        f'The "scenario" of every object is exactly "{scenario_id}".\n'
        f"Scenario: {declared.brief}.\n"
        f'Every object asks for the quantity "{unknown.symbol}" (unit {unknown.unit}), so '
        f'"unknown" is "{unknown.symbol}" and the "result_units" is "{unknown.unit}".\n'
        "Provide exactly these givens, with these symbols:\n"
        f"{givens}\n"
        "Rules: values are integers or exact decimals, never text and never a formula; "
        "units must be one of the allowed spellings; never state or compute the answer; "
        "all quantities must be physically plausible for the scenario; the objects must "
        "differ from each other in their numbers.\n"
    )


def _ascii(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
