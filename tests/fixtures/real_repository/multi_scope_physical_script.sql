SELECT * FROM dbo.BeforeTarget;
GO

CREATE TABLE dbo.LocalTable
(
    Id int NOT NULL
);
GO

SELECT * FROM dbo.AfterTarget;
DECLARE @sql nvarchar(max) = N'SELECT 1';
EXEC sp_executesql @sql;
