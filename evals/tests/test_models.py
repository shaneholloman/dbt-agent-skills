"""Tests for skill_eval data models."""

from pathlib import Path

from skill_eval.models import load_scenario


def test_load_scenario_parses_skill_sets(tmp_path: Path) -> None:
    """Scenario loads skill-sets.yaml correctly."""
    scenario_dir = tmp_path / "test-scenario"
    scenario_dir.mkdir()
    (scenario_dir / "scenario.md").write_text("# Test")
    (scenario_dir / "prompt.txt").write_text("Fix the bug")
    (scenario_dir / "skill-sets.yaml").write_text(
        """
sets:
  - name: no-skills
    skills: []
  - name: with-debug
    skills:
      - debugging-dbt-errors/baseline.md
"""
    )

    scenario = load_scenario(scenario_dir)

    assert scenario.name == "test-scenario"
    assert scenario.prompt == "Fix the bug"
    assert len(scenario.skill_sets) == 2
    assert scenario.skill_sets[0].name == "no-skills"
    assert scenario.skill_sets[0].skills == []
    assert scenario.skill_sets[1].name == "with-debug"
    assert scenario.skill_sets[1].skills == ["debugging-dbt-errors/baseline.md"]
