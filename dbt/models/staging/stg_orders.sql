{{
    config(
        materialized='view',
        tags=['staging', 'orders']
    )
}}

with source as (

    select * from {{ source('raw', 'orders') }}

),

renamed as (

    select
        order_id,
        customer_id,
        order_status,

        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date

    from source

),

parsed_timestamps as (

    select
        *,

        try_cast(order_purchase_timestamp as timestamp) as purchased_at,
        try_cast(order_approved_at as timestamp) as approved_at,
        try_cast(order_delivered_carrier_date as timestamp) as delivered_carrier_at,
        try_cast(order_delivered_customer_date as timestamp) as delivered_customer_at,
        try_cast(order_estimated_delivery_date as timestamp) as estimated_delivery_at

    from renamed

),

with_metrics as (

    select
        *,

        date_diff('day', purchased_at, approved_at) as days_to_approve,
        date_diff('day', purchased_at, delivered_carrier_at) as days_to_carrier,
        date_diff('day', purchased_at, delivered_customer_at) as days_to_delivery,
        date_diff('day', estimated_delivery_at, delivered_customer_at) as delivery_delay_days,

        case
            when estimated_delivery_at is null then false
            when delivered_customer_at > estimated_delivery_at then true
            when delivered_customer_at is null and current_timestamp > estimated_delivery_at then true
            else false
        end as is_late_delivery,

        case
            when order_status = 'canceled' then true
            else false
        end as is_canceled,

        case
            when order_status = 'delivered' then true
            else false
        end as is_delivered,

        case
            when purchased_at is null then true
            else false
        end as is_missing_purchased_at

    from parsed_timestamps

),

final as (

    select
        order_id,
        customer_id,
        order_status,

        purchased_at,
        approved_at,
        delivered_carrier_at,
        delivered_customer_at,
        estimated_delivery_at,

        days_to_approve,
        days_to_carrier,
        days_to_delivery,
        delivery_delay_days,

        is_late_delivery,
        is_canceled,
        is_delivered,
        is_missing_purchased_at

    from with_metrics

)

select * from final
