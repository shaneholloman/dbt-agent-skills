# Generating Unit Tests for Cross-Platform Migration

## PROBLEM

Before migrating to a target platform, we need to capture the expected data outputs from the source platform. dbt unit tests serve as a "golden dataset" that proves data consistency after migration — if the same inputs produce the same outputs on both platforms, the migration preserves business logic.

## SOLUTION

### Which models to test

The primary criterion is **DAG position**, not naming convention. Focus on:

1. **Leaf nodes** — Models at the very end of the DAG that nothing else depends on. These are the final outputs consumed by BI tools, reverse ETL, exports, and downstream systems. Every leaf node is worth testing regardless of what it's named. Use `dbt ls --resource-type model --output json` to identify models with no children, or inspect the DAG via `dbt docs generate`.
2. **Models with significant transformation logic** — Even if mid-DAG, any model with complex joins, calculations, or case statements should be tested. The more business logic a model contains, the more important it is to verify.

**Skip**:
- **Staging models** — Simple 1:1 source mappings; if sources are correct, staging will be correct
- **Pass-through models** — Models that just rename columns or filter rows without business logic

**If leaf nodes have common naming conventions** (e.g., `fct_*`, `dim_*`, `agg_*`), that's a helpful heuristic — but don't rely on it exclusively. A model named `customer_summary` at the end of the DAG is just as important to test as one named `dim_customers`.

### How to select test rows

Use `dbt show` to preview model outputs on the source platform:

```bash
dbt show --select fct_orders --limit 10
```

**Select rows that exercise key logic**:
- Rows that hit different branches of `CASE WHEN` statements
- Rows with NULL values in columns that have COALESCE/NVL logic
- Rows with edge case values (zero quantities, negative amounts, boundary dates)
- At minimum, 2-3 rows per model

### Writing unit tests

Place unit tests in the model's YAML file or a dedicated `_unit_tests.yml` file in the same directory. Use the `dict` format for readability:

```yaml
unit_tests:
  - name: test_fct_orders_basic
    description: "Verify core order calculations"
    model: fct_orders
    given:
      - input: ref('stg_orders')
        rows:
          - {order_key: 1, customer_key: 100, order_date: '1998-01-01', status_code: 'F', total_price: 150.00}
          - {order_key: 2, customer_key: 200, order_date: '1998-06-15', status_code: 'O', total_price: 0.00}
      - input: ref('stg_line_items')
        rows:
          - {order_key: 1, line_number: 1, extended_price: 100.00, discount: 0.05, tax: 0.08}
          - {order_key: 1, line_number: 2, extended_price: 50.00, discount: 0.00, tax: 0.08}
          - {order_key: 2, line_number: 1, extended_price: 0.00, discount: 0.00, tax: 0.00}
    expect:
      rows:
        - {order_key: 1, customer_key: 100, order_status: 'fulfilled', gross_amount: 150.00}
        - {order_key: 2, customer_key: 200, order_status: 'open', gross_amount: 0.00}
```

For detailed unit test authoring guidance, refer to the `adding-dbt-unit-test` skill.

### Verify tests pass on source platform

Before starting migration, confirm all unit tests pass on the source:

```bash
dbt test --select test_type:unit
```

All tests must pass. If any fail, fix them before proceeding — failed tests on the source platform indicate a test authoring issue, not a migration issue.

## CHALLENGES

### Large or complex models

For models with many input sources or complex joins:
- Start with a minimal test covering the primary join path
- Add additional tests for specific business logic branches
- You don't need to test every column — focus on calculated/derived columns

### Handling platform-specific functions in test data

If the source model uses platform-specific functions that produce specific data types:
- Use literal values in test expectations rather than function calls
- Focus on the business-meaningful output values, not intermediate representations

### Models with many columns

You don't need to include every column in the `expect` block. Include only the columns that have business logic applied — columns that are simple pass-throughs from inputs don't need explicit verification.

### Incremental models

For incremental models, unit tests should test the transformation logic, not the incremental behavior. Provide input rows and verify the output — the incremental strategy is a materialization concern, not a logic concern.

### Using dbt show for quick validation

Before writing formal unit tests, use `dbt show` to understand what a model outputs:

```bash
# Preview output
dbt show --select model_name --limit 5

# Preview with inline filter for specific scenarios
dbt show --inline "select * from {{ ref('model_name') }} where status = 'returned'" --limit 5
```

This helps you pick representative test rows and understand the expected output format.
