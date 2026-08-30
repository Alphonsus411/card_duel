# Optimización del contexto local de targeting 0.20.1

## Alcance

La única optimización aceptada en esta iteración es reutilizar consultas puras
durante una llamada pública a `GameEngine.legal_actions`. El cambio alcanza la
resolución de definiciones, palabras clave efectivas y efectos continuos que la
enumeración repite para una misma instancia. No cambia reglas, comandos, orden,
límites, perfiles semánticos ni API pública, y no abre una segunda candidata.

Quedan expresamente fuera snapshots, replay, persistencia, `GameState`,
`PhaseManager`, algoritmos combinatorios, `deepcopy`, fuentes PDF y metadatos de
versión. Tampoco se cachean resultados entre llamadas ni durante una mutación.

## Diseño

`LegalActionEnumerator.legal_actions` crea un `_LegalActionQueryContext` privado.
El contexto contiene tres mapas indexados por `card_id`: definiciones efectivas,
palabras clave efectivas y tuplas materializadas de efectos continuos. Se pasa
explícitamente sólo por las rutas de jugadas, habilidades y allocations usadas
por esa enumeración. Los métodos conservan `None` como valor predeterminado, de
modo que sus llamadores ajenos a `legal_actions` mantienen la ejecución anterior.

La materialización de efectos continuos usa una tupla y devuelve un iterador
nuevo en cada lectura. Así evita cachear un generador consumible y conserva el
orden de recorrido del estado. Las claves no intentan modelar invalidación: la
ausencia de mutaciones dentro de la consulta y la vida local hacen innecesario
un protocolo global de invalidación.

## Vida útil del contexto

El contexto nace dentro de cada invocación de `legal_actions`, después de entrar
en el enumerador, y queda inaccesible cuando la invocación retorna o propaga una
excepción. No se guarda en el motor ni en el estado, no es serializable y no se
comparte con una llamada posterior. Por ello, cualquier comando o mutación entre
dos consultas obtiene siempre un contexto nuevo y observa el estado actualizado.

## Invariantes de aceptación

1. El tipo, contenido, orden, cantidad y fingerprint de los comandos coinciden
   exactamente con el baseline en `CURRENT` y `LEGACY_019`.
2. El estado canónico anterior y posterior a la consulta es idéntico.
3. Retornos tempranos y excepciones no filtran el contexto a otra invocación.
4. Una mutación posterior se refleja en la siguiente enumeración.
5. Se conservan errores, truncamiento y perfiles semánticos.
6. El diff productivo no toca los subsistemas y artefactos excluidos ni cambia
   la versión `0.20.1`.

Una divergencia en cualquiera de estos observables obliga a retirar el cambio
productivo y documentar **NO-GO**.

## Riesgos y mitigaciones

- **Dato obsoleto tras mutación:** se evita al no compartir el contexto fuera de
  una única consulta, que es de solo lectura.
- **Clave incompleta:** sólo se cachean valores cuya dependencia es estable en
  esa ventana; la elegibilidad final conserva los parámetros de fuente y habilidad.
- **Cambio de orden:** los efectos se materializan en el mismo orden y cada
  consumidor recibe un iterador fresco.
- **Fuga accidental a estado/API:** la clase es privada, no pertenece a
  `GameState` y se transmite como argumento interno opcional.
- **Paridad parcial:** pruebas parametrizadas cubren ambos perfiles, distintos
  estados de targeting, excepciones y comportamiento después de mutar.
- **Memoria:** los mapas viven una llamada; el benchmark mide explícitamente su
  pico adicional y permite contrastarlo con el ahorro temporal.

## Razón de la decisión final

La decisión es **GO**: la ruta pública STRESS reduce la mediana de 26,848 ms a
8,205 ms (-69,44 %) y MEDIUM de 13,547 ms a 7,755 ms (-42,75 %), con igualdad
de fingerprints, orden y estado en todas las muestras. El coste máximo observado
es 11.024 bytes adicionales de pico en STRESS. La mejora procede de reducir el
trabajo interno repetido, no de cambiar el conjunto de acciones. La validación
integral y la verificación de fuentes normativas quedan registradas en los dos
documentos de evidencia. Tras esta decisión se detiene el trabajo de rendimiento:
no se inicia otra optimización candidata.
