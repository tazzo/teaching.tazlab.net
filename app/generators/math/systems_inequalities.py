"""Systems of two linear inequalities in two unknowns (DESIGN §2.10).

**The region is chosen first.** Easy picks a quadrant (two axes-aligned half-planes,
legitimately unbounded), Medium picks a wedge with two non-parallel boundaries, Hard draws
a convex quadrilateral and *derives* its four bounding constraints from the edges. Vertices
are ordered by an exact angular comparator (a slope sort is not an angular order — that bug
self-intersected 400/400 quads in the CRISP prototype) and convexity is asserted, not hoped
for.

The answer key carries the whole feasible region: the canonical ``a x + b y ≤ c`` forms,
the vertices in angular order and the recession rays of an unbounded region. The verifier
re-derives the region from the parameters, compares it with the claim, and runs an
independent sampler that classifies points from the constraints *and* from the
vertex/ray representation — a point classified inside by one and outside by the other is a
rejection.
"""

from __future__ import annotations

import random
from fractions import Fraction
from functools import cmp_to_key
from itertools import combinations
from math import gcd

from sympy import Integer, Rational, Symbol

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step

X = Symbol("x")
Y = Symbol("y")

_QUADRANT = "stmt.ineq_system_quadrant"
_WEDGE = "stmt.ineq_system_wedge"
_QUAD = "stmt.ineq_system_quad"

_SHAPE_KEYS = {1: _QUADRANT, 2: _WEDGE, 3: _QUAD}

Point = tuple[Fraction, Fraction]
Constraint = tuple[Fraction, Fraction, Fraction]


# --------------------------------------------------------------------- geometry
def _half(dx: Fraction, dy: Fraction) -> int:
    return 0 if (dy > 0 or (dy == 0 and dx > 0)) else 1


def _angular_order(points: list[Point]) -> list[Point]:
    """Counter-clockwise order around the centroid, exactly (no floats anywhere)."""
    count = len(points)
    centre = (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
    )

    def compare(left: Point, right: Point) -> int:
        dx1, dy1 = left[0] - centre[0], left[1] - centre[1]
        dx2, dy2 = right[0] - centre[0], right[1] - centre[1]
        half1, half2 = _half(dx1, dy1), _half(dx2, dy2)
        if half1 != half2:
            return -1 if half1 < half2 else 1
        cross = dx1 * dy2 - dy1 * dx2
        if cross != 0:
            return -1 if cross > 0 else 1
        norm1, norm2 = dx1 * dx1 + dy1 * dy1, dx2 * dx2 + dy2 * dy2
        if norm1 == norm2:
            return 0
        return -1 if norm1 < norm2 else 1

    return sorted(points, key=cmp_to_key(compare))


def _is_convex(ordered: list[Point]) -> bool:
    """All turns share one sign: the assertion the prototype's bug taught us to keep."""
    count = len(ordered)
    if count < 3:
        return False
    signs = set()
    for index in range(count):
        x1, y1 = ordered[index]
        x2, y2 = ordered[(index + 1) % count]
        x3, y3 = ordered[(index + 2) % count]
        cross = (x2 - x1) * (y3 - y2) - (y2 - y1) * (x3 - x2)
        if cross == 0:
            return False
        signs.add(cross > 0)
    return len(signs) == 1


def _edge_constraint(start: Point, end: Point, interior: Point) -> Constraint:
    """The ``a x + b y ≤ c`` form of the half-plane on the interior side of the edge."""
    a, b = end[1] - start[1], -(end[0] - start[0])
    c = a * start[0] + b * start[1]
    if a * interior[0] + b * interior[1] > c:
        a, b, c = -a, -b, -c
    if a == 0 and b == 0:
        raise ValueError("degenerate edge")
    return a, b, c


def _centroid(points: list[Point]) -> Point:
    count = len(points)
    return (
        sum(point[0] for point in points) / count,
        sum(point[1] for point in points) / count,
    )


def _line_intersection(first: Constraint, second: Constraint) -> Point | None:
    a1, b1, c1 = first
    a2, b2, c2 = second
    determinant = a1 * b2 - a2 * b1
    if determinant == 0:
        return None
    return (c1 * b2 - c2 * b1) / determinant, (a1 * c2 - a2 * c1) / determinant


def _primitive(direction: Point) -> tuple[int, int]:
    """Primitive integer direction, sign preserved: one canonical name per ray."""
    dx, dy = direction
    scale = dx.denominator * dy.denominator // gcd(dx.denominator, dy.denominator)
    x, y = int(dx * scale), int(dy * scale)
    divisor = gcd(abs(x), abs(y))
    if divisor == 0:
        return 0, 0
    return x // divisor, y // divisor


def _solve_region(constraints: list[Constraint]) -> tuple[list[Point], list[tuple[int, int]], str]:
    """Independent recomputation of the feasible region from the constraints alone."""
    vertices: set[Point] = set()
    for first, second in combinations(constraints, 2):
        point = _line_intersection(first, second)
        if point is None:
            continue
        if all(a * point[0] + b * point[1] <= c for a, b, c in constraints):
            vertices.add(point)
    rays: set[tuple[int, int]] = set()
    for a, b, _ in constraints:
        for direction in ((-b, a), (b, -a)):
            if direction == (0, 0):
                continue
            if all(da * direction[0] + db * direction[1] <= 0 for da, db, _ in constraints):
                rays.add(_primitive((Fraction(direction[0]), Fraction(direction[1]))))
    ordered = _angular_order(sorted(vertices)) if vertices else []
    if rays:
        return ordered, sorted(rays), "unbounded"
    return ordered, [], "polygon"


def _in_convex_hull(point: Point, vertices: list[Point]) -> bool:
    count = len(vertices)
    if count < 3:
        return point in vertices
    signs = set()
    for index in range(count):
        x1, y1 = vertices[index]
        x2, y2 = vertices[(index + 1) % count]
        cross = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)
        if cross != 0:
            signs.add(cross > 0)
    return len(signs) <= 1


def _in_cone(direction: Point, rays: list[tuple[int, int]]) -> bool:
    """``direction`` as a non-negative combination of the recession rays."""
    dx, dy = (Fraction(direction[0]), Fraction(direction[1]))
    if not rays:
        return dx == 0 and dy == 0
    if len(rays) == 1:
        rx, ry = rays[0]
        return dx * ry - dy * rx == 0 and dx * rx + dy * ry >= 0
    for first, second in combinations(rays, 2):
        rx, ry = first
        sx, sy = second
        determinant = rx * sy - ry * sx
        if determinant == 0:
            continue
        alpha = (dx * sy - dy * sx) / determinant
        beta = (rx * dy - ry * dx) / determinant
        if alpha >= 0 and beta >= 0:
            return True
    return False


def _region_member(point: Point, vertices: list[Point], rays: list[tuple[int, int]]) -> bool:
    if not rays:
        return _in_convex_hull(point, vertices)
    return any(_in_cone((point[0] - vertex[0], point[1] - vertex[1]), rays) for vertex in vertices)


# ------------------------------------------------------------------- formatting
def _num(value: Fraction) -> Integer | Rational:
    return Integer(value.numerator) if value.denominator == 1 else Rational(value.numerator, value.denominator)


def _fraction(text: str) -> Fraction | None:
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


def _point_latex(point: Point) -> str:
    return f"\\left({to_latex(_num(point[0]))}, {to_latex(_num(point[1]))}\\right)"


def _line_latex(constraint: Constraint) -> str:
    """The boundary line, printed the way the statement prints it."""
    a, b, c = constraint
    if a == 0:
        return f"{to_latex(Y)} = {to_latex(_num(c / b))}"
    if b == 0:
        return f"{to_latex(X)} = {to_latex(_num(c / a))}"
    if a < 0:
        a, b, c = -a, -b, -c
    sign = "+" if b > 0 else "-"
    return f"{to_latex(_num(a))}{to_latex(X)} {sign} {to_latex(_num(abs(b)))}{to_latex(Y)} = {to_latex(_num(c))}"


def _boundary_latex(constraints: list[Constraint]) -> str:
    return ", \\; ".join(_line_latex(constraint) for constraint in constraints)


def _region_latex(vertices: list[Point], rays: list[tuple[int, int]]) -> str:
    if not rays:
        return ", \\quad ".join(_point_latex(vertex) for vertex in vertices)
    base = _point_latex(vertices[0]) if vertices else "\\left(0, 0\\right)"
    terms = "".join(
        f" + \\lambda_{{{index + 1}}} {_point_latex((Fraction(ray[0]), Fraction(ray[1])))}"
        for index, ray in enumerate(rays)
    )
    lambdas = ", ".join(f"\\lambda_{{{index + 1}}}" for index in range(len(rays)))
    return f"{base}{terms}, \\; {lambdas} \\ge 0"


def _encode_point(point: Point) -> str:
    return f"{point[0]}|{point[1]}"


def _decode_point(text: str) -> Point | None:
    parts = text.split("|")
    if len(parts) != 2:
        return None
    values = [_fraction(part) for part in parts]
    if any(value is None for value in values):
        return None
    return values[0], values[1]


def _decode_constraint(text: str) -> Constraint | None:
    parts = text.split("|")
    if len(parts) != 3:
        return None
    values = [_fraction(part) for part in parts]
    if any(value is None for value in values):
        return None
    return values[0], values[1], values[2]


class InequalitySystem2x2:
    id = "math.systems.inequalities_2x2"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.systems_inequalities_2x2"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        if difficulty == "easy":
            key, params, vertices, rays, constraints = self._quadrant(rng)
        elif difficulty == "medium":
            key, params, vertices, rays, constraints = self._wedge(rng)
        else:
            key, params, vertices, rays, constraints = self._quadrilateral(rng)
        kind = "unbounded" if rays else "polygon"
        rays = sorted(rays)
        steps = (
            Step("step.boundary", _boundary_latex(constraints)),
            Step("step.vertices", ", \\; ".join(_point_latex(vertex) for vertex in vertices) or "\\emptyset"),
            Step("step.region", _region_latex(vertices, rays)),
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps,
            answer=Answer(
                latex=_region_latex(vertices, rays),
                kind="region",
                payload={
                    "kind": [kind],
                    "vertices": [_encode_point(vertex) for vertex in vertices],
                    "rays": [f"{dx}|{dy}" for dx, dy in rays],
                    "constraints": [f"{a}|{b}|{c}" for a, b, c in constraints],
                },
            ),
        )

    # ------------------------------------------------------------------ shapes
    def _quadrant(self, rng: random.Random):
        """Two axes-aligned half-planes: an unbounded quadrant, one vertex, two rays."""
        options = [(x, y) for x in range(-5, 6) for y in range(-5, 6) if (x, y) != (0, 0)]
        p, q = (Fraction(value) for value in rng.choice(options))
        vertices: list[Point] = [(p, q)]
        rays = [(1, 0), (0, 1)]
        constraints: list[Constraint] = [(-Fraction(1), Fraction(0), -p), (Fraction(0), -Fraction(1), -q)]
        params = {"shape": Fraction(1), "p": p, "q": q}
        return _QUADRANT, params, vertices, rays, constraints

    def _wedge(self, rng: random.Random):
        """Two non-parallel half-planes with positive normals: an unbounded wedge."""
        while True:
            a1, b1 = rng.randint(1, 4), rng.randint(1, 4)
            a2, b2 = rng.randint(1, 4), rng.randint(1, 4)
            if a1 * b2 != a2 * b1:
                break
        vertex = (Fraction(rng.randint(-4, 5)), Fraction(rng.randint(-4, 5)))
        c1 = a1 * vertex[0] + b1 * vertex[1]
        c2 = a2 * vertex[0] + b2 * vertex[1]
        constraints = [(Fraction(a1), Fraction(b1), c1), (Fraction(a2), Fraction(b2), c2)]
        rays = self._wedge_rays(a1, b1, a2, b2)
        params = {
            "shape": Fraction(2),
            "a1": Fraction(a1), "b1": Fraction(b1), "c1": c1,
            "a2": Fraction(a2), "b2": Fraction(b2), "c2": c2,
        }
        return _WEDGE, params, [vertex], rays, constraints

    @staticmethod
    def _wedge_rays(a1: int, b1: int, a2: int, b2: int) -> list[tuple[int, int]]:
        """Recession rays straight from the two normals of the construction."""
        rays = []
        for a, b, other in ((a1, b1, (a2, b2)), (a2, b2, (a1, b1))):
            direction = (b, -a)
            if other[0] * direction[0] + other[1] * direction[1] > 0:
                direction = (-b, a)
            rays.append(_primitive((Fraction(direction[0]), Fraction(direction[1]))))
        return sorted(rays)

    def _quadrilateral(self, rng: random.Random):
        """A convex quadrilateral drawn first; its four edges become the constraints."""
        for _ in range(200):
            candidate = self._draw_quad(rng)
            if candidate is None:
                continue
            key, params, vertices, constraints = candidate
            return key, params, vertices, [], constraints
        raise RuntimeError("quadrilateral system: no convex draw")

    def _draw_quad(self, rng: random.Random):
        offset_x = rng.randint(-3, 3)
        offset_y = rng.randint(-3, 3)
        magnitudes = [rng.randint(1, 6) for _ in range(8)]
        raw: list[Point] = [
            (Fraction(offset_x + magnitudes[0]), Fraction(offset_y + magnitudes[1])),
            (Fraction(offset_x - magnitudes[2]), Fraction(offset_y + magnitudes[3])),
            (Fraction(offset_x - magnitudes[4]), Fraction(offset_y - magnitudes[5])),
            (Fraction(offset_x + magnitudes[6]), Fraction(offset_y - magnitudes[7])),
        ]
        if len(set(raw)) != 4:
            return None
        ordered = _angular_order(raw)
        if not _is_convex(ordered):
            return None
        interior = _centroid(ordered)
        forms = [
            _edge_constraint(ordered[index], ordered[(index + 1) % 4], interior) for index in range(4)
        ]
        slots: dict[tuple[bool, bool], Constraint] = {}
        for a, b, c in forms:
            if a == 0 or b == 0:
                return None
            slots[(a > 0, b > 0)] = (a, b, c)
        if len(slots) != 4:
            return None
        params = {"shape": Fraction(3)}
        constraints: list[Constraint] = []
        for index, pattern in enumerate([(True, True), (False, True), (False, False), (True, False)], start=1):
            a, b, c = slots[pattern]
            params[f"a{index}"] = abs(a)
            params[f"b{index}"] = abs(b)
            params[f"c{index}"] = c
            constraints.append((a, b, c))
        return _QUAD, params, ordered, constraints

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        constraints = _constraints(item.statement_key, item.params)
        if constraints is None:
            return VerificationResult(False, "unknown_statement")

        claimed_constraints = [
            _decode_constraint(text) for text in item.answer.payload.get("constraints", [])
        ]
        if any(value is None for value in claimed_constraints):
            return VerificationResult(False, "unparsable_constraints")
        if sorted(claimed_constraints) != sorted(constraints):
            return VerificationResult(False, "constraint_mismatch")

        claimed_vertices = [_decode_point(text) for text in item.answer.payload.get("vertices", [])]
        if any(vertex is None for vertex in claimed_vertices):
            return VerificationResult(False, "unparsable_vertices")
        claimed_rays = [_decode_point(text) for text in item.answer.payload.get("rays", [])]
        if any(ray is None for ray in claimed_rays):
            return VerificationResult(False, "unparsable_rays")
        claimed_ray_names = sorted(_primitive(ray) for ray in claimed_rays)
        if any(name == (0, 0) for name in claimed_ray_names):
            return VerificationResult(False, "zero_ray")

        vertices, rays, kind = _solve_region(constraints)
        if sorted(claimed_vertices) != sorted(vertices):
            return VerificationResult(False, "vertex_set_mismatch")
        if claimed_ray_names != list(rays):
            return VerificationResult(False, "ray_set_mismatch")
        if list(item.answer.payload.get("kind", [])) != [kind]:
            return VerificationResult(False, "region_kind_mismatch")
        if claimed_vertices and claimed_vertices != _angular_order(claimed_vertices):
            return VerificationResult(False, "vertex_order_mismatch")  # the prototype's bug
        if len(claimed_vertices) >= 3 and not _is_convex(claimed_vertices):
            return VerificationResult(False, "non_convex_region")
        if item.answer.latex != _region_latex(claimed_vertices, claimed_ray_names):
            return VerificationResult(False, "answer_latex_mismatch")

        for point in _probes(vertices, constraints):
            from_constraints = all(a * point[0] + b * point[1] <= c for a, b, c in constraints)
            from_region = _region_member(point, claimed_vertices, claimed_ray_names)
            if from_constraints != from_region:
                return VerificationResult(False, "sampling_disagrees")
        return VerificationResult(True)


def _probes(vertices: list[Point], constraints: list[Constraint]) -> list[Point]:
    """Deterministic sample: grid around the region, the vertices, and each violation side."""
    points: set[Point] = set(vertices)
    if vertices:
        xs = [vertex[0] for vertex in vertices]
        ys = [vertex[1] for vertex in vertices]
        low_x, high_x = min(xs) - 3, max(xs) + 3
        low_y, high_y = min(ys) - 3, max(ys) + 3
        span_x, span_y = int(high_x - low_x), int(high_y - low_y)
        if span_x <= 24 and span_y <= 24:
            for step_x in range(span_x + 1):
                for step_y in range(span_y + 1):
                    points.add((low_x + step_x, low_y + step_y))
        for vertex in vertices:
            for shift in (-1, 1):
                points.add((vertex[0] + shift, vertex[1]))
                points.add((vertex[0], vertex[1] + shift))
    anchor = _centroid(vertices) if vertices else (Fraction(0), Fraction(0))
    for a, b, c in constraints:
        offset = a * anchor[0] + b * anchor[1] - c
        norm = a * a + b * b
        if norm == 0:
            continue
        base = (anchor[0] - offset * a / norm, anchor[1] - offset * b / norm)  # on the boundary line
        for step in (1, 2):
            points.add((base[0] + step * a, base[1] + step * b))  # violates this constraint
            points.add((base[0] - step * a, base[1] - step * b))  # satisfies it strictly
    return sorted(points)


def _constraints(statement_key: str, params: dict[str, Fraction]) -> list[Constraint] | None:
    """Rebuild the canonical ``a x + b y ≤ c`` forms that the statement displays."""
    shape = params.get("shape")
    if shape is None or shape.denominator != 1 or _SHAPE_KEYS.get(int(shape)) != statement_key:
        return None
    if statement_key == _QUADRANT:
        p, q = params.get("p"), params.get("q")
        if p is None or q is None:
            return None
        return [(-Fraction(1), Fraction(0), -p), (Fraction(0), -Fraction(1), -q)]
    if statement_key == _WEDGE:
        names = ("a1", "b1", "c1", "a2", "b2", "c2")
        if any(name not in params for name in names):
            return None
        a1, b1, c1, a2, b2, c2 = (params[name] for name in names)
        if min(a1, b1, a2, b2) <= 0:
            return None
        return [(a1, b1, c1), (a2, b2, c2)]
    if statement_key == _QUAD:
        names = [f"{letter}{index}" for index in range(1, 5) for letter in ("a", "b", "c")]
        if any(name not in params for name in names):
            return None
        signs = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        constraints: list[Constraint] = []
        for index, (sign_a, sign_b) in enumerate(signs, start=1):
            a, b, c = params[f"a{index}"], params[f"b{index}"], params[f"c{index}"]
            if a <= 0 or b <= 0:
                return None
            constraints.append((sign_a * a, sign_b * b, c))
        return constraints
    return None


TOPIC = InequalitySystem2x2()
