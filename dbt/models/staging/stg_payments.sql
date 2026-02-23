{{
    config(
        materialized='view',
        tags=['staging', 'payments']
    )
}}

with source as (

    select * from {{ source('raw', 'payments') }}

),

renamed as (

    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    from source

),

cleaned as (

    select
        *,

        nullif(lower(trim(payment_type)), '') as payment_type_clean,

        case
            when payment_value < 0 then true
            else false
        end as is_negative_value,

        case
            when payment_installments < 1 then true
            else false
        end as is_invalid_installments,

        case
            when payment_type_clean in ('credit_card', 'debit_card') and payment_installments > 24 then true
            else false
        end as is_excessive_installments

    from renamed

),

with_surrogate_key as (

    select
        *,

        case
            when order_id is null or payment_sequential is null then null
            else {{ dbt_utils.generate_surrogate_key(['order_id', 'payment_sequential']) }}
        end as payment_key

    from cleaned

),

final as (

    select
        payment_key,
        order_id,
        payment_sequential,
        payment_type,
        payment_type_clean,
        payment_installments,
        payment_value,
        is_negative_value,
        is_invalid_installments,
        is_excessive_installments
    from with_surrogate_key

)

select * from final
