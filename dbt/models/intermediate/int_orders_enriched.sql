{{
    config(
        materialized='view',
        tags=['intermediate', 'orders']
    )
}}

with orders as (

    select *
    from {{ ref('stg_orders') }}

),

customers as (

    select
        customer_id,
        customer_unique_id
    from {{ ref('stg_customers') }}

),

final as (

    select
        o.order_id,
        o.customer_id,
        c.customer_unique_id,

        o.order_status,

        o.purchased_at,
        o.approved_at,
        o.delivered_carrier_at,
        o.delivered_customer_at,
        o.estimated_delivery_at,

        o.days_to_approve,
        o.days_to_carrier,
        o.days_to_delivery,
        o.delivery_delay_days,

        o.is_late_delivery,
        o.is_canceled,
        o.is_delivered,
        o.is_missing_purchased_at

    from orders o
    left join customers c
        on o.customer_id = c.customer_id

)

select * from final
