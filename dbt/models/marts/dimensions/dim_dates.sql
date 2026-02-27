{{
    config(
        materialized='table',
        tags=['marts', 'dimension', 'dates']
    )
}}

with date_spine as (

    select
        cast(date_day as date) as date_day
    from generate_series(
        date '2016-01-01',
        date '2018-12-31',
        interval 1 day
    ) as t(date_day)

),

final as (

    select
        date_day,

        cast(date_part('year', date_day) as integer) as year,
        cast(date_part('quarter', date_day) as integer) as quarter,
        cast(date_part('month', date_day) as integer) as month,
        strftime(date_day, '%Y-%m') as year_month,
        cast(strftime(date_day, '%G') as integer) as iso_year,

        cast(strftime(date_day, '%V') as integer) as week_of_year,
        strftime(date_day, '%G-%V') as year_week,

        cast(date_part('day', date_day) as integer) as day_of_month,
        cast(date_part('isodow', date_day) as integer) as day_of_week,
        strftime(date_day, '%A') as day_name,
        strftime(date_day, '%B') as month_name,

        (date_part('isodow', date_day) in (6, 7)) as is_weekend,

        (date_day = date_trunc('month', date_day)) as is_month_start,
        (date_day = (date_trunc('month', date_day) + interval 1 month - interval 1 day)) as is_month_end,

        (date_day = date_trunc('quarter', date_day)) as is_quarter_start,
        (date_day = (date_trunc('quarter', date_day) + interval 3 month - interval 1 day)) as is_quarter_end,

        (date_day = date_trunc('year', date_day)) as is_year_start,
        (date_day = (date_trunc('year', date_day) + interval 1 year - interval 1 day)) as is_year_end

    from date_spine

)

select * from final
