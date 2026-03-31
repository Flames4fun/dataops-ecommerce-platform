{{
    config(
        materialized=var('benchmark_marts_materialized', 'table'),
        tags=['marts', 'dimension', 'customers']
    )
}}

with base_customers as (

    select
        customer_unique_id,
        customer_id,
        zip_code_clean as customer_zip_code_prefix,
        city_clean as customer_city,
        state_clean as customer_state
    from {{ ref('stg_customers') }}
    where customer_unique_id is not null

),

deduped_customers as (

    select
        customer_unique_id,
        customer_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    from (
        select
            *,
            row_number() over (
                partition by customer_unique_id
                order by customer_id desc
            ) as rn
        from base_customers
    ) ranked
    where rn = 1

),

orders_metrics as (

    select
        customer_unique_id,
        min(purchased_at) as first_order_at,
        max(purchased_at) as last_order_at,
        count(distinct order_id) as orders_count
    from {{ ref('int_orders_enriched') }}
    where customer_unique_id is not null
    group by 1

),

final as (

    select
        dc.customer_unique_id,
        dc.customer_id,
        dc.customer_zip_code_prefix,
        dc.customer_city,
        dc.customer_state,
        om.first_order_at,
        om.last_order_at,
        coalesce(om.orders_count, 0) as orders_count
    from deduped_customers dc
    left join orders_metrics om
        on dc.customer_unique_id = om.customer_unique_id

)

select * from final

