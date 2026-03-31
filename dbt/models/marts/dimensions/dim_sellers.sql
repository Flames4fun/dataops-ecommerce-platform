{{
    config(
        materialized=var('benchmark_marts_materialized', 'table'),
        tags=['marts', 'dimension', 'sellers']
    )
}}

with base_sellers as (

    select
        seller_id,
        zip_code_clean as seller_zip_code_prefix,
        city_clean as seller_city,
        state_clean as seller_state,
        is_missing_location
    from {{ ref('stg_sellers') }}
    where seller_id is not null

),

deduped_sellers as (

    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,
        is_missing_location
    from (
        select
            *,
            row_number() over (
                partition by seller_id
                order by
                    is_missing_location asc,
                    seller_state desc,
                    seller_city desc,
                    seller_zip_code_prefix desc
            ) as rn
        from base_sellers
    ) ranked
    where rn = 1

)

select * from deduped_sellers

