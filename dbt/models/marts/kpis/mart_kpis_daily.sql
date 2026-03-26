{{
    config(
        materialized='table',
        tags=['marts', 'kpi', 'daily']
    )
}}

with orders_daily as (
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

gmv_daily as (
    select
        fo.order_purchase_date as kpi_date,
        coalesce(sum(foi.item_total), 0) as gmv,
        count(distinct fo.order_id) as orders_for_aov
    from {{ ref('fact_orders') }} fo
    join {{ ref('fact_order_items') }} foi
        on fo.order_id = foi.order_id
    where fo.order_purchase_date is not null
      and fo.is_canceled = false
    group by 1
),

final as (
    select
        od.kpi_date,
        od.total_orders,
        od.canceled_orders,
        od.non_canceled_orders,
        od.delivered_orders,
        od.late_delivered_orders,
        coalesce(gd.orders_for_aov, 0) as orders_for_aov,
        coalesce(gd.gmv, 0) as gmv,
        coalesce(gd.gmv, 0) / nullif(coalesce(gd.orders_for_aov, 0), 0) as aov,
        od.canceled_orders * 1.0 / nullif(od.total_orders, 0) as cancel_rate,
        od.late_delivered_orders * 1.0 / nullif(od.delivered_orders, 0) as late_delivery_rate
    from orders_daily od
    left join gmv_daily gd
        on od.kpi_date = gd.kpi_date
)

select * from final

