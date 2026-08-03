# Procedimiento de rollback de una publicación

Este procedimiento retira una distribución defectuosa sin reescribir Git, sin
reutilizar su número de versión y sin modificar snapshots o replays persistidos.
Un rollback de artefactos **no** es una migración de datos ni autoriza cambios
normativos.

## Condiciones previas

1. Identificar el SHA, tag, workflow, wheel y los tres informes publicados.
2. Descargar juntos el wheel, `SHA256SUMS`, `wheel-audit.json` y
   `release-verification.json`; conservarlos como evidencia inmutable.
3. Verificar `SHA256SUMS` y confirmar que ambos JSON identifican el mismo wheel.
4. Nombrar una persona responsable de ejecutar y otra de revisar el rollback.

## Ensayo local no destructivo

El ensayo se hace sobre una copia descargada, nunca sobre `dist/` ni sobre el
registro remoto:

```bash
mkdir -p /tmp/card-duel-rollback-evidence
cp card_duel_engine-0.20.1-py3-none-any.whl SHA256SUMS \
  wheel-audit.json release-verification.json /tmp/card-duel-rollback-evidence/
(cd /tmp/card-duel-rollback-evidence && sha256sum --check SHA256SUMS)
python -m json.tool /tmp/card-duel-rollback-evidence/wheel-audit.json >/dev/null
python -m json.tool /tmp/card-duel-rollback-evidence/release-verification.json >/dev/null
```

El revisor debe registrar el resultado y comprobar que el checkout continúa
limpio. Este ensayo valida la evidencia, pero no simula ni afirma una retirada
del índice remoto.

## Ejecución remota

1. Suspender el job o credencial de publicación para impedir una nueva subida.
2. Marcar la versión afectada como retirada mediante la función de *yank* del
   índice. No borrar ni sustituir archivos con el mismo nombre.
3. Publicar un aviso que identifique versión, SHA, motivo, alcance y alternativa
   recomendada, sin divulgar datos sensibles.
4. Crear la corrección desde un commit posterior y asignarle una versión nueva;
   ejecutar el checklist completo y obtener aprobación independiente.
5. Reactivar la publicación únicamente después de comprobar el artefacto nuevo.

## Criterios de cierre

- La versión afectada permanece trazable y no puede confundirse con la corregida.
- Git, tags firmados y evidencia descargada no se reescribieron.
- Ningún replay, snapshot, manifiesto o contrato persistido fue alterado.
- La incidencia enlaza la ejecución del rollback, la corrección y su validación.
