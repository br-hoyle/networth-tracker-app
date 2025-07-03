SELECT
  DATE_TRUNC('month', STRPTIME(full_date, '%m/%d/%Y')) AS full_date,
  "group",
  SUM(amount) AS total_amount
FROM transactions t
where "group" != 'Savings'
GROUP BY DATE_TRUNC('month', STRPTIME(full_date, '%m/%d/%Y')), "group"
ORDER BY full_date, "group";
