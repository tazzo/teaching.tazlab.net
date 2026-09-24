"""Rendering must not drift silently (C.9)."""

from __future__ import annotations

from tests.golden.latex import collect, load, save, updating


def test_latex_output_matches_the_golden_file() -> None:
    current = collect()
    golden = load()

    if updating() or not golden:
        save(current)
        # A freshly written golden file is a bootstrap, not a pass: say so loudly.
        assert golden == {} or updating(), (
            "golden file was missing and has been generated — review and commit it"
        )
        return

    missing = sorted(set(current) - set(golden))
    assert not missing, (
        f"new topic/difficulty without golden output: {missing}. "
        "Run TEACHING_UPDATE_GOLDEN=1 pytest tests/test_latex_golden.py and review the diff."
    )

    changed = {key: (golden[key], current[key]) for key in sorted(current) if golden.get(key) != current[key]}
    assert not changed, f"LaTeX output changed for {sorted(changed)} — a SymPy bump or a real change?"
