with
a as (select count(*) as c from {{ ref('int_orders_enriched') }}),
b as (select count(*) as c from {{ ref('fact_orders') }})
select a.c as int_count, b.c as fact_count
from a cross join b
where a.c <> b.c
