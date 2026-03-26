with order_dates as (
    select distinct
        order_purchase_date as kpi_date
    from {{ ref('fact_orders') }}
    where order_purchase_date is not null
),
gmv_expected as (
    select
        fo.order_purchase_date as kpi_date,
        round(coalesce(sum(foi.item_total), 0), 4) as gmv,
        count(distinct fo.order_id) as orders_for_aov
    from {{ ref('fact_orders') }} fo
    join {{ ref('fact_order_items') }} foi
        on fo.order_id = foi.order_id
    where fo.order_purchase_date is not null
      and fo.is_canceled = false
    group by 1
),
expected as (
    select
        od.kpi_date,
        round(coalesce(ge.gmv, 0), 4) as gmv,
        coalesce(ge.orders_for_aov, 0) as orders_for_aov
    from order_dates od
    left join gmv_expected ge
        on od.kpi_date = ge.kpi_date
),
actual as (
    select
        kpi_date,
        round(coalesce(gmv, 0), 4) as gmv,
        orders_for_aov
    from {{ ref('mart_kpis_daily') }}
),
diff as (
    select
        coalesce(e.kpi_date, a.kpi_date) as kpi_date,
        e.gmv as expected_gmv,
        a.gmv as actual_gmv,
        e.orders_for_aov as expected_orders_for_aov,
        a.orders_for_aov as actual_orders_for_aov
    from expected e
    full outer join actual a
        on e.kpi_date = a.kpi_date
    where coalesce(e.gmv, -1) <> coalesce(a.gmv, -1)
       or coalesce(e.orders_for_aov, -1) <> coalesce(a.orders_for_aov, -1)
)

select * from diff
