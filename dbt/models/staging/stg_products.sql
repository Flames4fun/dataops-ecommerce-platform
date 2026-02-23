{{
    config(
        materialized='view',
        tags=['staging', 'products']
    )
}}

with source as (

    select * from {{ source('raw', 'products') }}

),

renamed as (

    select
        product_id,
        product_category_name,
        product_name_lenght as product_name_length,
        product_description_lenght as product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm
    from source

),

cleaned as (

    select
        *,

        nullif(lower(trim(product_category_name)), '') as category_name_clean,

        product_weight_g as weight_g,
        product_length_cm as length_cm,
        product_height_cm as height_cm,
        product_width_cm as width_cm,

        case
            when product_category_name is null then true
            else false
        end as is_missing_category,

        case
            when product_weight_g is null
              or product_length_cm is null
              or product_height_cm is null
              or product_width_cm is null
            then true
            else false
        end as is_missing_dimensions

    from renamed

),

with_volume as (

    select
        *,

        (length_cm * height_cm * width_cm) as volume_cm3

    from cleaned

),

with_density as (

    select
        *,

        case
            when weight_g > 0
             and length_cm > 0
             and height_cm > 0
             and width_cm > 0
            then (weight_g * 1000.0) / volume_cm3
            else null
        end as density_kg_per_m3

    from with_volume

),

with_surrogate_key as (

    select
        *,

        case
            when product_id is null then null
            else {{ dbt_utils.generate_surrogate_key(['product_id']) }}
        end as product_key

    from with_density

),

final as (

    select
        product_key,
        product_id,

        product_category_name,
        category_name_clean,

        product_name_length,
        product_description_length,
        product_photos_qty,

        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,

        weight_g,
        length_cm,
        height_cm,
        width_cm,

        volume_cm3,
        density_kg_per_m3,

        is_missing_category,
        is_missing_dimensions

    from with_surrogate_key

)

select * from final
