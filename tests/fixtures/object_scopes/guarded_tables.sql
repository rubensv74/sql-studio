IF OBJECT_ID(N'[warroom].[ExportBatch]', N'U') IS NULL
BEGIN
    CREATE TABLE [warroom].[ExportBatch]
    (
        [ExportBatchId] bigint NOT NULL,
        CONSTRAINT [PK_ExportBatch] PRIMARY KEY ([ExportBatchId])
    );
END;
GO

IF OBJECT_ID(N'[warroom].[ImportBatch]', N'U') IS NULL
BEGIN
    CREATE TABLE [warroom].[ImportBatch]
    (
        [ImportBatchId] bigint NOT NULL,
        CONSTRAINT [PK_ImportBatch] PRIMARY KEY ([ImportBatchId])
    );
END;
GO
