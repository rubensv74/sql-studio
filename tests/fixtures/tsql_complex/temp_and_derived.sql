CREATE OR ALTER PROCEDURE dbo.BuildSnapshot
AS
BEGIN
    SELECT s.Id
      INTO #Snapshot
      FROM dbo.SourceRows AS s;

    SELECT d.Id, o.Name
      FROM (
          SELECT Id
            FROM #Snapshot
      ) AS d
      JOIN dbo.OtherRows AS o ON o.Id = d.Id;
END;
