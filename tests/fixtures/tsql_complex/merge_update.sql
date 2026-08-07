CREATE OR ALTER PROCEDURE [warehouse].[Sync Orders]
AS
BEGIN
    MERGE INTO [warehouse].[Order Fact] AS target
    USING [staging].[Order Stage] AS source
      ON target.OrderId = source.OrderId
    WHEN MATCHED THEN
      UPDATE SET target.Amount = source.Amount;

    UPDATE f
       SET f.CustomerName = c.CustomerName
      FROM [warehouse].[Order Fact] AS f
      JOIN [crm].[Customer Master] AS c ON c.CustomerId = f.CustomerId;
END;
