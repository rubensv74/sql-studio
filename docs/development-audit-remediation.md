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

Los hallazgos que bloqueaban continuar el roadmap han sido remediados. El baseline `0.12.0` puede considerarse **estabilizado y reproducible**.

## 2. Hallazgos cerrados

### P0.1 — Semántica de Impact Analysis

**Cerrado.**

El contrato del grafo queda formalizado como `source -> target`, donde `source` depende de `target`.

Impact Analysis recorre ahora `DependencyGraph.dependents_of()` de forma transitiva para responder qué objetos pueden verse afectados si cambia el objeto raíz. La navegación `dependencies_of()` se conserva para responder de qué depende un objeto.

Se añadieron pruebas específicas para distinguir ambas direcciones, preservar casing, manejar objetos desconocidos y evitar ciclos infinitos.

### P0.2 — Clasificación directa/indirecta del informe HTML

**Cerrado.**

El informe obtiene los impactos directos de los hijos de primer nivel del árbol de impacto y clasifica como indirectos los niveles posteriores.

El flujo normal de exportación ya no depende de un parámetro externo que no se proporcionaba.

### P1.1 — Árbol y contrato JSON

**Decisión cerrada.**

El schema JSON `1.0` permanece deliberadamente plano por compatibilidad. El árbol es un contrato en memoria y HTML. Incorporarlo al JSON requerirá una nueva versión de schema.

### P1.2 — Test de contrato débil

**Cerrado.**

El test verifica ahora la existencia real de `docs/impact-report.md` y las secciones obligatorias del contrato.

### P1.3 — Ausencia de CI

**Cerrado.**

Existe `.github/workflows/ci.yml` sobre Python 3.12. La validación ejecuta:

- compilación de fuentes;
- imports del paquete;
- suite completa de tests;
- smoke tests de la CLI.

La CI fue verde en el head del PR #1 y volvió a ser verde sobre `main` después del merge.

### P1.4 — Versiones de Python contradictorias

**Cerrado.**

La documentación y CI fijan Python `3.12+` como baseline soportado.

### Deriva documental y de versión

**Cerrada para el baseline actual.**

README, arquitectura, CLI, roadmap, changelog y `core/version.txt` describen ahora la versión `0.12.0` y las capacidades efectivamente implementadas.

### Bytecode y artefactos generados

**Cerrado.**

Se retiraron los `__pycache__`/`.pyc` versionados y `.gitignore` evita su reintroducción.

### Duplicados legacy inequívocos

**Parcialmente cerrado.**

Se eliminaron `core/dependency_models.py` y `core/sqlstudio.json`, que duplicaban o contradecían la implementación/versionado canónicos.

No se eliminaron otras áreas históricas sin demostrar previamente que sean prescindibles.

## 3. Hallazgos no bloqueantes que permanecen abiertos

Los siguientes puntos no bloquean el próximo motor funcional, pero siguen formando parte de la deuda controlada:

- introducir packaging formal (`pyproject.toml`) y entry point instalable;
- completar la licencia antes de una publicación formal;
- decidir el destino de `handoff/` frente a `handoffs/`;
- revisar si `profiler/` y `benchmark/` pertenecen realmente al MVP;
- valorar protección de `main` y reglas de branch protection;
- ampliar casos reales de T-SQL complejo para endurecer el parser.

Estos puntos deben resolverse por prioridad explícita y no mezclarse incidentalmente con el siguiente sprint funcional.

## 4. Gate de salida

Baseline Stabilization queda cerrado porque:

- la semántica de impacto está documentada y probada;
- el HTML clasifica correctamente impacto directo e indirecto;
- el contrato JSON mantiene compatibilidad explícita;
- la suite completa pasa en CI;
- imports y CLI pasan en CI;
- no se versiona bytecode Python;
- documentación y código comparten versión y estado;
- los cambios quedaron integrados mediante PR y commits trazables.

## 5. Punto de reanudación

El siguiente milestone funcional autorizado por el roadmap es:

**Circular Dependency Detection**

Debe construirse reutilizando `DependencyGraph`, sin redefinir la dirección de las aristas y con cobertura específica para ciclos simples, ciclos multisalto, componentes desconectados, duplicados y casing.
