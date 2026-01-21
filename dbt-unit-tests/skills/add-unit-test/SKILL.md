---
name: adding-dbt-unit-test
description: Use when adding unit tests for a dbt model
---

# Add unit test for a dbt model

## What are unit tests in dbt

In software programming, unit tests validate small portions of your functional code, and they work much the same way in dbt. dbt uwnit tests allow you to validate your SQL modeling logic on a small set of static inputs _before_ you materialize your full model in production. dbt unit tests enable test-driven development, benefiting developer efficiency and code reliability.

Unit tests allow enforcing that all the unit tests for a model pass before it is materialized (i.e. dbt won't materialize the model in the database if *any* of its unit tests do not pass).

## When to use

You should unit test a model:
- Adding Model-Input-Output scenarios for the intended functionality of the model as well as edge cases to prevent regressions if the model logic is changed at a later date.
- Verifying that a bug fix solves a bug report for an existing dbt model.

More examples:
- When your SQL contains complex logic:
    - Regex
    - Date math
    - Window functions
    - `case when` statements when there are many `when`s
    - Truncation
- When you're writing custom logic to process input data, similar to creating a function.
- Logic for which you had bugs reported before.
- Edge cases not yet seen in your actual data that you want to be confident you are handling properly.
- Prior to refactoring the transformation logic (especially if the refactor is significant).
- Models with high "criticality" (public, contracted models or models directly upstream of an exposure).

## When not to use

Cases we don't recommend creating unit tests for:
- Built-in functions that are tested extensively by the warehouse provider. If an unexpected issue arises, it's more likely a result of issues in the underlying data rather than the function itself. Therefore, fixture data in the unit test won't provide valuable information.
    - common SQL spec functions like `min()`, etc.

## General format

dbt unit test uses a trio of the model, given inputs, and expected outputs (Model-Inputs-Outputs):

1. `model` - when building this model
2. `given` inputs - given a set of source, seeds, and models as preconditions
3. `expect` output - then expect this row content of the model as a postcondition

### Workflow

### 1. Choose the model to test

Self explanatory -- the title says it all!

### 2. Mock the inputs

- Create an input for each of the nodes the model depends on.
- Specify the mock data it should use.
- Specify the `format` if different than the default (YAML `dict`).
  - See the "Data `format`s for unit tests" section below to determine which `format` to use.
- The mock data only needs include the subset of columns used within this test case.

### 3. Mock the output

- Specify the data that you expect the model to create given those inputs.
- Specify the `format` if different than the default (YAML `dict`).
  - See the "Data `format`s for unit tests" section below to determine which `format` to use.
- The mock data only needs include the subset of columns used within this test case.

## Minimal unit test

Suppose you have this model:

```sql
-- models/hello_world.sql

select 'world' as hello
```

Minimal unit test for that model:

```yaml
# models/_properties.yml

unit_tests:
  - name: test_hello_world

    # Always only one transformation to test
    model: hello_world

    # No inputs needed this time!
    # Most unit tests will have inputs -- see the "real world example" section below
    given: []

    # Expected output can have zero to many rows
    expect:
      rows:
        - {hello: world}
```

## Executing unit tests

Run the unit tests, build the model, and run the data tests for the `hello_world` model:

```shell
dbt build --select hello_world
```

This saves on warehouse spend as the model will only be materialized and move on to the data tests if the unit tests pass successfully.

Or only run the unit tests without building the model or running the data tests:

```shell
dbt test --select "hello_world,test_type:unit"
```

Or choose a specific unit test by name:

```shell
dbt test --select test_is_valid_email_address
```

### Excluding unit tests from production builds

dbt Labs strongly recommends only running unit tests in development or CI environments. Since the inputs of the unit tests are static, there's no need to use additional compute cycles running them in production. Use them when doing development for a test-driven approach and CI to ensure changes don't break them.

Use the `--resource-type` flag `--exclude-resource-type` or the `DBT_EXCLUDE_RESOURCE_TYPES` environment variable to exclude unit tests from your production builds and save compute. 

## More realistic example

```yaml
unit_tests:

  - name: test_order_items_count_drink_items_with_zero_drinks
    description: >
      Scenario: Order without any drinks
        When the `order_items_summary` table is built
        Given an order with nothing but 1 food item
        Then the count of drink items is 0

    # Model
    model: order_items_summary

    # Inputs
    given:
      - input: ref('order_items')
        rows:
          - {
              order_id: 76,
              order_item_id: 3,
              is_drink_item: false,
            }
      - input: ref('stg_orders')
        rows:
          - { order_id: 76 }

    # Output
    expect:
      rows:
        - {
            order_id: 76,
            count_drink_items: 0,
          }
```

For more examples of unit tests, see [examples.md](examples.md)

## Supported and unsupported scenarios

- dbt only supports unit testing SQL models.
    - Unit testing Python models is not supported.
    - Unit testing non-model nodes like snapshots, seeds, sources, analyses, etc. is not supported.
- dbt only supports adding unit tests to models in your _current_ project.
    - Unit testing cross-project models or models imported from a package is not supported.
- dbt _does not_ support unit testing models that use the `materialized view` materialization.
- dbt _does not_ support unit testing models that use recursive SQL.
- dbt _does not_ support unit testing models that use introspective queries.
- dbt _does not_ support an `expect` output for final state of the database table after inserting/merging for incremental models.
- dbt _does_ support an `expect` output for what will be merged/inserted for incremental models.

## Handy to know

- Unit tests must be defined in a YAML file in your `model-paths` directory (`models/` by default)
- Fixture files for unit tests must be defined in a SQL or CSV file in your `test-paths` directory (`tests/fixtures` by default)
- Include all `ref` or `source` model references in the unit test configuration as `input`s to avoid "node not found" errors during compilation.
- If your model has multiple versions, by default the unit test will run on *all* versions of your model.
- If you want to unit test a model that depends on an ephemeral model, you must use `format: sql` for the ephemeral model input.
- Table names within the model must be aliased in order to unit test `join` logic

## YAML for specifying unit tets

- For all the required and optional keys in the YAML definition of unit tests, see [spec.md](spec.md)

# Inputs for unit tests

Use `input`s in your unit tests to reference a specific model or source for the test:

-  For `input:`, use a string that represents a `ref` or `source` call:
    - `ref('my_model')` or `ref('my_model', v='2')` or `ref('dougs_project', 'users')`
    - `source('source_schema', 'source_name')`
- For seed inputs:
    - If you do not supply an input for a seed, we will use the seed's CSV file _as_ the input.
    - If you do supply an input for a seed, we will use that input instead.
- Use “empty” inputs by setting rows to an empty list `rows: []`
    - This is useful if the model has a `ref` or `source` dependency, but its values are irrelevant to this particular unit test. Just beware if the model has a join on that input that would cause rows to drop out!

<File name='models/schema.yml'>

```yaml
unit_tests:
  - name: test_is_valid_email_address  # this is the unique name of the test
    model: dim_customers  # name of the model I'm unit testing
    given:  # the mock data for your inputs
      - input: ref('stg_customers')
        rows:
         - {email: cool@example.com,     email_top_level_domain: example.com}
         - {email: cool@unknown.com,     email_top_level_domain: unknown.com}
         - {email: badgmail.com,         email_top_level_domain: gmail.com}
         - {email: missingdot@gmailcom,  email_top_level_domain: gmail.com}
      - input: ref('top_level_email_domains')
        rows:
         - {tld: example.com}
         - {tld: gmail.com}
      - input: ref('irrelevant_dependency')  # dependency that we need to acknowlege, but does not need any data
        rows: []
...

```
</File>

# Data `format`s for unit tests

dbt supports three formats for mock data within unit tests:

1. `dict` (default): Inline YAML dictionary values.
2. `csv`: Inline CSV values or a CSV file.
3. `sql`: Inline SQL query or a SQL file.

Notes:
- For the `sql` format you must supply mock data for _all columns_ whereas `dict` and `csv` may supply only a subset.
- Only the `sql` format allows you to unit test a model that depends on an ephemeral model -- `dict` and `csv` can't be used in that case.
- There are no formats that support Jinja.

## `dict`

The `dict` data format is the default if no `format` is defined.

`dict` requires an inline YAML dictionary for `rows`:

<File name='models/schema.yml'>

```yaml
unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_model_a')
        format: dict
        rows:
          - {id: 1, name: gerda}
          - {id: 2, b: michelle}    
```

</File>

## `csv`

### Inline `csv` example

When using the `csv` format, you can use either an inline CSV string for `rows`:

<File name='models/schema.yml'>

```yaml

unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_model_a')
        format: csv
        rows: |
          id,name
          1,gerda
          2,michelle

```
</File>

### Fixture `csv` example

Or, you can provide the name of a CSV file in the `test-paths` location (`tests/fixtures` by default): 

<File name='models/schema.yml'>

```yaml

unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_model_a')
        format: csv
        fixture: my_model_a_fixture

```
</File>

<File name='tests/fixtures/my_model_a_fixture.csv'>

```csv

id,name
1,gerda
2,michelle

```
</File>

## `sql`

Using this format:
- Provides more flexibility for the unit testing column that have a data type not supported by the `dict` or `csv` formats
- Allows you to unit test a model that depends on an `ephemeral` model

However, when using `format: sql` you must supply mock data for _all columns_.

When using the `sql` format, you can use either an inline SQL query for `rows`:

### Inline `sql` example

<File name='models/schema.yml'>

```yaml

unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_model_a')
        format: sql
        rows: |
          select 1 as id, 'gerda' as name, null as loaded_at union all
          select 2 as id, 'michelle', null as loaded_at as name

```

</File>

### Fixture `sql` example

Or, you can provide the name of a SQL file in the `test-paths` location (`tests/fixtures` by default): 

<File name='models/schema.yml'>

```yaml

unit_tests:
  - name: test_my_model
    model: my_model
    given:
      - input: ref('my_model_a')
        format: sql
        fixture: my_model_a_fixture

```
</File>

<File name='tests/fixtures/my_model_a_fixture.sql'>

```sql

select 1 as id, 'gerda' as name, null as loaded_at union all
select 2 as id, 'michelle', null as loaded_at as name

```
</File>

**Note:** Contrary to dbt SQL models, Jinja is unsupported within SQL fixtures for unit tests.

# Special cases

## Unit testing incremental models

When configuring your unit test, you can override the output of macros, vars, or environment variables. This enables you to unit test your incremental models in "full refresh" and "incremental" modes.

### Note
Incremental models need to exist in the database first before running unit tests. Use the `--empty` flag to build an empty version of the models to save warehouse spend. You can also optionally select only your incremental models using the `--select` flag.

  ```shell
  dbt run --select "config.materialized:incremental" --empty
  ```

  After running the command, you can then perform a regular `dbt build` for that model and then run your unit test.

When testing an incremental model, the expected output is the __result of the materialization__ (what will be merged/inserted), not the resulting model itself (what the final table will look like after the merge/insert).

For example, say you have an incremental model in your project:

<File name='my_incremental_model.sql'>

```sql

{{
    config(
        materialized='incremental'
    )
}}

select * from {{ ref('events') }}
{% if is_incremental() %}
where event_time > (select max(event_time) from {{ this }})
{% endif %}

```

</File>

You can define unit tests on `my_incremental_model` to ensure your incremental logic is working as expected:

```yml

unit_tests:
  - name: my_incremental_model_full_refresh_mode
    model: my_incremental_model
    overrides:
      macros:
        # unit test this model in "full refresh" mode
        is_incremental: false 
    given:
      - input: ref('events')
        rows:
          - {event_id: 1, event_time: 2020-01-01}
    expect:
      rows:
        - {event_id: 1, event_time: 2020-01-01}

  - name: my_incremental_model_incremental_mode
    model: my_incremental_model
    overrides:
      macros:
        # unit test this model in "incremental" mode
        is_incremental: true 
    given:
      - input: ref('events')
        rows:
          - {event_id: 1, event_time: 2020-01-01}
          - {event_id: 2, event_time: 2020-01-02}
          - {event_id: 3, event_time: 2020-01-03}
      - input: this 
        # contents of current my_incremental_model
        rows:
          - {event_id: 1, event_time: 2020-01-01}
    expect:
      # what will be inserted/merged into my_incremental_model
      rows:
        - {event_id: 2, event_time: 2020-01-02}
        - {event_id: 3, event_time: 2020-01-03}

```

There is currently no way to unit test whether the dbt framework inserted/merged the records into your existing model correctly, but we're investigating support for this in the future in GitHub issue #8664.

## Unit testing a model that depends on ephemeral model(s)

If you want to unit test a model that depends on an ephemeral model, you must use `format: sql` for that input.

```yml
unit_tests:
  - name: my_unit_test
    model: dim_customers
    given:
      - input: ref('ephemeral_model')
        format: sql
        rows: |
          select 1 as id, 'emily' as name
    expect:
      rows:
        - {id: 1, first_name: emily}
```

# Unit testing versioned SQL models

If your model has multiple versions, the default unit test will run on _all_ versions of your model. To specify version(s) of your model to unit test, use `include` or `exclude` for the desired versions in your model versions config:

<File name='models/schema.yml'>

```yaml

# my test_is_valid_email_address unit test will run on all versions of my_model
unit_tests:
  - name: test_is_valid_email_address
    model: my_model
    ...
            
# my test_is_valid_email_address unit test will run on ONLY version 2 of my_model
unit_tests:
  - name: test_is_valid_email_address 
    model: my_model 
    versions:
      include: 
        - 2
    ...
            
# my test_is_valid_email_address unit test will run on all versions EXCEPT 1 of my_model
unit_tests:
  - name: test_is_valid_email_address
    model: my_model 
    versions:
      exclude: 
        - 1
    ...

```
</File>

# Unit test overrides

When configuring your unit test, you can override the output of macros, project variables, or environment variables for a given unit test.

<File name='models/schema.yml'>

```yml

 - name: test_my_model_overrides
    model: my_model
    given:
      - input: ref('my_model_a')
        rows:
          - {id: 1, a: 1}
      - input: ref('my_model_b')
        rows:
          - {id: 1, b: 2}
          - {id: 2, b: 2}
    overrides:
      macros:
        type_numeric: override
        invocation_id: 123
      vars:
        my_test: var_override
      env_vars:
        MY_TEST: env_var_override
    expect:
      rows:
        - {macro_call: override, var_call: var_override, env_var_call: env_var_override, invocation_id: 123}

```

</File>

## Macros

You can override the output of any macro in your unit test defition. 

If the model you're unit testing uses these macros, you must override them:
  - `is_incremental`: If you're unit testing an incremental model, you must explicity set `is_incremental` to `true` or `false`.

<File name='models/schema.yml'>

  ```yml

  unit_tests:
    - name: my_unit_test
      model: my_incremental_model
      overrides:
        macros:
          # unit test this model in "full refresh" mode
          is_incremental: false 
      ...

  ```
</File>

  - `dbt_utils.star`: If you're unit testing a model that uses the `star` macro, you must explicity set `star` to a list of columns. This is because the `star` only accepts a relation for the `from` argument; the unit test mock input data is injected directly into the model SQL, replacing the `ref()` or `source()` function, causing the `star` macro to fail unless overidden.

<File name='models/schema.yml'>

  ```yml

  unit_tests:
    - name: my_other_unit_test
      model: my_model_that_uses_star
      overrides:
        macros:
          # explicity set star to relevant list of columns
          dbt_utils.star: col_a,col_b,col_c 
      ...

  ``` 
</File>

#### Platform/adapter-specific caveats

- You must specify all fields in a BigQuery `STRUCT` in a unit test. You cannot use only a subset of fields in a `STRUCT`.
- Redshift sources need to be in the same database as the models.

## Unit test limitations for Redshift

- Redshift doesn't support unit tests when the SQL in the common table expression (CTE) contains functions such as `LISTAGG`, `MEDIAN`, `PERCENTILE_CONT`, and so on. These functions must be executed against a user-created table. dbt combines given rows to be part of the CTE, which Redshift does not support.

  In order to support this pattern in the future, dbt would need to "materialize" the input fixtures as tables, rather than interpolating them as CTEs. If you are interested in this functionality, we'd encourage you to participate in this issue in GitHub issue #8499.

- Redshift doesn't support unit tests that rely on sources in a database that differs from the models.

# Platform/adapter-specific data types

Unit tests are designed to test for the expected _values_, not for the data types themselves. dbt takes the value you provide and attempts to cast it to the data type as inferred from the input and output models. 

How you specify input and expected values in your unit test YAML definitions are largely consistent across data warehouses, with some variation for more complex data types. The following are platform-specific data types:

### Snowflake

```yaml
unit_tests:
  - name: test_my_data_types
    model: fct_data_types
    given:
      - input: ref('stg_data_types')
        rows:
         - int_field: 1
           float_field: 2.0
           str_field: my_string
           str_escaped_field: "my,cool'string"
           date_field: 2020-01-02
           timestamp_field: 2013-11-03 00:00:00-0
           timestamptz_field: 2013-11-03 00:00:00-0
           number_field: 3
           variant_field: 3
           geometry_field: POINT(1820.12 890.56)
           geography_field: POINT(-122.35 37.55)
           object_field: {'Alberta':'Edmonton','Manitoba':'Winnipeg'}
           str_array_field: ['a','b','c']
           int_array_field: [1, 2, 3]
           binary_field: 19E1FFDCCB6CDEE788BF631C1C4905D1
```

### BigQuery

```yaml
unit_tests:
  - name: test_my_data_types
    model: fct_data_types
    given:
      - input: ref('stg_data_types')
        rows:
         - int_field: 1
           float_field: 2.0
           str_field: my_string
           str_escaped_field: "my,cool'string"
           date_field: 2020-01-02
           timestamp_field: 2013-11-03 00:00:00-0
           timestamptz_field: 2013-11-03 00:00:00-0
           bigint_field: 1
           geography_field: 'st_geogpoint(75, 45)'
           json_field: {"name": "Cooper", "forname": "Alice"}
           str_array_field: ['a','b','c']
           int_array_field: [1, 2, 3]
           date_array_field: ['2020-01-01']
           struct_field: 'struct("Isha" as name, 22 as age)'
           struct_of_struct_field: 'struct(struct(1 as id, "blue" as color) as my_struct)'
           struct_array_field: ['struct(st_geogpoint(75, 45) as my_point)', 'struct(st_geogpoint(75, 35) as my_point)']
           # Make sure to include **all** the fields in a BigQuery `struct` within the unit test.
           # It's not currently possible to use only a subset of columns in a 'struct'
```

### Redshift

```yaml

unit_tests:
  - name: test_my_data_types
    model: fct_data_types
    given:
      - input: ref('stg_data_types')
        rows:
         - int_field: 1
           float_field: 2.0
           str_field: my_string
           str_escaped_field: "my,cool'string"
           date_field: 2020-01-02
           timestamp_field: 2013-11-03 00:00:00-0
           timestamptz_field: 2013-11-03 00:00:00-0
           json_field: '{"bar": "baz", "balance": 7.77, "active": false}'
```

Currently, the `array` data type is not supported for YAML format `dict` inputs. Use the `sql` format instead if you need to mock `array` inputs or outputs.

### Spark

```yaml

unit_tests:
  - name: test_my_data_types
    model: fct_data_types
    given:
      - input: ref('stg_data_types')
        rows:
         - int_field: 1
           float_field: 2.0
           str_field: my_string
           str_escaped_field: "my,cool'string"
           bool_field: true
           date_field: 2020-01-02
           timestamp_field: 2013-11-03 00:00:00-0
           timestamptz_field: 2013-11-03 00:00:00-0
           int_array_field: 'array(1, 2, 3)'
           map_field: 'map("10", "t", "15", "f", "20", NULL)'
           named_struct_field: 'named_struct("a", 1, "b", 2, "c", 3)'
```

### Postgres

```yaml

unit_tests:
  - name: test_my_data_types
    model: fct_data_types
    given:
      - input: ref('stg_data_types')
        rows:
         - int_field: 1
           float_field: 2.0
           numeric_field: 1
           str_field: my_string
           str_escaped_field: "my,cool'string"
           bool_field: true
           date_field: 2020-01-02
           timestamp_field: 2013-11-03 00:00:00-0
           timestamptz_field: 2013-11-03 00:00:00-0
           json_field: '{"bar": "baz", "balance": 7.77, "active": false}'
```

Currently, the `array` data type is not supported for YAML format `dict` inputs. Use the `sql` format instead if you need to mock `array` inputs or outputs.

# Disabling a unit test

By default, all specified unit tests are enabled and will be included according to the `--select` flag.

To disable a unit test from being executed, set:
```yaml
    config: 
      enabled: false
```

This is helpful if a unit test is incorrectly failing and it needs to be disabled until it is fixed.

### When a unit test fails 

When a unit test fails, there will be a log message of "actual differs from expected", and it will show a "data diff" between the two:

```
actual differs from expected:

@@ ,email           ,is_valid_email_address
→  ,cool@example.com,True→False
   ,cool@unknown.com,False
```

There are two main possibilities when a unit test fails:

1. There was an error in the way the unit test was constructed (false positive)
2. There is an bug is the model (true positive)

It takes expert judgement to determine one from the other.

### The `--empty` flag

The direct parents of the model that you’re unit testing need to exist in the warehouse before you can execute the unit test. The `run` and `build` commands supports the `--empty` flag for building schema-only dry runs. The `--empty` flag limits the `ref`s and `sources` to zero rows. dbt will still execute the model SQL against the target data warehouse but will avoid expensive reads of input data. This validates dependencies and ensures your models will build properly.

Use the `--empty` flag to build an empty version of the models to save warehouse spend. 

```bash

dbt run --select "stg_customers top_level_email_domains" --empty

```

### Fixture files

The `dict` format only supports inline YAML mock data, but you can also use `csv` or `sql` either inline or in a separate fixture file. Store your fixture files in a `fixtures` subdirectory in any of your `test-paths`. For example, `tests/fixtures/my_unit_test_fixture.sql`. 

When using the `dict` or `csv` format, you only have to define the mock data for the columns relevant to you. This enables you to write succinct and _specific_ unit tests. For the `sql` format _all_ columns need to be defined.

### Similar testing concepts

There are similar concepts that dbt's `model`, `given`, `expect` lines up with (Hoare triple, Arrange-Act-Assert, Gherkin, What's in a Story?, etc):

| dbt unit test | Description                                | Hoare triple | Arrange-Act-Assert | Gherkin | What's in a Story? |
|---------------|--------------------------------------------|------------------------------------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **`model`**   | when running the command for this model    | Command                                                                | Act                                                                             | When                                                   | Event                                                                                                                                |
| **`given`**   | given these test inputs as  preconditions  | Precondition                                                           | Arrange                                                                         | Given                                                  | Givens                                                                                                                               |
| **`expect`**  | then expect this output as a postcondition | Postcondition                                                          | Assert                                                                          | Then                                                   | Outcome                                                                                                                              |
