from struct import pack
import os
import pytest
from dbt.tests.util import run_dbt

# our file contents
from tests.functional.fixtures import (
    fact_orders_source_csv,
    fact_orders_sql,
    fact_orders_yml,
)

# models/multi_dimension_base_sum_metric.sql
multi_dimension_base_sum_metric_sql = """
select *
from 
{{ metrics.calculate(metric('multi_dimension_base_sum_metric'), 
    grain='month',
    dimensions=['had_discount','order_country']
    )
}}
"""

# models/multi_dimension_base_sum_metric.yml
multi_dimension_base_sum_metric_yml = """
version: 2 
models:
  - name: multi_dimension_base_sum_metric
    tests: 
      - dbt_utils.equality:
          compare_model: ref('multi_dimension_base_sum_metric__expected')
metrics:
  - name: multi_dimension_base_sum_metric
    model: ref('fact_orders')
    label: Total Discount ($)
    timestamp: order_date
    time_grains: [day, week, month]
    calculation_method: sum
    expression: order_total
    dimensions:
      - had_discount
      - order_country
"""

# seeds/multi_dimension_base_sum_metric__expected.csv
multi_dimension_base_sum_metric__expected_csv = """
date_month,had_discount,order_country,multi_dimension_base_sum_metric
2022-01-01,TRUE,France,1
2022-01-01,TRUE,Japan,1
2022-01-01,FALSE,France,4
2022-01-01,FALSE,Japan,2
2022-02-01,TRUE,France,4
2022-02-01,FALSE,France,0
2022-02-01,FALSE,Japan,2
2022-02-01,TRUE,Japan,0
""".lstrip()

class TestMultiDimensionBaseSumMetric:

    # configuration in dbt_project.yml
    # setting bigquery as table to get around query complexity 
    # resource constraints with compunding views
    if os.getenv('dbt_target') == 'bigquery':
        @pytest.fixture(scope="class")
        def project_config_update(self):
            return {
            "name": "example",
            "models": {"+materialized": "table"}
            }
    else: 
        @pytest.fixture(scope="class")
        def project_config_update(self):
            return {
            "name": "example",
            "models": {"+materialized": "view"}
            }  

    # install current repo as package
    @pytest.fixture(scope="class")
    def packages(self):
        return {
            "packages": [
                {"local": os.getcwd()}
                ]
        }


    # everything that goes in the "seeds" directory
    @pytest.fixture(scope="class")
    def seeds(self):
        return {
            "fact_orders_source.csv": fact_orders_source_csv,
            "multi_dimension_base_sum_metric__expected.csv": multi_dimension_base_sum_metric__expected_csv,
        }

    # everything that goes in the "models" directory
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "fact_orders.sql": fact_orders_sql,
            "fact_orders.yml": fact_orders_yml,
            "multi_dimension_base_sum_metric.sql": multi_dimension_base_sum_metric_sql,
            "multi_dimension_base_sum_metric.yml": multi_dimension_base_sum_metric_yml
        }

    def test_build_completion(self,project,):
        # running deps to install package
        results = run_dbt(["deps"])

        # seed seeds
        results = run_dbt(["seed"])
        assert len(results) == 2

        # initial run
        results = run_dbt(["run"])
        assert len(results) == 3

        # test tests
        results = run_dbt(["test"]) # expect passing test
        assert len(results) == 1

        # # # validate that the results include pass
        result_statuses = sorted(r.status for r in results)
        assert result_statuses == ["pass"]