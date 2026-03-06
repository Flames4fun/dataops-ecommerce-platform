{{
    config(
        materialized='table',
        tags=['marts', 'fact', 'order_items']
    )
}}

with order_items as (

    select *
    from {{ ref('int_order_items_enriched') }}

),

orders as (

    select
        order_id,
        cast(purchased_at as date) as order_purchase_date
    from {{ ref('int_orders_enriched') }}

),

final as (

    select
        oi.order_item_key,
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,

        o.order_purchase_date,

        oi.price,
        oi.freight_value,
        oi.item_total,
        oi.is_zero_price,
        oi.is_negative_freight,

        oi.product_category_name,
        oi.category_name_en,

        oi.product_name_length,
        oi.product_description_length,
        oi.product_photos_qty,
        oi.weight_g,
        oi.length_cm,
        oi.height_cm,
        oi.width_cm,
        oi.volume_cm3,
        oi.density_kg_per_m3,

        oi.seller_city,
        oi.seller_state,
        oi.seller_zip_code

    from order_items oi
    left join orders o
        on oi.order_id = o.order_id

)

select * from final
