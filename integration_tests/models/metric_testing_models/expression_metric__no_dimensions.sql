select *
from 
{{ dbt_metrics.calculate(
    metric('expression_metric'), 
    grain='day', 
    start_date = '2022-01-01',
    end_date = '2022-01-10') 
}}