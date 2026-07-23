# Architecture

## Cross Reference Engine

The Cross Reference Engine extends the Dependency Engine.

### Components

- CrossReference
- CrossReferenceEngine
- CrossReferenceAnalyzer
- CrossReferenceSerializer

### Flow

SQL -> Parser -> DependencyGraph -> CrossReferenceEngine -> JSON / CLI

### Public API

- analyze()
- analyze_many()
- incoming()
- outgoing()

