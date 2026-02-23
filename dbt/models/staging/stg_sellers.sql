{{
    config(
        materialized='view',
        tags=['staging', 'sellers']
    )
}}

with source as (

    select * from {{ source('raw', 'sellers') }}

),

renamed as (

    select
        seller_id,
        seller_zip_code_prefix as zip_code_prefix,
        seller_city as city,
        seller_state as state
    from source

),

cleaned as (

    select
        *,

        nullif(upper(trim(city)), '') as city_clean,
        nullif(upper(trim(state)), '') as state_clean,
        nullif(trim(cast(zip_code_prefix as varchar)), '') as zip_code_clean

    from renamed

),

with_flags as (

    select
        *,

        case
            when zip_code_clean is null
              or city_clean is null
              or state_clean is null
            then true
            else false
        end as is_missing_location

    from cleaned

),

with_surrogate_key as (

    select
        *,

        case
            when seller_id is null then null
            else {{ dbt_utils.generate_surrogate_key(['seller_id']) }}
        end as seller_key

    from with_flags

),

final as (

    select
        seller_key,
        seller_id,

        zip_code_prefix,
        city,
        state,

        zip_code_clean,
        city_clean,
        state_clean,

        is_missing_location

    from with_surrogate_key

)

select * from final
