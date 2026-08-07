# Impact Report

## Objetivo

Definir el contrato funcional del análisis de impacto y la estructura estándar de
sus salidas.

## Semántica de impacto

El grafo de dependencias utiliza la dirección `source -> target`: el objeto
`source` depende del objeto `target`.

Por tanto, analizar el impacto de modificar un objeto raíz significa recorrer
los **dependientes entrantes** mediante `DependencyGraph.dependents_of()`:

- el objeto raíz se incluye siempre en el resultado;
- un objeto impactado directo depende directamente del objeto raíz;
- un objeto impactado indirecto depende de un objeto ya impactado;
- el recorrido es transitivo, determinista y seguro ante ciclos;
- la comparación de nombres es case-insensitive y conserva el casing conocido
  por el grafo.

El recorrido inverso, `dependencies_of()`, responde a una pregunta diferente:
"¿de qué depende este objeto?". Esa capacidad pertenece al Dependency Engine y
no define el análisis de impacto.

## Clasificación

El árbol de impacto conserva la jerarquía real:

- `tree.name` es el objeto raíz;
- `tree.children` contiene los impactos directos;
- los descendientes a partir del segundo nivel son impactos indirectos.

El informe HTML obtiene la clasificación directa/indirecta de este árbol. Un
resultado que no incluya árbol puede seguir renderizándose, pero no inventará
una clasificación directa que no pueda demostrar.

## Contrato JSON 1.0

El contrato JSON `1.0` se mantiene deliberadamente plano por compatibilidad:

```json
{
  "schema_version": "1.0",
  "root_object": "sales.Orders",
  "impacted_objects": [
    "dbo.ActiveOrders",
    "sales.Orders"
  ]
}
```

`tree` no forma parte del schema `1.0`. Incluir la jerarquía en JSON requerirá
una nueva versión de schema; no se modificará silenciosamente el contrato
existente.

## Salida HTML

El informe HTML debe incluir:

- objeto raíz;
- impacto total;
- impactos directos;
- impactos indirectos;
- árbol de impacto navegable.

La salida debe ser autocontenida y escapar nombres de objetos antes de
insertarlos en HTML.
