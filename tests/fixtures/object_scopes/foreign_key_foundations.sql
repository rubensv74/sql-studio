IF OBJECT_ID(N'[warroom].[ExportBatch]', N'U') IS NULL
BEGIN
    CREATE TABLE [warroom].[ExportBatch]
    (
        [ExportBatchId] bigint NOT NULL,
        CONSTRAINT [PK_ExportBatch] PRIMARY KEY ([ExportBatchId])
    );
END;
GO

IF OBJECT_ID(N'[warroom].[ExportBatchRow]', N'U') IS NULL
BEGIN
    CREATE TABLE [warroom].[ExportBatchRow]
    (
        [ExportBatchId] bigint NOT NULL,
        [WorkItemId] bigint NOT NULL,
        CONSTRAINT [PK_ExportBatchRow] PRIMARY KEY ([ExportBatchId], [WorkItemId]),
        CONSTRAINT [FK_ExportBatchRow_ExportBatch]
            FOREIGN KEY ([ExportBatchId])
            REFERENCES [warroom].[ExportBatch] ([ExportBatchId])
    );
END;
GO

IF OBJECT_ID(N'[warroom].[ImportBatch]', N'U') IS NULL
BEGIN
    CREATE TABLE [warroom].[ImportBatch]
    (
        [ImportBatchId] bigint NOT NULL,
        [ExportBatchId] bigint NOT NULL,
        CONSTRAINT [PK_ImportBatch] PRIMARY KEY ([ImportBatchId]),
        CONSTRAINT [FK_ImportBatch_ExportBatch]
            FOREIGN KEY ([ExportBatchId])
            REFERENCES [warroom].[ExportBatch] ([ExportBatchId])
    );
END;
GO

GRANT REFERENCES ON OBJECT::[warroom].[ExportBatch] TO [app_role];
GO
