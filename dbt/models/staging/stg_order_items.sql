{{
    config(
        materialized='view',
        tags=['staging', 'order_items']
    )
}}

with source as (

    select * from {{ source('raw', 'order_items') }}

),

renamed as (

    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        price,
        freight_value
    from source

),

calculated as (

    select
        *,

        price + freight_value as item_total,

        case
            when price <= 0 then true
            else false
        end as is_zero_price,

        case
            when freight_value < 0 then true
            else false
        end as is_negative_freight

    from renamed

),

with_surrogate_key as (

    select
        *,

        case
            when order_id is null or order_item_id is null then null
            else {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_id']) }}
        end as order_item_key

    from calculated

),

final as (

    select
        order_item_key,
        order_id,
        order_item_id,
        product_id,
        seller_id,

        price,
        freight_value,
        item_total,

        is_zero_price,
        is_negative_freight

    from with_surrogate_key

)

select * from final