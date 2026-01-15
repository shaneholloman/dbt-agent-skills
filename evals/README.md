# Skill Evaluation Tool

A/B testing tool for comparing LLM skill variations.

## Setup

```bash
cd evals
uv sync
```

## Usage

```bash
# Run a scenario
uv run skill-eval run <scenario-name>

# Run all scenarios
uv run skill-eval run --all

# Grade outputs from a run
uv run skill-eval grade <run-id>

# Generate comparison report
uv run skill-eval report <run-id>
```

## Directory Structure

```
evals/
├── scenarios/          # Test scenarios
│   └── example-yaml-error/
│       ├── scenario.md       # Description and grading criteria
│       ├── prompt.txt        # User message to send
│       ├── skill-sets.yaml   # Which skill combinations to test
│       └── context/          # Files Claude needs to see
├── variants/           # Skill variants to compare
│   └── debugging-dbt-errors/
│       └── baseline.md
├── runs/               # Output from runs (gitignored)
├── reports/            # Generated comparison reports
├── src/skill_eval/     # CLI source code
└── tests/              # Unit tests
```

## Workflow

1. **Create a scenario** - Record a real issue with context files and expected behavior
2. **Define skill sets** - Specify which skill variants to compare
3. **Run evaluation** - `skill-eval run <scenario>` executes Claude with each skill set
4. **Grade outputs** - `skill-eval grade <run-id>` creates grades.yaml for human review
5. **Generate report** - `skill-eval report <run-id>` shows comparison summary
