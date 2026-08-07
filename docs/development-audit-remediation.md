# SQL Studio — Cierre de la auditoría de desarrollo

**Fecha de cierre:** 2026-08-08  
**Auditoría de origen:** `docs/development-audit.md`  
**Baseline auditado:** `c7cdfafb6bfb9e662290320cfac5d6cffb040c89`  
**Baseline estabilizado:** `1f0e628433323b4afde2f034eef2d68b445d1082`  
**Versión estabilizada:** `0.12.0`  
**PR de remediación:** `#1 — Baseline Stabilization: impact semantics, CI and documentation`

---

## 1. Estado

La auditoría original se conserva sin modificaciones como fotografía histórica del estado detectado el 8 de agosto de 2026.

Los hallazgos que bloqueaban continuar el roadmap fueron remediados en `0.12.0`. Este documento también registra el cierre posterior de deuda originalmente clasificada como no bloqueante para evitar que vuelva a interpretarse como pendiente.

## 2. Hallazgos cerrados en la estabilización 0.12.0

### P0.1 — Semántica de Impact Analysis

**Cerrado.** El contrato del grafo queda formalizado como `source -> target`, donde `source` depende de `target`. Impact Analysis recorre `DependencyGraph.dependents_of()` transitivamente.

### P0.2 — Clasificación directa/indirecta del informe HTML

**Cerrado.** El informe deriva impactos directos de los hijos de primer nivel y clasifica como indirectos los niveles posteriores.

### P1.1 — Árbol y contrato JSON

**Decisión cerrada.** El schema JSON `1.0` permanece deliberadamente plano por compatibilidad; incorporar árbol requerirá una nueva versión.

### P1.2 — Test de contrato débil

**Cerrado.** El test verifica la existencia real de `docs/impact-report.md` y sus secciones obligatorias.

### P1.3 — Ausencia de CI

**Cerrado.** Existe CI Python 3.12 con compilación, imports, suite completa y smoke tests de CLI; posteriormente se amplió con validación de wheel instalado.

### P1.4 — Versiones de Python contradictorias

**Cerrado.** Python `3.12+` es el baseline soportado.

### Deriva documental, bytecode y duplicados inequívocos

**Cerrado para el baseline.** README/arquitectura/CLI/roadmap/changelog/versionado se alinearon; se retiraron bytecode versionado y duplicados legacy inequívocos.

## 3. Deuda no bloqueante cerrada después de la estabilización

### Packaging formal y CLI instalable

**Cerrado en 0.16.0.** SQL Studio dispone de `pyproject.toml`, sdist, wheel, entry point `sqlstudio`, versión pública y CI que instala el wheel y ejecuta el comando fuera del checkout.

### Licencia

**Cerrado en 0.16.0.** El repositorio contiene el texto MIT completo y la distribución lo incorpora como metadata/licencia.

### Profiler y benchmark

**Decisión cerrada en 0.17.0.** La auditoría confirmó que los artefactos existentes eran stubs sin medición real, sin integración de paquete, tests ni CI y con schemas duplicados/incompatibles. Se retiraron del baseline y el concepto se difiere a post-MVP bajo `docs/performance-tooling-scope.md`.

## 4. Deuda controlada que permanece abierta

- decidir el destino de `handoff/` frente a `handoffs/`;
- valorar protección de `main` y reglas de branch protection antes de un release formal;
- ampliar casos reales de T-SQL complejo para endurecer el parser;
- definir política de tags/releases y eventual publicación PyPI.

Estos puntos deben resolverse como milestones explícitos y no mezclarse incidentalmente con cambios funcionales no relacionados.

## 5. Gate de salida histórico

Baseline Stabilization quedó cerrado porque la semántica de impacto estaba documentada y probada, HTML y JSON tenían contratos definidos, CI estaba verde, versiones/documentación estaban alineadas y los cambios quedaron integrados mediante PR trazable.

Los milestones posteriores han mantenido el mismo principio: una capacidad o decisión no se considera cerrada sin evidencia automatizada cuando sea aplicable, documentación alineada y estado versionado.

## 6. Punto de reanudación actual

Con packaging y performance-scope resueltos, el siguiente trabajo técnico recomendado es:

**Representative complex T-SQL parser hardening**

Debe introducir fixtures reales/reducidos de construcciones T-SQL complejas, registrar claramente soporte y limitaciones, y añadir regresiones sin cambiar silenciosamente los contratos de objetos/referencias existentes.
