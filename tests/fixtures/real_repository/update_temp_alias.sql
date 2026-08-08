CREATE OR ALTER PROCEDURE warroom.usp_UpdateSnapshot
AS
BEGIN
    SELECT s.Id, s.ValueText
    INTO #ExportBase
    FROM dbo.SourceRows AS s;

    UPDATE eb
    SET ValueText = snapshot.ValueText
    FROM #ExportBase AS eb
    CROSS APPLY
    (
        SELECT eb.ValueText
    ) AS snapshot(ValueText);
END;
