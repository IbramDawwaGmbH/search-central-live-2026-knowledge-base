# BigQuery: top queries per page from the Search Console bulk export

Run against the `searchdata_url_impression` table of the bulk data export (default dataset `searchconsole`; replace the project name). Anonymized queries have an empty query and `is_anonymized_query` set, so they are left out of the ranking here but should stay in totals.

```sql
-- Top non-anonymized queries per page, web search, last 28 days
SELECT
  url,
  query,
  SUM(clicks) AS clicks,
  SUM(impressions) AS impressions,
  SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
  SAFE_DIVIDE(SUM(sum_position), SUM(impressions)) + 1 AS avg_position
FROM `my-project.searchconsole.searchdata_url_impression`
WHERE search_type = 'WEB'
  AND data_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
  AND NOT is_anonymized_query
GROUP BY url, query
ORDER BY clicks DESC
LIMIT 1000;
```
