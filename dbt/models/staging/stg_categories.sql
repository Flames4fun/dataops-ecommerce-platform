{{
    config(
        materialized='view',
        tags=['staging', 'categories']
    )
}}

with source as (

    select * from {{ source('raw', 'categories') }}

),

renamed as (

    select
        product_category_name as category_name_pt_raw,
        product_category_name_english as category_name_en_raw
    from source

),

cleaned as (

    select
        nullif(lower(trim(category_name_pt_raw)), '') as category_name_pt,
        nullif(lower(trim(category_name_en_raw)), '') as category_name_en
    from renamed

),

with_surrogate_key as (

    select
        *,

        case
            when category_name_pt is null then null
            else {{ dbt_utils.generate_surrogate_key(['category_name_pt']) }}
        end as category_key

    from cleaned

),

final as (

    select
        category_key,
        category_name_pt,
        category_name_en
    from with_surrogate_key

)

select * from final
