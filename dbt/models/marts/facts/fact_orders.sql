{{
    config(
        materialized='table',
        tags=['marts', 'fact', 'orders']
    )
}}

with orders as (

    select *
    from {{ ref('int_orders_enriched') }}

),

final as (

    select
        order_id,
        customer_id,
        customer_unique_id,

        order_status,

        purchased_at,
        cast(purchased_at as date) as order_purchase_date,

        approved_at,
        cast(approved_at as date) as order_approved_date,

        delivered_carrier_at,
        cast(delivered_carrier_at as date) as order_delivered_carrier_date,

        delivered_customer_at,
        cast(delivered_customer_at as date) as order_delivered_customer_date,

        estimated_delivery_at,
        cast(estimated_delivery_at as date) as order_estimated_delivery_date,

        days_to_approve,
        days_to_carrier,
        days_to_delivery,
        delivery_delay_days,

        is_late_delivery,
        is_canceled,
        is_delivered,
        is_missing_purchased_at

    from orders

)

select * from final
