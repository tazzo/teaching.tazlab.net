"""Piecewise motion — a configurable sequence of segments, read off a graph.

Operator's spec (2026-09-24): the student configures how many segments the motion has
(accelerated → uniform → decelerated → accelerated, or any mix), whether the graph shows
velocity or position, whether the units are SI or converted, and what must be read off the
graph. The graph marks the division with dashed guides — "una linea segmentata che fa
vedere questa cosa" — and starts at the origin, so the axes sit in the bottom-left corner.

Operator's spec (2026-09-30): the page is no longer a form to fill but a graph mill — the
teacher clicks and gets a graph to build oral questions on. So every choice defaults to
`random` (segment kinds, plotted quantity, unit system), the number of segments is a
plain 3/4/5 choice instead of an add/remove list, and the "what must the student read"
control is gone: the generator draws the reading itself, one the drawn motion can actually
answer. The statement stays out of the page for the same reason (the teacher asks), but it
is still generated and still verified — the item is a normal exercise for every other
consumer (PDF export, tests).

Motion model: v(t) is piecewise linear in time, hence s(t) is piecewise quadratic. Each
segment is `uniform` (v constant), `accelerate` (v rises) or `decelerate` (v falls, never
below zero). Continuity is by construction: a segment's end velocity is the next segment's
start velocity. All arithmetic is exact (Fraction); nothing is re-solved in the browser.

Unit policy — one rule, stated once: **time is always in seconds**; a unit system is a
pair of exact scales (velocity, position) plus the labels the axes and the answer carry.
The acceleration answer stays in m/s², so a converted variant makes the student convert
before dividing; the steps show that conversion. The graph axes carry the units, and the
statements deliberately do not repeat them.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

from app.core.units import fmt, fmt_reading, unit_latex
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step

UNIFORM = "uniform"
ACCELERATE = "accelerate"
DECELERATE = "decelerate"
SEGMENT_KINDS = (UNIFORM, ACCELERATE, DECELERATE)

VELOCITY = "velocity"
POSITION = "position"
QUANTITIES = (VELOCITY, POSITION)

RANDOM = "random"

KMH_PER_MS = Fraction(18, 5)      # 1 m/s = 3.6 km/h, exactly


@dataclass(frozen=True)
class UnitSystem:
    """A unit system is two exact scales plus the labels they carry.

    `velocity_scale` maps an SI speed (m/s) onto `velocity_unit`, `position_scale` maps an
    SI length (m) onto `position_unit`: a converted item is the *same* motion written
    differently, never a redrawn one, and every conversion in the module is one multiply.
    """

    id: str
    label_key: str
    velocity_unit: str
    velocity_scale: Fraction
    position_unit: str
    position_scale: Fraction

    @property
    def is_si(self) -> bool:
        return self.velocity_scale == 1 and self.position_scale == 1


SI_SYSTEM = UnitSystem("si", "config.units.si", "m/s", Fraction(1), "m", Fraction(1))
KMH_SYSTEM = UnitSystem("kmh", "config.units.kmh", "km/h", KMH_PER_MS, "km",
                        Fraction(1, 1000))
CM_SYSTEM = UnitSystem("cm", "config.units.cm", "cm/s", Fraction(100), "cm", Fraction(100))
UNIT_SYSTEMS = (SI_SYSTEM, KMH_SYSTEM, CM_SYSTEM)
UNIT_SYSTEM_IDS = tuple(system.id for system in UNIT_SYSTEMS)
SYSTEMS_BY_ID = {system.id: system for system in UNIT_SYSTEMS}
# a drawn figure names its system by the unit it labels the axis with, and the verifier
# reads the answer back from the figure alone — so the figure must lead back to a system
SYSTEM_BY_VELOCITY_UNIT = {system.velocity_unit: system for system in UNIT_SYSTEMS}
SYSTEM_BY_POSITION_UNIT = {system.position_unit: system for system in UNIT_SYSTEMS}

VELOCITY_AT = "velocity_at"
DISTANCE = "distance"
ACCELERATION = "acceleration"
ASKS = (VELOCITY_AT, DISTANCE, ACCELERATION)

SEGMENT_COUNTS = (3, 4, 5)
DEFAULT_SEGMENT_COUNT = SEGMENT_COUNTS[0]
_COUNT_REASON = f"segment count must be one of {list(SEGMENT_COUNTS)}"

PHASE_LABELS = {UNIFORM: "phase.uniform", ACCELERATE: "phase.accelerated",
                DECELERATE: "phase.decelerated"}

@dataclass(frozen=True)
class Segment:
    kind: str
    duration: Fraction          # s
    v_start: Fraction           # m/s
    v_end: Fraction             # m/s

    @property
    def acceleration(self) -> Fraction:
        return (self.v_end - self.v_start) / self.duration

    def position_after(self, duration: Fraction) -> Fraction:
        """Distance covered in the first `duration` seconds of this segment."""
        return self.v_start * duration + self.acceleration * duration * duration / 2


class SegmentMotion:
    id = "physics.kinematics.segments"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.physics.kinematics.segments"
    scenarios: tuple[str, ...] = ()

    # ------------------------------------------------------------- options ---
    def default_options(self) -> dict:
        """What the page shows before anyone touches it: everything drawn at random."""
        return {
            "count": DEFAULT_SEGMENT_COUNT,
            "kinds": [RANDOM] * DEFAULT_SEGMENT_COUNT,
            "quantity": RANDOM,
            "units": RANDOM,
        }

    def validate_options(self, options: dict) -> dict:
        """Normalise the configurator's choices; ValueError carries the machine reason."""
        count = self._segment_count(options.get("count"))
        # An absent list means "draw one kind per segment"; an empty one is a client bug,
        # and a length that disagrees with the count is a form whose two fields contradict
        # each other — both are refused rather than quietly replaced.
        raw_kinds = options.get("kinds")
        if raw_kinds is None:
            raw_kinds = [RANDOM] * count
        if not isinstance(raw_kinds, list) or len(raw_kinds) != count:
            raise ValueError(f"kinds must list one entry per segment ({count})")
        kinds = [str(kind) for kind in raw_kinds]
        unknown = [kind for kind in kinds if kind not in SEGMENT_KINDS + (RANDOM,)]
        if unknown:
            raise ValueError(f"unknown segment kinds: {unknown}")
        quantity = str(options.get("quantity", RANDOM))
        if quantity not in QUANTITIES + (RANDOM,):
            raise ValueError(f"unknown quantity: {quantity}")
        units = str(options.get("units", RANDOM))
        if units not in UNIT_SYSTEM_IDS + (RANDOM,):
            raise ValueError(f"unknown unit system: {units}")
        # The page no longer offers the reading; a caller that names one still gets it,
        # because the item's answer is that reading and the verifier reads it back.
        ask = options.get("ask")
        if ask is not None:
            ask = str(ask)
            if ask not in ASKS:
                raise ValueError(f"unknown ask: {ask}")
            if ask == ACCELERATION and all(kind == UNIFORM for kind in kinds):
                # a uniform-only motion has zero acceleration in every segment: there would
                # be nothing to read. Rejected here with a reason the client can show.
                raise ValueError(
                    "acceleration needs at least one accelerated or decelerated segment")
        resolved = {"count": count, "kinds": kinds, "quantity": quantity, "units": units}
        if ask is not None:
            resolved["ask"] = ask
        return resolved

    @staticmethod
    def _segment_count(raw) -> int:
        """The number of segments, as the 3/4/5 a select offers (a string is a client)."""
        if raw is None:
            return DEFAULT_SEGMENT_COUNT
        try:
            count = int(str(raw).strip())
        except ValueError:
            raise ValueError(_COUNT_REASON) from None
        if count not in SEGMENT_COUNTS:
            raise ValueError(_COUNT_REASON)
        return count

    def resolve(self, rng: random.Random, options: dict) -> dict:
        """Draw the `random` choices — per item, from that item's own rng.

        Done here rather than in `validate_options` because a random choice belongs to the
        exercise, not to the request: two items from one click may differ, and the same
        seed must still reproduce each of them exactly.
        """
        resolved = dict(options)
        resolved["kinds"] = [rng.choice(SEGMENT_KINDS) if kind == RANDOM else kind
                             for kind in options["kinds"]]
        resolved["quantity"] = (rng.choice(QUANTITIES) if options["quantity"] == RANDOM
                                else options["quantity"])
        resolved["units"] = (rng.choice(UNIT_SYSTEM_IDS) if options["units"] == RANDOM
                             else options["units"])
        # the reading is drawn too: one the drawn motion can actually answer
        resolved["ask"] = options.get("ask") or self._draw_ask(rng, resolved["kinds"])
        return resolved

    @staticmethod
    def _draw_ask(rng: random.Random, kinds: list[str]) -> str:
        """A reading the motion supports: an acceleration needs a segment that changes."""
        candidates = [VELOCITY_AT, DISTANCE]
        if any(kind != UNIFORM for kind in kinds):
            candidates.append(ACCELERATION)
        return rng.choice(candidates)

    def configurer(self) -> list[dict]:
        """The page's configurator, described once so the client renders it generically."""
        return [
            {
                "id": "count", "kind": "select", "label_key": "config.segment_count",
                "hint_key": "config.segment_count_hint",
                "choices": [{"value": str(count), "label_key": f"config.count.{count}"}
                            for count in SEGMENT_COUNTS],
            },
            {
                # one selector per segment, as many as the count field says: a motion with
                # random kinds in every segment is the default, and each row can be pinned
                "id": "kinds", "kind": "segment_kinds", "label_key": "config.segments",
                "hint_key": "config.segments_hint", "count_from": "count",
                "choices": [{"value": RANDOM, "label_key": "config.kind.random"}]
                + [{"value": kind, "label_key": PHASE_LABELS[kind]} for kind in SEGMENT_KINDS],
            },
            {
                "id": "quantity", "kind": "select", "label_key": "config.quantity",
                "hint_key": "config.quantity_hint",
                "choices": [{"value": RANDOM, "label_key": "config.quantity.random"},
                            {"value": VELOCITY, "label_key": "config.quantity.velocity"},
                            {"value": POSITION, "label_key": "config.quantity.position"}],
            },
            {
                "id": "units", "kind": "select", "label_key": "config.units",
                "hint_key": "config.units_hint",
                "choices": [{"value": RANDOM, "label_key": "config.units.random"}]
                + [{"value": system.id, "label_key": system.label_key}
                   for system in UNIT_SYSTEMS],
            },
        ]

    # -------------------------------------------------------------- motion ---
    def _build_segments(self, rng: random.Random, kinds: list[str], difficulty: str,
                        pinned: int | None = None, pinned_a: int | None = None,
                        pinned_duration: Fraction | None = None) -> list[Segment]:
        """Draw durations and velocities; continuity holds by construction.

        `pinned` names the segment the question points at. That segment gets an exact
        integer acceleration (Δv = a·Δt), because a student reading a graph should not be
        asked for 3/7 m/s²; the segments before it are bounded so the pinned one fits.
        """
        if difficulty == "easy":
            v_top, d_lo, d_hi = 12, 4, 8
        elif difficulty == "medium":
            v_top, d_lo, d_hi = 20, 3, 9
        else:
            v_top, d_lo, d_hi = 25, 2, 6

        floor, ceiling = 0, v_top
        if pinned is not None and pinned_a is not None and kinds[pinned] != UNIFORM:
            # Clamp the requested acceleration to what the range can hold: a 3 m/s² ramp
            # over 5 s needs 15 m/s of room, which the "easy" range does not have.
            room = max(1, (v_top - 2) // int(pinned_duration or 5))
            pinned_a = max(1, min(pinned_a, room))
            span = pinned_a * int(pinned_duration or 5)
            if kinds[pinned] == ACCELERATE:
                ceiling = v_top - span          # leave room to rise
            else:
                floor = span                    # leave room to fall
        floor = max(floor, 0)

        segments: list[Segment] = []
        # a motion may start from rest — or from a speed the pinned segment needs
        v = Fraction(rng.randint(floor, max(floor, min(4, ceiling))))
        for index, kind in enumerate(kinds):
            duration = (pinned_duration if index == pinned and pinned_duration else
                        Fraction(rng.randint(d_lo, d_hi)))
            if index == pinned and pinned_a is not None and kind != UNIFORM:
                span = Fraction(pinned_a) * duration
                if kind == DECELERATE and v - span <= 0:
                    # The pinned deceleration would take the motion to a stop or below.
                    # Lifting the segments drawn so far by one constant is the only repair
                    # that changes no Δv: their kinds, accelerations and the shared boundary
                    # sample all survive, and the drawing continues above the answer's own
                    # segment, which is the one the question points at.
                    lift = span + 1 - v
                    segments = [Segment(seg.kind, seg.duration, seg.v_start + lift,
                                        seg.v_end + lift) for seg in segments]
                    v = v + lift
                v_end = v + span if kind == ACCELERATE else v - span
            elif kind == UNIFORM:
                v_end = v if v > 0 else Fraction(rng.randint(max(2, floor), max(ceiling, 2)))
            elif kind == ACCELERATE:
                # Δv is a whole multiple of the duration, so the acceleration is an integer
                # m/s² and every drawn coordinate is a terminating decimal: a school graph
                # shows v = 1, 2, 3 m/s, not v = 5/3 m/s
                headroom = min(6, ceiling - int(v))
                step = max(1, rng.randint(1, headroom)) if headroom >= 1 else 1
                v_end = v + Fraction(step) * duration
            else:                                           # decelerate
                # The speed it gives up is at most 3 m/s and at most half of what it has:
                # the segment always really decelerates and never reaches a speed the next
                # one cannot continue from, so consecutive decelerating segments — which a
                # random draw produces — stay continuous instead of restarting at a lift.
                v_end = v - min(Fraction(3), v / 2)
                if v_end == v:
                    # nothing to give up (the motion is at rest): lift the start instead,
                    # which touches nothing drawn before it because it is the first segment
                    v = Fraction(rng.randint(floor + 1, max(floor + 1, min(4, ceiling))))
                    v_end = v - min(Fraction(3), v / 2)
            segments.append(Segment(kind, duration, v, v_end))
            v = v_end

        if all(seg.v_start == seg.v_end == 0 for seg in segments):
            # A motion that never leaves rest is a flat line on the axis: there is nothing
            # to read off it. The whole motion is lifted by one constant rather than one
            # segment being moved, because neighbouring segments share their boundary
            # sample and that shared sample *is* the continuity the verifier checks.
            segments = [Segment(seg.kind, seg.duration, seg.v_start + 2, seg.v_end + 2)
                        for seg in segments]
        return segments

    @staticmethod
    def _position_at(segments: list[Segment], t: Fraction) -> Fraction:
        travelled = Fraction(0)
        elapsed = Fraction(0)
        for seg in segments:
            if t <= elapsed + seg.duration:
                return travelled + seg.position_after(t - elapsed)
            travelled += seg.position_after(seg.duration)
            elapsed += seg.duration
        return travelled

    @staticmethod
    def _velocity_at(segments: list[Segment], t: Fraction) -> Fraction:
        elapsed = Fraction(0)
        for seg in segments:
            if t <= elapsed + seg.duration:
                return seg.v_start + seg.acceleration * (t - elapsed)
            elapsed += seg.duration
        return segments[-1].v_end

    # ------------------------------------------------------------ generate ---
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        opts = self.resolve(rng, self.validate_options(options or {}))
        kinds, quantity, ask = opts["kinds"], opts["quantity"], opts["ask"]
        system = SYSTEMS_BY_ID[opts["units"]]
        if ask == ACCELERATION and all(kind == UNIFORM for kind in kinds):
            # the caller named the reading but left the kinds random, and every drawn
            # segment came out uniform: refuse rather than answer a question that has none
            raise ValueError(
                "acceleration needs at least one accelerated or decelerated segment")
        # The question names a segment (or none, for the total distance). For the two
        # asks that read an acceleration, the named segment is the first non-uniform one:
        # asking "what is the acceleration here" about a uniform segment has no answer,
        # and pointing at the first accelerated one is what the statement promises.
        seg_index: int | None = None
        pinned_a: int | None = None
        pinned_duration: Fraction | None = None
        if ask == ACCELERATION:
            seg_index = next(i for i, kind in enumerate(kinds) if kind != UNIFORM)
            pinned_a = rng.randint(1, 3)                # 1..3 m/s², always an integer
            pinned_duration = Fraction(5)               # 5 s: Δv = 18a km/h stays integer
        elif ask == VELOCITY_AT:
            seg_index = rng.randrange(len(kinds))
            pinned_a = rng.randint(1, 3) if kinds[seg_index] != UNIFORM else None
            # Even duration: the halfway instant is then an exact integer second AND one of
            # the drawn samples, which is what makes the position-graph reading exact.
            span_even = [d for d in range(4, 9) if d % 2 == 0]
            pinned_duration = Fraction(rng.choice(span_even))

        segments = self._build_segments(rng, kinds, difficulty, pinned=seg_index,
                                        pinned_a=pinned_a, pinned_duration=pinned_duration)
        total_time = sum(seg.duration for seg in segments)

        # where the question points, and the exact SI value it asks for
        t_ask: Fraction | None = None
        if ask == VELOCITY_AT:
            # an integer instant: a reading half-way through an odd second is not something
            # a student can mark on the axis
            t_ask = (sum(seg.duration for seg in segments[:seg_index])
                     + Fraction(segments[seg_index].duration // 2))
            value_si = self._velocity_at(segments, t_ask)
        elif ask == ACCELERATION:
            value_si = segments[seg_index].acceleration
        else:
            t_ask = total_time
            value_si = self._position_at(segments, total_time)

        # the answer, in the unit the student will write — the graph's own unit (time stays
        # in seconds, and an acceleration is always SI, so it is the one reading that has
        # to be converted before dividing)
        value = (value_si * system.velocity_scale if ask == VELOCITY_AT
                 else value_si * system.position_scale if ask == DISTANCE else value_si)
        answer_unit = {"velocity_at": system.velocity_unit,
                       "distance": system.position_unit}.get(ask, "m/s^2")

        params = {
            "n": Fraction(len(segments)),
            "t_total": total_time,
            "t_ask": t_ask if t_ask is not None else Fraction(0),
            "seg": Fraction((seg_index + 1) if seg_index is not None else 0),
            "value": value,
            "value_si": value_si,
        }
        statement_key = f"stmt.segments_{ask}_{quantity}"
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=statement_key,
            steps=self._steps(segments, ask, seg_index, t_ask, system, quantity),
            answer=Answer(
                # the caret in m/s^2 cannot live inside \text{}: KaTeX refuses the formula
                latex=f"{fmt_reading(value)}\\,{unit_latex(answer_unit)}",
                kind="scalar_with_unit",
                payload={"value": [fmt_reading(value)], "unit": [answer_unit]},
            ),
            figure=self._figure(segments, quantity, system, t_ask, ask, seg_index),
        )

    def _steps(self, segments, ask, seg_index, t_ask, system, quantity) -> tuple[Step, ...]:
        """The derivation, in the units of the graph, with the conversion written out."""
        unit_v, unit_s = system.velocity_unit, system.position_unit
        converted = not system.is_si
        rows: list[Step] = [Step("step.read_segments", f"n = {len(segments)}")]
        if ask == ACCELERATION and seg_index is not None:
            seg = segments[seg_index]
            if quantity == POSITION:
                # A position-time graph has no velocity axis: the velocity is a *slope* in
                # two instants, and the acceleration is how much that slope changed. The
                # slopes are shown in the graph's own units (km/s when the position axis is
                # in kilometres), then converted — never shown as a mixed-up hybrid.
                half = seg.duration / 2
                v_first = seg.v_start + seg.acceleration * half / 2     # m/s
                v_second = seg.v_end + seg.acceleration * half / 2      # m/s
                unit_slope = f"{unit_s}/s"
                rows.append(Step("step.read_slopes",
                                 f"v_1 = \\frac{{\\Delta s_1}}{{\\Delta t_1}} = "
                                 f"{fmt_reading(v_first * system.position_scale)}"
                                 f"\\,\\text{{{unit_slope}}},"
                                 f"\\quad v_2 = \\frac{{\\Delta s_2}}{{\\Delta t_2}} = "
                                 f"{fmt_reading(v_second * system.position_scale)}"
                                 f"\\,\\text{{{unit_slope}}}"))
                if converted:
                    rows.append(Step("step.convert",
                                     f"v_1 = {fmt_reading(v_first)}\\,\\text{{m/s}},"
                                     f"\\quad v_2 = {fmt_reading(v_second)}\\,\\text{{m/s}}"))
                rows.append(Step("step.slope",
                                 f"a = \\frac{{v_2 - v_1}}{{\\Delta t}} = "
                                 f"\\frac{{{fmt_reading(v_second - v_first)}}}"
                                 f"{{{fmt_reading(half)}\\,\\text{{s}}}}"))
            else:
                delta_v = (seg.v_end - seg.v_start) * system.velocity_scale
                rows.append(Step("step.read_points",
                                 f"\\Delta v = {fmt_reading(delta_v)}\\,\\text{{{unit_v}}},"
                                 f"\\quad \\Delta t = {fmt_reading(seg.duration)}\\,\\text{{s}}"))
                if converted:
                    rows.append(Step("step.convert",
                                     f"\\Delta v = {fmt_reading(delta_v / system.velocity_scale)}"
                                     "\\,\\text{m/s}"))
                rows.append(Step("step.slope", "a = \\frac{\\Delta v}{\\Delta t}"))
        elif ask == VELOCITY_AT and t_ask is not None:
            rows.append(Step("step.read_points", f"t = {fmt_reading(t_ask)}\\,\\text{{s}}"))
            velocity_si = self._velocity_at(segments, t_ask)
            if quantity == POSITION:
                # The graph plots position: the velocity is the steepness of the curve there,
                # and the slope is read in the graph's own unit before it is re-expressed —
                # printing the SI slope under a km/h label would be a wrong answer, not a
                # different presentation of one.
                slope_si = velocity_si
                rows.append(Step("step.read_slope_at",
                                 f"v = \\frac{{\\Delta s}}{{\\Delta t}} = "
                                 f"{fmt_reading(slope_si * system.position_scale)}"
                                 f"\\,\\text{{{unit_s}/s}}"))
                if converted:
                    rows.append(Step("step.convert",
                                     f"v = {fmt_reading(slope_si)}\\,\\text{{m/s}} = "
                                     f"{fmt_reading(velocity_si * system.velocity_scale)}"
                                     f"\\,\\text{{{unit_v}}}"))
            else:
                rows.append(Step("step.read_value",
                                 f"v = {fmt_reading(velocity_si * system.velocity_scale)}"
                                 f"\\,\\text{{{unit_v}}}"))
        elif quantity == POSITION:
            # a position graph answers "how far" by itself: read where the curve is at the end
            total_time = sum(seg.duration for seg in segments)
            travelled = self._position_at(segments, total_time)
            rows.append(Step("step.read_displacement",
                             f"\\Delta s = {fmt_reading(travelled * system.position_scale)}"
                             f"\\,\\text{{{unit_s}}}"))
        else:
            rows.append(Step("step.area", "s = \\text{somma delle aree sotto il grafico } v(t)"))
            if converted:
                # the factor that turns an area in (velocity unit x s) into the answer's unit
                factor = system.position_scale / system.velocity_scale
                rows.append(Step("step.convert",
                                 f"1\\,\\text{{{unit_v}}} \\cdot \\text{{s}} = "
                                 f"{fmt(factor)}\\,\\text{{{unit_s}}}"))
        return tuple(rows)

    def _figure(self, segments, quantity, system, t_ask, ask, seg_index) -> dict:
        """One trace per segment — the division is visible at a glance — plus the guides."""
        y_unit = system.position_unit if quantity == POSITION else system.velocity_unit
        y_scale = system.position_scale if quantity == POSITION else system.velocity_scale

        traces, phases = [], []
        elapsed = Fraction(0)
        travelled = Fraction(0)
        for seg in segments:
            points = []
            subdivisions = 4
            for i in range(subdivisions + 1):
                dt = seg.duration * Fraction(i, subdivisions)
                s = travelled + seg.position_after(dt)
                raw = s if quantity == POSITION else seg.v_start + seg.acceleration * dt
                points.append((elapsed + dt, raw * y_scale))
            traces.append({
                "label_key": PHASE_LABELS[seg.kind],
                "kind": seg.kind,
                "samples": [[fmt(x), fmt(y)] for x, y in points],
            })
            phases.append({
                "label_key": PHASE_LABELS[seg.kind],
                "kind": seg.kind,
                "t_from": fmt(elapsed),
                "t_to": fmt(elapsed + seg.duration),
            })
            travelled += seg.position_after(seg.duration)
            elapsed += seg.duration

        markers = []
        if t_ask is not None:
            raw = (self._position_at(segments, t_ask) if quantity == POSITION
                   else self._velocity_at(segments, t_ask))
            markers.append({"label_key": "marker.asked_instant",
                            "at": [fmt(t_ask), fmt(raw * y_scale)]})
        elif ask == ACCELERATION and seg_index is not None:
            # the statement says "the segment shown on the graph": mark it, or the student
            # is asked about a segment the drawing never singles out
            samples = traces[seg_index]["samples"]
            middle = samples[(len(samples) - 1) // 2]
            markers.append({"label_key": "marker.asked_segment",
                            "at": [middle[0], middle[1]]})

        # The vertices of the broken line: where the motion changes, the graph bends. Drawn
        # as points so a student can SEE the readings the statement talks about.
        vertices = [{"at": traces[0]["samples"][0], "kind": traces[0]["kind"]}]
        for trace in traces:
            vertices.append({"at": trace["samples"][-1], "kind": trace["kind"]})

        guides = []
        boundary = Fraction(0)
        for seg in segments[:-1]:
            boundary += seg.duration
            guides.append({"at": fmt(boundary), "label_key": "guide.segment"})

        return {
            "kind": "kinematics",
            "origin": "corner",                 # axes in the bottom-left corner, x >= 0
            "x_unit": "s",
            "y_unit": y_unit,
            "y_label": "trace.position" if quantity == POSITION else "trace.velocity",
            "domain": {"t_min": "0", "t_max": fmt(elapsed)},
            "traces": traces,
            "vertices": vertices,
            "markers": markers,
            "guides": guides,
            "phases": phases,
        }

    # -------------------------------------------------------------- verify ---
    def verify(self, item: Item) -> VerificationResult:
        """The answer must follow from the graph as drawn — recomputed, not re-read."""
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        figure = item.figure
        if not figure or not figure.get("traces"):
            return VerificationResult(False, "missing_figure")
        if figure.get("origin") != "corner":
            return VerificationResult(False, "axes_not_at_origin")

        traces = figure["traces"]
        if len(traces) != int(item.params["n"]):
            return VerificationResult(False, "trace_count_mismatch")

        times: list[Fraction] = []
        values: list[Fraction] = []
        for index, trace in enumerate(traces):
            samples = trace["samples"]
            if len(samples) < 2:
                return VerificationResult(False, "trace_too_short")
            # a segment starts where the previous one ends: that shared sample is the
            # continuity of the motion, not a step backwards in time
            first = 1 if index else 0
            times.extend(Fraction(x) for x, _ in samples[first:])
            values.extend(Fraction(y) for _, y in samples[first:])
        if times[0] != 0:
            return VerificationResult(False, "figure_does_not_start_at_zero")   # x >= 0 always
        if any(later <= earlier for earlier, later in zip(times, times[1:])):
            return VerificationResult(False, "figure_not_monotone_in_time")
        if any(value < 0 for value in values):
            return VerificationResult(False, "negative_quantity")
        for previous, following in zip(traces, traces[1:]):
            if Fraction(previous["samples"][-1][1]) != Fraction(following["samples"][0][1]):
                return VerificationResult(False, "discontinuity_between_segments")
        for guide in figure.get("guides", []):
            if not 0 < Fraction(guide["at"]) < times[-1]:
                return VerificationResult(False, "guide_outside_domain")
        # every vertex of the broken line must be a point the traces actually pass through
        drawn = {(x, y) for trace in traces for x, y in trace["samples"]}
        for vertex in figure.get("vertices", []):
            if tuple(vertex["at"]) not in drawn:
                return VerificationResult(False, "vertex_not_on_the_line")
        # markers must sit inside the plotted box
        for marker in figure.get("markers", []):
            x, y = (Fraction(value) for value in marker["at"])
            if not 0 <= x <= times[-1] or y < 0:
                return VerificationResult(False, "marker_outside_domain")

        claimed = item.answer.payload.get("value", [None])[0]
        if claimed is None:
            return VerificationResult(False, "no_answer")
        from_graph = self._read_off_graph(item, traces)
        if from_graph is None:
            return VerificationResult(False, "unreadable_graph")
        if Fraction(claimed) != from_graph:
            # the printed answer disagrees with the drawn motion: the defect that shipped
            # once already (x²+2x+8=0 answered x=-4, x=2) must never reach a student again
            return VerificationResult(False, f"answer_disagrees_with_graph:{claimed}!={from_graph}")
        return VerificationResult(True)

    @staticmethod
    def _read_off_graph(item: Item, traces: list[dict]) -> Fraction | None:
        """Recompute the answer from the drawn samples, in the answer's own unit."""
        # the figure names its unit system on the y axis; that, not the options, is what
        # the reading below must convert back from
        positions = item.figure["y_label"] == "trace.position"
        table = SYSTEM_BY_POSITION_UNIT if positions else SYSTEM_BY_VELOCITY_UNIT
        system = table.get(item.figure["y_unit"])
        if system is None:
            return None
        ask = next(candidate for candidate in ASKS
                   if item.statement_key.startswith(f"stmt.segments_{candidate}_"))

        if ask == "distance":
            if positions:
                # the drawn axis already carries the system's own unit, so the answer is the
                # distance between the two drawn points: there is no scale to undo
                return (Fraction(traces[-1]["samples"][-1][1])
                        - Fraction(traces[0]["samples"][0][1]))
            # trapezoid rule over the drawn samples, across every segment
            area = Fraction(0)
            for trace in traces:
                samples = [(Fraction(x), Fraction(y)) for x, y in trace["samples"]]
                for (x1, y1), (x2, y2) in zip(samples, samples[1:]):
                    area += (x2 - x1) * (y1 + y2) / 2
            return area * system.position_scale / system.velocity_scale   # (u_v · s) -> u_s

        if ask == "velocity_at":
            x_ask = Fraction(item.figure["markers"][0]["at"][0])
            for trace in traces:
                samples = [(Fraction(x), Fraction(y)) for x, y in trace["samples"]]
                if not samples[0][0] <= x_ask <= samples[-1][0]:
                    continue
                if item.figure["y_label"] == "trace.velocity":
                    # a velocity graph is linear inside a segment: interpolate exactly
                    (x1, y1), (x2, y2) = samples[0], samples[-1]
                    return y1 + (y2 - y1) * (x_ask - x1) / (x2 - x1)
                # a position graph: the velocity is the tangent's slope. The asked instant is
                # drawn as a sample, and the secant through its symmetric neighbours cancels
                # the quadratic term, so this is the exact instantaneous velocity.
                at = next((i for i, (x, _) in enumerate(samples) if x == x_ask), None)
                if at is None or at == 0 or at == len(samples) - 1:
                    return None
                (xa, ya), (xb, yb) = samples[at - 1], samples[at + 1]
                slope = (yb - ya) / (xb - xa)          # position unit per second
                # the graph plots the position in its own unit while the answer is asked in
                # the system's velocity unit: the conversion is exact, never an approximation
                return slope * system.velocity_scale / system.position_scale
            return None

        # acceleration, from the segment the question names
        segment = int(item.params["seg"]) - 1
        samples = [(Fraction(x), Fraction(y)) for x, y in traces[segment]["samples"]]
        (x1, y1), (x2, y2) = samples[0], samples[-1]
        if item.figure["y_label"] == "trace.velocity":
            # a velocity graph: the acceleration IS the slope of the segment
            slope = (y2 - y1) / (x2 - x1)                            # y_unit per second
            return slope / system.velocity_scale                   # -> m/s^2
        # a position graph: the acceleration is the change of the *slope*. The average
        # velocity over each half is a secant, and their difference over half a segment is
        # the acceleration exactly — a parabola's curvature is constant.
        mid = (len(samples) - 1) // 2
        half = (x2 - x1) / 2
        v_first = (samples[mid][1] - y1) / half
        v_second = (y2 - samples[mid][1]) / half
        curvature = (v_second - v_first) / half             # position unit per second^2
        return curvature / system.position_scale            # -> m/s^2


TOPIC = SegmentMotion()
