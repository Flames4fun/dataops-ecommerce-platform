# Business Metrics Definitions

This document defines the core business metrics used in the project for consistent KPI tracking.

## Scope

- Primary fact tables: `marts.fact_orders`, `marts.fact_order_items`
- Default time grain: `order_purchase_date` (daily)
- Currency: BRL

## Metrics

### GMV

- Definition: Gross Merchandise Value of sold items.
- Formula: `SUM(item_total)`
- Grain: Daily (`order_purchase_date`), aggregable to week/month.
- Filters:
  - Include only orders with `is_canceled = false`.
  - Recommended for "realized GMV": also filter `is_delivered = true`.

SQL reference:

```sql
select
  fo.order_purchase_date,
  sum(foi.item_total) as gmv
from marts.fact_order_items foi
join marts.fact_orders fo on fo.order_id = foi.order_id
where fo.is_canceled = false
group by 1;
```

### AOV

- Definition: Average Order Value.
- Formula: `GMV / COUNT(DISTINCT order_id)`
- Grain: Daily (`order_purchase_date`), aggregable to week/month.
- Filters:
  - Same population as GMV (recommended: non-canceled orders).

SQL reference:

```sql
select
  fo.order_purchase_date,
  sum(foi.item_total) / nullif(count(distinct fo.order_id), 0) as aov
from marts.fact_order_items foi
join marts.fact_orders fo on fo.order_id = foi.order_id
where fo.is_canceled = false
group by 1;
```

### cancel_rate

- Definition: Share of canceled orders over total orders.
- Formula: `COUNT_IF(is_canceled) / COUNT(order_id)`
- Grain: Daily (`order_purchase_date`), aggregable to week/month.
- Filters:
  - Include all orders in denominator.

SQL reference:

```sql
select
  order_purchase_date,
  avg(case when is_canceled then 1.0 else 0.0 end) as cancel_rate
from marts.fact_orders
group by 1;
```

### late_delivery_rate

- Definition: Share of delivered orders that arrived after estimated date.
- Formula: `COUNT_IF(is_late_delivery) / COUNT_IF(is_delivered)`
- Grain: Daily (`order_purchase_date`), aggregable to week/month.
- Filters:
  - Denominator should include delivered orders only.
  - Exclude canceled/non-delivered orders from denominator.

SQL reference:

```sql
select
  order_purchase_date,
  sum(case when is_late_delivery and is_delivered then 1 else 0 end) * 1.0
    / nullif(sum(case when is_delivered then 1 else 0 end), 0) as late_delivery_rate
from marts.fact_orders
group by 1;
```

## Notes

- Keep metric filters identical across dashboards and API endpoints.
- For monthly reporting, aggregate from daily grain rather than recalculating from mixed granularities.
