{{
    config(
        materialized=var('benchmark_marts_materialized', 'table'),
        tags=['marts', 'dimension', 'products']
    )
}}

with products as (

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
        density_kg_per_m3,
        is_missing_category,
        is_missing_dimensions
    from {{ ref('stg_products') }}
    where product_id is not null

),

categories as (

    select
        category_name_pt,
        category_name_en
    from {{ ref('stg_categories') }}

),

final as (

    select
        p.product_id,
        p.product_category_name as category_name_pt,
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

        p.is_missing_category,
        p.is_missing_dimensions

    from products p
    left join categories c
        on p.category_name_clean = c.category_name_pt

)

select * from final

