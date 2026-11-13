-- Standard SQL (SELECT, JOIN, GROUP BY, subqueries, CTE, window function).
-- Written for SQLite; the syntax also works in PostgreSQL with minor changes (e.g. date functions).
-- Revenue = quantity * unit_price for orders with status 'Delivered'.

-- Q1: Monthly revenue
SELECT substr(o.order_date, 1, 7) AS month,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Delivered'
GROUP BY month
ORDER BY month;

-- Q2: Revenue and units by product category
SELECT p.category,
       SUM(oi.quantity) AS units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY revenue DESC;

-- Q3: Top 10 customers by spend
SELECT c.customer_id, c.customer_name, c.city,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Delivered'
GROUP BY c.customer_id, c.customer_name, c.city
ORDER BY total_spent DESC
LIMIT 10;

-- Q4: Customers who spent more than the average customer (subquery)
SELECT customer_id, ROUND(total_spent, 2) AS total_spent
FROM (SELECT o.customer_id, SUM(oi.quantity * oi.unit_price) AS total_spent
      FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
      WHERE o.status = 'Delivered' GROUP BY o.customer_id)
WHERE total_spent > (SELECT AVG(t) FROM (SELECT SUM(oi.quantity * oi.unit_price) AS t
                                         FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
                                         WHERE o.status = 'Delivered' GROUP BY o.customer_id))
ORDER BY total_spent DESC;

-- Q5: City-wise revenue and average order value
SELECT c.city,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'Delivered'
GROUP BY c.city
ORDER BY revenue DESC;

-- Q6: Order status mix by payment method (cancel and return rates)
SELECT payment_method,
       COUNT(*) AS orders,
       ROUND(100.0 * SUM(status = 'Cancelled') / COUNT(*), 1) AS cancel_rate_pct,
       ROUND(100.0 * SUM(status = 'Returned')  / COUNT(*), 1) AS return_rate_pct
FROM orders
GROUP BY payment_method
ORDER BY cancel_rate_pct DESC;

-- Q7: Top 5 products by revenue (JOIN + GROUP BY)
SELECT p.product_name, p.category,
       SUM(oi.quantity) AS units_sold,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'Delivered'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 5;

-- Q8: Running total of monthly revenue (CTE + window function)
WITH monthly AS (
  SELECT substr(o.order_date, 1, 7) AS month,
         SUM(oi.quantity * oi.unit_price) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.status = 'Delivered'
  GROUP BY month)
SELECT month, ROUND(revenue, 2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2) AS running_total
FROM monthly ORDER BY month;

-- Q9: Customers grouped by number of delivered orders (CASE + subquery)
SELECT CASE WHEN n_orders <= 5  THEN '1-5 orders'
            WHEN n_orders <= 10 THEN '6-10 orders'
            WHEN n_orders <= 15 THEN '11-15 orders'
            ELSE '16+ orders' END AS order_band,
       COUNT(*) AS customers
FROM (SELECT customer_id, COUNT(*) AS n_orders FROM orders WHERE status = 'Delivered' GROUP BY customer_id)
GROUP BY order_band
ORDER BY MIN(n_orders);
