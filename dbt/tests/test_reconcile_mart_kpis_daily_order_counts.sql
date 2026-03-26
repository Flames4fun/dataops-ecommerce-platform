with expected as (
    select
        order_purchase_date as kpi_date,
        count(*) as total_orders,
        sum(case when is_canceled then 1 else 0 end) as canceled_orders,
        sum(case when not is_canceled then 1 else 0 end) as non_canceled_orders,
        sum(case when is_delivered then 1 else 0 end) as delivered_orders,
        sum(case when is_delivered and is_late_delivery then 1 else 0 end) as late_delivered_orders
    from {{ ref('fact_orders') }}
    where order_purchase_date is not null
    group by 1
),
actual as (
    select
        kpi_date,
        total_orders,
        canceled_orders,
        non_canceled_orders,
        delivered_orders,
        late_delivered_orders
    from {{ ref('mart_kpis_daily') }}
),
diff as (
    select
        coalesce(e.kpi_date, a.kpi_date) as kpi_date,
        e.total_orders as expected_total_orders,
        a.total_orders as actual_total_orders,
        e.canceled_orders as expected_canceled_orders,
        a.canceled_orders as actual_canceled_orders,
        e.non_canceled_orders as expected_non_canceled_orders,
        a.non_canceled_orders as actual_non_canceled_orders,
        e.delivered_orders as expected_delivered_orders,
        a.delivered_orders as actual_delivered_orders,
        e.late_delivered_orders as expected_late_delivered_orders,
        a.late_delivered_orders as actual_late_delivered_orders
    from expected e
    full outer join actual a
        on e.kpi_date = a.kpi_date
    where coalesce(e.total_orders, -1) <> coalesce(a.total_orders, -1)
       or coalesce(e.canceled_orders, -1) <> coalesce(a.canceled_orders, -1)
       or coalesce(e.non_canceled_orders, -1) <> coalesce(a.non_canceled_orders, -1)
       or coalesce(e.delivered_orders, -1) <> coalesce(a.delivered_orders, -1)
       or coalesce(e.late_delivered_orders, -1) <> coalesce(a.late_delivered_orders, -1)
)

select * from diff

