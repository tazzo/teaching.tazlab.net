"""Spec → ``Item``: the model proposes a scenario, SymPy derives and verifies the answer.

The model never produces an answer (DESIGN §2.5). It proposes *givens* — symbols, exact
values, units — and this module turns that proposal into exactly the same kind of ``Item``
a template generator produces: the same ``params`` tuple, the same figure schema, and the
same independent verification, because the finished item is checked by the *existing*
physics topic's ``verify()`` (``uniform.py`` / ``accelerated.py``), not by a parallel
copy of the physics.

Reverse construction still holds, one level up: the givens are the parameters and the
answer is a projection of them, solved through ``solveset`` (via
``core.verify.real_solutions``, which is the only API that admits "I don't know" instead of
returning a plausible empty set), then cross-checked by substitution. Construction-time
impossibilities raise :class:`~app.llm.spec.SpecError`; physical inconsistencies are left
to ``topic.verify()`` so that a bad proposal is *discarded*, never silently repaired.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

from sympy import Expr, Rational, Symbol

from app.core.units import convert, fmt
from app.core.verify import no_floats, real_solutions, satisfies
from app.generators.base import Answer, Item, Step
from app.generators.registry import TOPICS
from app.llm.spec import SCENARIOS, ScenarioSpec, Spec, SpecError
from app.render.figure import cartesian_trace, linear_samples

S = Symbol("s")
V = Symbol("v")
V0 = Symbol("v0")
A = Symbol("a")
T = Symbol("t")
T1 = Symbol("t1")
T2 = Symbol("t2")
S1 = Symbol("s1")
S2 = Symbol("s2")
V1 = Symbol("v1")
V2 = Symbol("v2")
C = Symbol("c")
T_STOP = Symbol("t_stop")


def _sym(value: Fraction) -> Rational:
    """An exact ``Fraction`` as an exact SymPy rational — never a Float."""
    return Rational(value.numerator, value.denominator)


def _solve(expr: Expr, unknown: Symbol, subs: dict[Symbol, Rational]) -> Fraction:
    """The unique exact real root of ``expr`` for ``unknown`` after substitution."""
    reduced = expr.subs(subs)
    if not no_floats(reduced):
        raise SpecError("float_atom", str(reduced))
    values = real_solutions(reduced, unknown)
    if values is None:
        raise SpecError("undecidable", str(reduced))
    if len(values) != 1:
        raise SpecError("not_a_unique_solution", str(reduced))
    value = values[0]
    if not isinstance(value, Rational):
        raise SpecError("non_rational_solution", str(value))
    if not satisfies(reduced, unknown, value):
        raise SpecError("solution_does_not_satisfy", str(reduced))
    return Fraction(int(value.p), int(value.q))


def _canonical_givens(spec: Spec, declared: ScenarioSpec) -> dict[str, Fraction]:
    """Every given converted to the scenario's canonical unit (exact rationals)."""
    quantities = {q.symbol: q for q in declared.givens}
    return {
        given.symbol: convert(given.value, given.unit, quantities[given.symbol].unit)
        for given in spec.givens
    }


def _check_answer(declared: ScenarioSpec, value: Fraction) -> Fraction:
    """The answer must land in the scenario's realistic range (§2.10)."""
    quantity = declared.unknown
    if not (quantity.lo <= value <= quantity.hi):
        raise SpecError(
            "implausible_answer",
            f"{quantity.symbol}={value} not in [{quantity.lo},{quantity.hi}]{quantity.unit}",
        )
    return value


def _item(
    declared: ScenarioSpec,
    *,
    seed: int,
    index: int,
    params: dict[str, Fraction],
    value: Fraction,
    value_unit: str,
    statement_key: str,
    steps: tuple[Step, ...],
    figure: dict | None,
) -> Item:
    return Item(
        topic=declared.topic_id,
        difficulty=declared.difficulty,
        seed=seed,
        index=index,
        params=params,
        statement_key=statement_key,
        steps=steps,
        answer=Answer(
            latex=f"{fmt(value)}\\,\\text{{{value_unit}}}",
            kind="scalar_with_unit",
            payload={"value": [fmt(value)], "unit": [value_unit]},
        ),
        figure=figure,
    )


# ------------------------------------------------------------------- builders
def _build_uniform_one_object(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    v, t = given["v"], given["t"]
    s = _check_answer(declared, _solve(S - V * T, S, {V: _sym(v), T: _sym(t)}))
    return _item(
        declared, seed=seed, index=index,
        params={"v": v, "t": t, "s": s}, value=s, value_unit="m",
        statement_key="stmt.uniform_easy",
        steps=(
            Step("step.formula", "s = v \\cdot t"),
            Step("step.substitute", f"s = {fmt(v)}\\,\\text{{m/s}} \\cdot {fmt(t)}\\,\\text{{s}}"),
            Step("step.result", f"s = {fmt(s)}\\,\\text{{m}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m", t_max=t, samples=linear_samples(v, t),
            trace_label="trace.position", phase_label="phase.uniform",
            markers=[(t, s, "marker.asked_instant")],
        ),
    )


def _build_uniform_unit_conversion(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    v_kmh, t = given["v_kmh"], given["t"]
    v = convert(v_kmh, "km/h", "m/s")
    s = _check_answer(declared, _solve(S - V * T, S, {V: _sym(v), T: _sym(t)}))
    return _item(
        declared, seed=seed, index=index,
        params={"v_kmh": v_kmh, "v": v, "t": t, "s": s}, value=s, value_unit="m",
        statement_key="stmt.uniform_medium",
        steps=(
            Step("step.convert", f"{fmt(v_kmh)}\\,\\text{{km/h}} = {fmt(v)}\\,\\text{{m/s}}"),
            Step("step.formula", "s = v \\cdot t"),
            Step("step.result", f"s = {fmt(s)}\\,\\text{{m}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m", t_max=t, samples=linear_samples(v, t),
            trace_label="trace.position", phase_label="phase.uniform",
            markers=[(t, s, "marker.asked_instant")],
        ),
    )


def _build_uniform_graph_reading(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    t1, s1, t2, s2 = given["t1"], given["s1"], given["t2"], given["s2"]
    if t2 <= t1:
        raise SpecError("degenerate_interval", f"{t1} -> {t2}")
    v = _check_answer(
        declared,
        _solve(V * (T2 - T1) - (S2 - S1), V, {T1: _sym(t1), S1: _sym(s1), T2: _sym(t2), S2: _sym(s2)}),
    )
    # The points must describe motion from the origin; a proposal that does not is left
    # to ``topic.verify()`` (UniformMotion.verify → "point_not_on_the_line") so the
    # physics has exactly one home.
    t_max = Fraction(t2) * Fraction(6, 5)
    return _item(
        declared, seed=seed, index=index,
        params={"v": v, "t1": t1, "t2": t2, "s1": s1, "s2": s2}, value=v, value_unit="m/s",
        statement_key="stmt.uniform_hard",
        steps=(
            Step("step.read_points", f"P_1({fmt(t1)}; {fmt(s1)})\\quad P_2({fmt(t2)}; {fmt(s2)})"),
            Step("step.slope", f"v = \\frac{{\\Delta s}}{{\\Delta t}} = \\frac{{{fmt(s2 - s1)}}}{{{fmt(t2 - t1)}}}"),
            Step("step.result", f"v = {fmt(v)}\\,\\text{{m/s}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m", t_max=t_max, samples=linear_samples(v, t_max),
            trace_label="trace.position", phase_label="phase.uniform",
            markers=[(t1, s1, "marker.point_1"), (t2, s2, "marker.point_2")],
        ),
    )


def _build_uniform_sound_distance(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    c, t = given["c"], given["t"]
    s = _check_answer(declared, _solve(S - C * T, S, {C: _sym(c), T: _sym(t)}))
    return _item(
        declared, seed=seed, index=index,
        params={"v": c, "c": c, "t": t, "s": s}, value=s, value_unit="m",
        statement_key="stmt.uniform_sound",
        steps=(
            Step("step.formula", "s = c \\cdot t"),
            Step("step.substitute", f"s = {fmt(c)}\\,\\text{{m/s}} \\cdot {fmt(t)}\\,\\text{{s}}"),
            Step("step.result", f"s = {fmt(s)}\\,\\text{{m}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m", t_max=t, samples=linear_samples(c, t),
            trace_label="trace.position", phase_label="phase.uniform",
            markers=[(t, s, "marker.asked_instant")],
        ),
    )


def _build_accelerated_from_rest(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    a, t = given["a"], given["t"]
    v0 = Fraction(0)
    v = _check_answer(declared, _solve(V - A * T, V, {A: _sym(a), T: _sym(t)}))
    s = v0 * t + a * t * t / 2
    t_max = t * Fraction(5, 4)
    return _item(
        declared, seed=seed, index=index,
        params={"a": a, "t": t, "v0": v0, "v": v, "s": s}, value=v, value_unit="m/s",
        statement_key="stmt.accelerated_easy",
        steps=(
            Step("step.formula_v", "v = a \\cdot t"),
            Step("step.substitute", f"v = {fmt(a)} \\cdot {fmt(t)}"),
            Step("step.result", f"v = {fmt(v)}\\,\\text{{m/s}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m/s", t_max=t_max,
            samples=[(Fraction(0), v0), (t_max, v0 + a * t_max)],
            trace_label="trace.velocity", phase_label="phase.accelerated",
            markers=[(t, v, "marker.asked_instant")],
        ),
    )


def _build_accelerated_with_v0(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    v0, a = given["v0"], given["a"]
    if a >= 0:
        raise SpecError("not_a_braking_case", f"a={a}")
    t_stop = _check_answer(
        declared, _solve(V0 + A * T_STOP, T_STOP, {V0: _sym(v0), A: _sym(a)})
    )
    s_stop = v0 * t_stop + a * t_stop * t_stop / 2
    t_max = t_stop * Fraction(5, 4)
    return _item(
        declared, seed=seed, index=index,
        params={"a": a, "v0": v0, "t_stop": t_stop, "s_stop": s_stop},
        value=t_stop, value_unit="s",
        statement_key="stmt.accelerated_medium",
        steps=(
            Step("step.formula", "0 = v_0 + a\\,t"),
            Step("step.substitute", f"t = \\frac{{-{fmt(v0)}}}{{{fmt(a)}}}"),
            Step("step.result", f"t = {fmt(t_stop)}\\,\\text{{s}}"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m/s", t_max=t_max,
            samples=[(Fraction(0), v0), (t_max, v0 + a * t_max)],
            trace_label="trace.velocity", phase_label="phase.accelerated",
            markers=[(t_stop, Fraction(0), "marker.stop")],
        ),
    )


def _build_accelerated_derive_a(spec, declared, seed, index) -> Item:
    given = _canonical_givens(spec, declared)
    t1, v1, t2, v2 = given["t1"], given["v1"], given["t2"], given["v2"]
    if t2 <= t1:
        raise SpecError("degenerate_interval", f"{t1} -> {t2}")
    a = _check_answer(
        declared,
        _solve(V1 + A * (T2 - T1) - V2, A, {T1: _sym(t1), V1: _sym(v1), T2: _sym(t2), V2: _sym(v2)}),
    )
    v0 = v1 - a * t1
    t_max = Fraction(t2) * Fraction(5, 4)
    return _item(
        declared, seed=seed, index=index,
        params={"a": a, "v0": v0, "t1": t1, "t2": t2, "v1": v1, "v2": v2},
        value=a, value_unit="m/s^2",
        statement_key="stmt.accelerated_hard",
        steps=(
            Step("step.read_points", f"v({fmt(t1)}) = {fmt(v1)}\\,\\text{{m/s}},\\quad v({fmt(t2)}) = {fmt(v2)}\\,\\text{{m/s}}"),
            Step("step.slope", f"a = \\frac{{\\Delta v}}{{\\Delta t}} = \\frac{{{fmt(v2 - v1)}}}{{{fmt(t2 - t1)}}}"),
            Step("step.result", f"a = {fmt(a)}\\,\\text{{m/s}}^2"),
        ),
        figure=cartesian_trace(
            x_unit="s", y_unit="m/s", t_max=t_max,
            samples=[(Fraction(0), v0), (t_max, v0 + a * t_max)],
            trace_label="trace.velocity", phase_label="phase.accelerated",
            markers=[(t2, v2, "marker.second_reading")],
        ),
    )


BUILDERS: dict[str, Callable[[Spec, ScenarioSpec, int, int], Item]] = {
    "uniform_one_object": _build_uniform_one_object,
    "uniform_unit_conversion": _build_uniform_unit_conversion,
    "uniform_graph_reading": _build_uniform_graph_reading,
    "uniform_sound_distance": _build_uniform_sound_distance,
    "accelerated_from_rest": _build_accelerated_from_rest,
    "accelerated_with_v0": _build_accelerated_with_v0,
    "accelerated_derive_a": _build_accelerated_derive_a,
}


def spec_to_item(spec: Spec, *, seed: int, index: int) -> Item:
    """Turn a validated spec into an ``Item``, then verify it with the topic's own rules.

    Solving and verifying happen here so a proposal that cannot be turned into a *sound*
    item fails as one thing: the topic's ``verify()`` is the only judge, exactly as on the
    template path. A failure raises :class:`SpecError`, and the caller discards the spec.
    """
    declared = SCENARIOS.get(spec.scenario)
    if declared is None:
        raise SpecError("unknown_scenario", spec.scenario)
    builder = BUILDERS.get(spec.scenario)
    if builder is None:
        raise SpecError("no_builder", spec.scenario)

    item = builder(spec, declared, seed, index)
    try:
        result = TOPICS[declared.topic_id].verify(item)
    except Exception as exc:  # noqa: BLE001 - several verifiers raise on a missing param key
        # A verifier that raises is a rejection, not a crash: the spec is arbitrary input
        # and an exception escaping here would turn a bad proposal into a 500.
        raise SpecError("verification_raised", f"{type(exc).__name__}: {exc}") from exc
    if not result.ok:
        raise SpecError("verification_failed", result.reason or "unspecified")
    return item


def scenarios() -> tuple[str, ...]:
    """The scenario ids this module can build, in a deterministic order."""
    return tuple(sorted(BUILDERS))
