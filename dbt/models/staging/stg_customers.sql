{{
    config(
        materialized='view',
        tags=['staging', 'customers']
    )
}}

with source as (
    
    select * from {{ source('raw', 'customers') }}

),

renamed as (

    select
        -- Primary Key (surrogate per order)
        customer_id,
        
        -- Natural Key 
        customer_unique_id,
        
        -- Location attributes
        customer_zip_code_prefix as zip_code_prefix,
        customer_city as city,
        customer_state as state,
        
        -- Metadata 
        -- _loaded_at as loaded_at,
        
        -- Data quality flags
        case 
            when customer_unique_id is null then true
            else false
        end as is_missing_natural_key,
        
        case
            when customer_zip_code_prefix is null 
                or customer_city is null 
                or customer_state is null 
            then true
            else false
        end as is_missing_location

    from source

),

cleaned as (

    select
        *,
        
        -- Standardize location fields
        trim(upper(city)) as city_clean,
        trim(upper(state)) as state_clean,
        trim(zip_code_prefix) as zip_code_clean,
        
        -- Generate surrogate key for staging row grain (1 row per customer_id)
        case
            when customer_id is null then null
            else {{ dbt_utils.generate_surrogate_key(['customer_id']) }}
        end as customer_key

    from renamed

),

final as (

    select
        -- Keys
        customer_id,
        customer_unique_id,
        customer_key,
        
        -- Location (raw)
        zip_code_prefix,
        city,
        state,
        
        -- Location (cleaned)
        zip_code_clean,
        city_clean,
        state_clean,
        
        -- Quality flags
        is_missing_natural_key,
        is_missing_location
        
        -- Metadata
        -- loaded_at

    from cleaned

)

select * from final