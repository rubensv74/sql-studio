CREATE OR ALTER PROCEDURE [warroom].[usp_RegisterSnapshot]
    @LogId              bigint,
    @ProjectId          bigint,
    @ExportType         nvarchar(30),
    @CreatedBy          nvarchar(320),
    @Amount             decimal(18,4) = 0,
    @ExpiresAtUtc       datetime2(3) = NULL,
    @IsReady            bit = 0 OUTPUT
AS
BEGIN
    SET @ExportType = NULLIF(LTRIM(RTRIM(@ExportType)), N'');
    SET @CreatedBy = NULLIF(LTRIM(RTRIM(@CreatedBy)), N'');
    SET @ExpiresAtUtc = COALESCE(@ExpiresAtUtc, SYSUTCDATETIME());

    DECLARE @LocalBatchId uniqueidentifier;
    DECLARE @LocalStatus varchar(20);

    SELECT @LocalBatchId = ExportBatchId
    FROM [warroom].[ExportBatch]
    WHERE ProjectId = @ProjectId;
END;
GO
