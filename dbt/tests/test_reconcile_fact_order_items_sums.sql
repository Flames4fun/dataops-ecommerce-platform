with
a as (
    select
        round(coalesce(sum(price), 0), 4) as sum_price,
        round(coalesce(sum(freight_value), 0), 4) as sum_freight
    from {{ ref('int_order_items_enriched') }}
),
b as (
    select
        round(coalesce(sum(price), 0), 4) as sum_price,
        round(coalesce(sum(freight_value), 0), 4) as sum_freight
    from {{ ref('fact_order_items') }}
)
select
    a.sum_price as int_sum_price,
    b.sum_price as fact_sum_price,
    a.sum_freight as int_sum_freight,
    b.sum_freight as fact_sum_freight
from a cross join b
where a.sum_price <> b.sum_price
   or a.sum_freight <> b.sum_freight
