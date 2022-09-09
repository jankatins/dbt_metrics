select *
from 
{{ dbt_metrics.calculate(
    metric('base_sum_metric'), 
    grain='day', 
    dimensions=['had_discount','is_weekend']) 
}}