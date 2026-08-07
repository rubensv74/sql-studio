# SQL Studio — Auditoría del estado de desarrollo

**Fecha:** 2026-08-08  
**Repositorio:** `rubensv74/sql-studio`  
**Rama auditada:** `main`  
**Baseline:** `c7cdfafb6bfb9e662290320cfac5d6cffb040c89`

---

## 1. Resumen ejecutivo

SQL Studio dispone ya de un núcleo técnico real y modular para análisis estático de SQL. No es un repositorio vacío ni un simple conjunto de prototipos: existen un Repository Engine, parser SQL, grafo de dependencias, motor de referencias cruzadas, análisis de impacto, serialización JSON, CLI y generación de informes HTML.

Sin embargo, el repositorio **no está todavía en un estado suficientemente controlado para continuar añadiendo funcionalidades sin una estabilización previa**. El código ha avanzado por delante de la documentación y existen al menos dos defectos funcionales relevantes en el análisis de impacto que pueden producir conclusiones incorrectas para el usuario.

**Diagnóstico global:** núcleo de MVP avanzado, pero baseline no consolidado.  
**Decisión recomendada:** ejecutar un sprint de estabilización antes de implementar Circular Dependency Detection o Dead Object Detection.

---

## 2. Estado real del repositorio

### 2.1. Estructura principal

La implementación funcional actual está concentrada principalmente en:

- `src/sqlstudio/repository.py`
- `src/sqlstudio/scanner.py`
- `src/sqlstudio/parser/`
- `src/sqlstudio/dependencies/`
- `src/sqlstudio/cross_reference/`
- `src/sqlstudio/impact_analysis/`
- `cli/sqlstudio.py`
- `tests/`

También existen áreas auxiliares o heredadas:

- `core/`
- `analyzers/`
- `benchmark/`
- `benchmarks/`
- `profiler/`
- `templates/`
- `handoff/`
- `handoffs/`
- `sprints/`

### 2.2. Capacidades implementadas

#### Repository Engine

Existe un motor capaz de recorrer un repositorio y generar un modelo serializable del contenido.

**Estado:** implementado.

#### SQL Parser

El parser dispone de tokenizer, token stream, contexto, AST y parsers especializados. Reconoce, entre otros:

- procedimientos almacenados;
- vistas;
- funciones;
- triggers;
- tablas;
- parámetros;
- variables;
- referencias;
- ejecuciones;
- tablas temporales;
- SQL dinámico.

**Estado:** implementado, aunque su cobertura real sobre T-SQL complejo debe seguir ampliándose mediante casos de prueba reales.

#### Dependency Engine

El grafo distingue:

- nodos;
- dependencias salientes mediante `dependencies_of()`;
- dependientes entrantes mediante `dependents_of()`;
- tipos de relación `REFERENCES` y `EXECUTES`.

El resolver construye relaciones con la dirección:

`objeto que contiene la referencia -> objeto referenciado`

**Estado:** implementado y es actualmente la base conceptual correcta para los motores superiores.

#### Cross Reference Engine

Existe análisis de referencias cruzadas con consultas `incoming()` y `outgoing()`, serialización y soporte CLI.

**Estado:** implementado.

#### Impact Analysis Engine

Existe un motor transitivo, árbol jerárquico, serialización JSON, CLI y reporte HTML.

**Estado:** implementado técnicamente, pero **no debe considerarse funcionalmente cerrado** hasta resolver los defectos P0 descritos en esta auditoría.

#### CLI

`cli/sqlstudio.py` expone actualmente:

- `new-sprint`
- `new-handoff`
- `scan`
- `parse`
- `dependencies`
- `cross-references`
- `impact`

El comando `impact` soporta salida JSON y HTML.

**Estado:** operativo a nivel de código, pendiente de validación automatizada continua.

---

## 3. Hallazgos críticos — P0

### P0.1. La semántica actual de Impact Analysis parece invertida respecto al objetivo de negocio

El `DependencyResolver` crea las relaciones de esta forma:

`source = objeto analizado`  
`target = objeto que source utiliza`

Por tanto:

- `dependencies_of(A)` responde **qué utiliza A**;
- `dependents_of(A)` responde **qué objetos dependen de A**.

Sin embargo, `ImpactAnalysisEngine` recorre actualmente `dependencies_of()`.

Ejemplo conceptual:

`Vista -> Tabla`

Si se pregunta por el impacto de modificar la **Tabla**, lo útil normalmente es conocer qué vistas, procedimientos o funciones dependen de ella. Eso requiere recorrer los **dependientes entrantes**, no las dependencias salientes.

El comportamiento actual responde mejor a:

> “¿De qué depende este objeto?”

que a:

> “¿Qué podría verse afectado si cambio este objeto?”

Además, los tests actuales de CLI codifican esa semántica saliente, por lo que pueden pasar perfectamente y aun así proteger un comportamiento conceptualmente incorrecto.

**Acción obligatoria antes de continuar:** fijar formalmente el contrato del análisis de impacto y, si el objetivo es medir el efecto de un cambio, invertir el recorrido para utilizar `dependents_of()` de forma transitiva. La navegación saliente puede conservarse como una capacidad distinta de trazabilidad de dependencias.

### P0.2. El informe HTML pierde la clasificación de dependencias directas

`ImpactReportGenerator.generate()` acepta `direct_objects`, pero `ImpactReportExporter.export()` invoca al generador sin proporcionar ese conjunto.

Consecuencia probable en el flujo CLI normal:

- `Dependencias directas = 0`;
- los objetos impactados restantes aparecen como indirectos.

Esto contradice el contrato de `docs/impact-report.md`, que exige separar dependencias directas e indirectas.

**Acción obligatoria:** hacer que la clasificación directa/indirecta provenga del propio resultado de análisis —preferentemente de los hijos de primer nivel del árbol— o transportar explícitamente ese dato mediante el modelo. El exportador no debe depender de un parámetro que el flujo normal nunca proporciona.

---

## 4. Hallazgos importantes — P1

### P1.1. El árbol de impacto se pierde en la serialización JSON

`ImpactResult` contiene `tree`, pero `ImpactResultSerializer` versión `1.0` solo serializa:

- `root_object`;
- `impacted_objects`.

La jerarquía calculada por el motor desaparece en la salida JSON.

**Acción recomendada:** decidir si el contrato JSON debe seguir siendo plano. Si el árbol pasa a formar parte del contrato público, crear una nueva versión de esquema en lugar de modificar silenciosamente `1.0`.

### P1.2. Hay un test de contrato que no valida lo que pretende

`tests/test_impact_report_contract.py` utiliza:

`self.assertTrue(Path("docs/impact-report.md"))`

Un objeto `Path` es verdadero independientemente de que el archivo exista, por lo que el test no verifica realmente la presencia del contrato.

**Corrección:** utilizar `Path(...).is_file()` o `Path(...).exists()` y validar además las secciones obligatorias si ese documento forma parte del contrato.

### P1.3. No existe CI en GitHub

No existe `.github/workflows/` y el commit auditado no tiene checks asociados.

Por ello, aunque hay una suite de tests significativa, **el repositorio no demuestra actualmente que el último commit pase las pruebas**.

La auditoría ha identificado 18 módulos de test bajo `tests/`, cubriendo repository, parser, dependencias, cross references e impact analysis.

**Acción recomendada:** añadir GitHub Actions para Python 3.12 y ejecutar al menos:

`python -m unittest discover -s tests -p "test_*.py"`

También debe validarse la importación del paquete y los comandos principales de la CLI.

### P1.4. Contradicción de versiones de Python

`AI_DEVELOPMENT.md` establece Python `3.12+`, mientras que `docs/CLI.md` declara Python `3.10+`.

Además, el repositorio contiene bytecode generado con CPython 3.11.

**Acción recomendada:** fijar una única versión soportada. El criterio más coherente con el marco actual es Python 3.12+.

### P1.5. No existe configuración formal de packaging

No se observa `pyproject.toml`, `setup.py` ni configuración equivalente. La CLI modifica `sys.path` para cargar `src/sqlstudio` directamente desde el checkout.

Esto puede ser válido durante desarrollo, pero limita:

- instalación reproducible;
- comando `sqlstudio` real;
- metadata de versión;
- testing en entornos limpios;
- publicación futura.

**Acción recomendada:** introducir `pyproject.toml` cuando el baseline esté estabilizado y definir un entry point de consola.

---

## 5. Deriva documental y de versión

La documentación no representa el código actual:

- `README.md` sigue indicando `Sprint 007` y “Static SQL Analyzer prototype”.
- `docs/roadmap.md` todavía marca Impact Analysis como pendiente.
- `docs/architecture.md` solo describe Cross Reference Engine.
- `docs/CLI.md` no incluye el comando `impact` en su inventario principal y declara Python 3.10+.
- `CHANGELOG.md` termina en `0.11.0` con Cross Reference Engine.
- `core/version.txt` contiene `0.3.0`.

No existe actualmente una única versión de producto coherente.

**Acción recomendada:** después de corregir los P0, establecer un único versionado y actualizar README, arquitectura, CLI, roadmap y changelog en el mismo sprint de estabilización.

---

## 6. Higiene del repositorio

### 6.1. Bytecode Python versionado

Se han encontrado múltiples directorios `__pycache__` y archivos `.pyc` versionados dentro de `src/` y `tests/`.

`.gitignore` no contiene reglas para excluirlos.

**Acción recomendada:** eliminar los artefactos generados del índice y añadir:

```gitignore
__pycache__/
*.py[cod]
```

### 6.2. Estructuras legacy o duplicadas

Existe, por ejemplo, `core/dependency_models.py`, mientras que el motor real de dependencias está en `src/sqlstudio/dependencies/`.

También hay carpetas antiguas como `handoff/` y `handoffs/` con responsabilidades solapadas.

**Acción recomendada:** inventariar cada elemento legacy y eliminarlo o documentar claramente por qué sigue existiendo. No debe mantenerse una segunda arquitectura paralela por inercia.

### 6.3. Componentes todavía nominales o embrionarios

`profiler/`, `benchmark/` y algunas plantillas existen, pero su nivel de implementación no es comparable al parser o al Dependency Engine.

Por ejemplo, el profiler actual genera una estructura con métricas vacías y el benchmark registra valores proporcionados externamente; no constituyen todavía un motor de profiling o benchmarking automático.

**Conclusión:** no deben contabilizarse como capacidades MVP terminadas.

### 6.4. Licencia incompleta

El archivo `LICENSE` solo contiene el texto `MIT License`, sin el cuerpo completo de la licencia MIT. GitHub no puede identificarla como una licencia MIT estándar.

**Prioridad:** baja para el desarrollo funcional, pero debe corregirse antes de una publicación formal.

---

## 7. Gobierno de desarrollo

### Situación actual

- Solo existe la rama `main`.
- `main` no está protegida.
- No hay PRs abiertos o históricos detectables desde el repositorio actual.
- No hay issues activos.
- No hay CI.
- Muchos commits recientes utilizan mensajes genéricos como `add`, `Add` o `fix files`.

Esto contradice `AI_DEVELOPMENT.md`, que exige Conventional Commits y validaciones antes de cerrar cada sprint.

### Recomendación

A partir de esta auditoría:

1. GitHub será la fuente de verdad del desarrollo.
2. Cada avance debe quedar persistido en el repositorio.
3. Cada cambio funcional debe incluir tests.
4. Cada cierre debe dejar una evidencia reproducible de validación.
5. Los commits deben usar Conventional Commits.
6. No se debe considerar un sprint terminado únicamente porque el código exista.

---

## 8. Numeración de sprints

El repositorio permite identificar explícitamente commits llamados `Add sprint 12` y `Add sprint 13`.

Después de Sprint 13 existen ocho commits adicionales hasta el baseline actual, pero sus mensajes (`add`, `Add`, `fix files`) no permiten reconstruir de forma fiable a qué sprint pertenecía cada uno.

**Conclusión:** la numeración histórica posterior a Sprint 13 no puede recuperarse con suficiente rigor únicamente desde Git. No conviene inventarla.

Hasta consolidar este baseline, el siguiente trabajo debe denominarse por objetivo —por ejemplo, **Baseline Stabilization**— y solo después fijar la secuencia de sprints funcionales restantes.

---

## 9. Plan recomendado para retomar el desarrollo

### Fase inmediata — Baseline Stabilization

#### Gate 1 — Semántica de impacto

- Formalizar qué significa “impacto”.
- Corregir el recorrido del grafo si debe responder qué objetos dependen del objeto modificado.
- Separar, si procede, “dependency trace” de “impact analysis”.
- Añadir casos de prueba bidireccionales que demuestren la diferencia.

#### Gate 2 — Contrato del informe

- Corregir clasificación directa/indirecta.
- Validar árbol jerárquico.
- Decidir contrato JSON del árbol y versionarlo si cambia.
- Reparar tests débiles.

#### Gate 3 — Validación reproducible

- Añadir GitHub Actions.
- Ejecutar suite completa en Python 3.12.
- Validar CLI.
- Validar imports desde entorno limpio.

#### Gate 4 — Higiene técnica

- Eliminar `__pycache__` y `.pyc` versionados.
- Actualizar `.gitignore`.
- Identificar y retirar duplicados legacy inequívocos.

#### Gate 5 — Fuente de verdad documental

Actualizar de forma coordinada:

- `README.md`
- `docs/architecture.md`
- `docs/CLI.md`
- `docs/roadmap.md`
- `CHANGELOG.md`
- versión del proyecto

### Definition of Done de Baseline Stabilization

El baseline se considerará cerrado solo cuando:

- la semántica de Impact Analysis esté documentada y probada;
- el informe HTML clasifique correctamente directos e indirectos;
- todos los tests pasen en CI;
- no haya bytecode versionado;
- documentación y código describan la misma versión del producto;
- el commit final utilice Conventional Commits;
- `main` esté en un estado reproducible y verificable.

---

## 10. Roadmap posterior recomendado

Una vez estabilizado el baseline, el orden lógico del roadmap actual es:

1. **Circular Dependency Detection**
2. **Dead Object Detection**
3. Consolidación del motor de reglas/análisis estático
4. Revisión del alcance real de profiler y benchmark
5. Packaging y distribución del CLI, si sigue siendo parte del objetivo del MVP

No se recomienda comenzar Circular Dependency Detection antes de cerrar los P0, porque ese motor dependerá de la misma semántica del grafo que actualmente debe corregirse o formalizarse.

---

## 11. Veredicto

SQL Studio está en mejor estado de lo que su README sugiere, pero en peor estado de control de lo que la cantidad de módulos podría hacer pensar.

La arquitectura central tiene una base válida y reutilizable. El problema inmediato no es falta de funcionalidad: es **falta de consolidación del contrato funcional, trazabilidad del estado y validación continua**.

El siguiente paso correcto no es añadir otra capacidad. Es cerrar el baseline existente y convertirlo en una plataforma fiable para los siguientes motores de análisis.
