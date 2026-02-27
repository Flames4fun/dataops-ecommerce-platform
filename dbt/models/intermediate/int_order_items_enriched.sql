{{
    config(
        materialized='view',
        tags=['intermediate', 'order_items']
    )
}}

with order_items as (

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
    from {{ ref('stg_order_items') }}

),

products as (

    select
        product_id,
        product_category_name,
        category_name_clean,
        product_name_length,
        product_description_length,
        product_photos_qty,
        weight_g,
        length_cm,
        height_cm,
        width_cm,
        volume_cm3,
        density_kg_per_m3
    from {{ ref('stg_products') }}

),

categories as (

    select
        category_name_pt,
        category_name_en
    from {{ ref('stg_categories') }}

),

sellers as (

    select
        seller_id,
        city_clean as seller_city,
        state_clean as seller_state,
        zip_code_clean as seller_zip_code
    from {{ ref('stg_sellers') }}

),

final as (

    select
        oi.order_item_key,
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,

        oi.price,
        oi.freight_value,
        oi.item_total,
        oi.is_zero_price,
        oi.is_negative_freight,

        p.product_category_name,
        c.category_name_en,

        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.weight_g,
        p.length_cm,
        p.height_cm,
        p.width_cm,
        p.volume_cm3,
        p.density_kg_per_m3,

        s.seller_city,
        s.seller_state,
        s.seller_zip_code

    from order_items oi
    left join products p
        on oi.product_id = p.product_id
    left join categories c
        on p.category_name_clean = c.category_name_pt
    left join sellers s
        on oi.seller_id = s.seller_id

)

select * from final
