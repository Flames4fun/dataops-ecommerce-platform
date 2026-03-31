{{
    config(
        materialized=var('benchmark_marts_materialized', 'table'),
        tags=['marts', 'fact', 'payments']
    )
}}

with payments as (
    select * from {{ ref('stg_payments') }}
),

orders as (
    select
        order_id,
        cast(purchased_at as date) as order_purchase_date
    from {{ ref('int_orders_enriched') }}
),

final as (
    select
        p.payment_key,
        p.order_id,
        p.payment_sequential,
        p.payment_type,
        p.payment_type_clean,
        p.payment_installments,
        p.payment_value,
        p.is_negative_value,
        p.is_invalid_installments,
        p.is_excessive_installments,
        o.order_purchase_date
    from payments p
    left join orders o
        on p.order_id = o.order_id
)

select * from final
