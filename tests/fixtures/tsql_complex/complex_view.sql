CREATE OR ALTER VIEW [reporting].[Order Summary]
AS
WITH [Recent Orders] AS (
    SELECT o.OrderId, o.CustomerId
    FROM [OtherDb].[sales].[Order Header] AS o
    WHERE o.CreatedAt >= '2026-01-01'
)
SELECT r.OrderId, c.CustomerName, a.Flag
FROM [Recent Orders] AS r
JOIN [crm].[Customer Master] AS c ON c.CustomerId = r.CustomerId
LEFT JOIN (
    SELECT OrderId, MAX(Flag) AS Flag
    FROM [audit].[Order Flags]
    GROUP BY OrderId
) AS a ON a.OrderId = r.OrderId;
