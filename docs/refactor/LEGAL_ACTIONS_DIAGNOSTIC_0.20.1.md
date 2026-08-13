# Diagnóstico previo: enumeración de acciones legales — 0.20.1

> **Tipo de documento:** informe previo a la implementación. Este diagnóstico
> describe el punto de partida que se tomó para la extracción; no presenta como
> evidencia posterior ningún resultado de `docs/release-results/`.

## 1. Identificación

- Componente: `GameEngine.legal_actions`.
- Versión objetivo: `0.20.1`.
- Base propuesta: `952b1759371eb9c591c7601d906547de4f508449`.
- Objetivo: separar enumeración de coordinación sin cambiar reglas observables.

## 2. Validez de la base

Al comenzar la documentación final, `git merge-base --is-ancestor
952b1759371eb9c591c7601d906547de4f508449 HEAD` terminó con código **0**. La
base propuesta sigue siendo un ancestro real y, por ello, es la base de la
comparación. No se sustituyó por un SHA conveniente ni por evidencia histórica.

## 3. Estado previo

En la base, `GameEngine` era a la vez fachada, coordinador y propietario del
algoritmo completo de `legal_actions`. El método recorría estado, decisiones,
pila, prioridad, combate, mano y permanentes, y construía directamente la tupla.

## 4. Problema de diseño

La enumeración estaba acoplada al objeto coordinador completo. Eso hacía difícil
reconocer qué datos eran consultas, qué helpers continuaban siendo reglas del
motor y cuál era la frontera que podía extraerse sin convertir la enumeración en
un segundo motor.

## 5. Responsabilidad que se extrae

Se extrae únicamente la **construcción ordenada y acotada** de comandos legales.
No se extraen ejecución, validación de comandos, mutación, resolución, costes ni
selección válida de objetivos.

## 6. Invariantes observables

La salida debe conservar tipo `tuple`, orden, duplicados si existieran, límites,
excepciones, comportamiento antes de iniciar la partida y ausencia de mutaciones.
Dos llamadas con el mismo estado deben producir el mismo valor.

## 7. Ramas funcionales inventariadas

Se inventariaron: decisiones pendientes, objetivos disparados, selección de
reemplazos, prioridad, jugadas, activaciones, combate, equipamiento, descarte por
límite de mano, concesión y partidas no activas.

## 8. Datos consultados

La enumeración necesita la instancia autoritativa de `GameState`, el límite de
enumeración, el límite de mano, definiciones de cartas, sustituciones, semántica
legacy y el enumerador de combate.

## 9. Colaboraciones necesarias

Los cálculos compartidos de objetivos disparados, jugadas, activaciones y la
pregunta de tipo criatura permanecen como consultas del contexto. La extracción
no debe acceder a capas de servicio, aplicación, controladores ni simulación.

## 10. Riesgos

Los principales riesgos son reordenar comandos, truncar en un punto distinto,
leer una copia obsoleta del estado, mutar accidentalmente el motor, ampliar la
API pública o divergir en los perfiles `RuleSet` pequeños y legacy 0.19.

## 11. Frontera propuesta

Se propone `LegalActionContext` como protocolo estructural mínimo y
`LegalActionEnumerator` como colaborador interno. `GameEngine` implementará el
protocolo mediante propiedades/consultas privadas y conservará `legal_actions`
como fachada pública.

## 12. Estrategia de compatibilidad

La primera prueba compara literalmente el algoritmo anterior capturado con el
enumerador directo y la fachada. Después se añaden escenarios característicos
para límites pequeños, privacidad, servicios y dependencias de capa.

## 13. Criterios de aceptación previos

Se exige paridad exacta de valores y excepciones, identidad del estado
consultado, cero mutaciones, tipado correcto, ninguna dependencia hacia capas
externas y suite completa verde. Un fallo se registra; no se reemplaza por un
resultado almacenado de release.

## 14. Decisión previa

Proceder con una extracción mecánica y luego estrechar la frontera. Los helpers
de costes/objetivos quedan expresamente fuera. La delegación deseada es
`GameEngine -> LegalActionEnumerator -> consultas del contexto`; no se autoriza
una reescritura de reglas.
