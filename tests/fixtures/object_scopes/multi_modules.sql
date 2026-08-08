CREATE OR ALTER PROCEDURE dbo.ProcA
    @Id INT
AS
BEGIN
    DECLARE @LocalA INT;
    SELECT s.Id
    INTO #StageA
    FROM dbo.SourceA AS s;
    EXEC sys.sp_executesql N'SELECT 1';
END;
GO

CREATE OR ALTER PROCEDURE dbo.ProcB
    @Code NVARCHAR(20)
AS
BEGIN
    DECLARE @LocalB INT;
    SELECT s.Code
    FROM dbo.SourceB AS s;
    EXEC dbo.HelperB;
END;
GO
