CREATE OR ALTER PROCEDURE [ops].[usp_LoadPayload]
    @RowsJson nvarchar(max)
AS
BEGIN
    SET NOCOUNT ON;

    CREATE TABLE #Stage
    (
        ItemId bigint NOT NULL,
        ItemName nvarchar(200) NULL
    );

    INSERT INTO #Stage (ItemId, ItemName)
    SELECT
        TRY_CONVERT(bigint, payload.ItemId),
        payload.ItemName
    FROM OPENJSON(@RowsJson)
    WITH
    (
        ItemId nvarchar(50) '$.ItemId',
        ItemName nvarchar(200) '$.ItemName'
    ) AS payload;

    SELECT
        stage.ItemId,
        referenceData.DisplayName
    FROM #Stage AS stage
    INNER JOIN dbo.ReferenceData AS referenceData
        ON referenceData.ItemId = stage.ItemId;
END;
