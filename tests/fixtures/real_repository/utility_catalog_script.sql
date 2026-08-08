SET NOCOUNT ON;

CREATE TABLE #ObjectDefinitions
(
    ObjectId int NOT NULL,
    SchemaName sysname NOT NULL,
    ObjectName sysname NOT NULL
);

INSERT INTO #ObjectDefinitions (ObjectId, SchemaName, ObjectName)
SELECT
    tableInfo.object_id,
    schemaInfo.name,
    tableInfo.name
FROM sys.tables AS tableInfo
INNER JOIN sys.schemas AS schemaInfo
    ON schemaInfo.schema_id = tableInfo.schema_id;

SELECT *
FROM #ObjectDefinitions;
