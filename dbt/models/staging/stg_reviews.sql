{{
    config(
        materialized='view',
        tags=['staging', 'reviews']
    )
}}

with source as (

    select * from {{ source('raw', 'reviews') }}

),

renamed as (

    select
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp
    from source

),

cleaned_text as (

    select
        *,

        nullif(trim(review_comment_title), '') as review_comment_title_clean,
        nullif(trim(review_comment_message), '') as review_comment_message_clean

    from renamed

),

parsed_timestamps as (

    select
        *,

        review_creation_date as created_at,
        review_answer_timestamp as answered_at

    from cleaned_text

),

with_flags as (

    select
        *,

        case
            when review_comment_title_clean is not null
              or review_comment_message_clean is not null
            then true
            else false
        end as has_comment,

        case
            when answered_at is not null then true
            else false
        end as has_answer,

        case
            when created_at is null then true
            else false
        end as is_missing_created_at

    from parsed_timestamps

),

with_surrogate_key as (

    select
        *,

        case
            when review_id is null or order_id is null then null
            else {{ dbt_utils.generate_surrogate_key(['review_id', 'order_id']) }}
        end as review_key

    from with_flags

),

final as (

    select
        review_key,
        review_id,
        order_id,

        review_score,
        review_comment_title,
        review_comment_message,

        created_at,
        answered_at,

        has_comment,
        has_answer,
        is_missing_created_at

    from with_surrogate_key

)

select * from final
