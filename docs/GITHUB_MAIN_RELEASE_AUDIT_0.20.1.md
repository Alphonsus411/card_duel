# Auditoría de gobierno de `main` y publicación 0.20.1

Fecha de consulta: **2026-08-27 UTC**. Repositorio consultado:
`Alphonsus411/card_duel`. Esta auditoría separa deliberadamente lo observado,
lo que la sesión anónima no pudo consultar y las recomendaciones. No se cambió
ninguna configuración remota, no se creó `v0.20.1` y no se publicó en PyPI.

## Método y límites

`gh auth status` indicó que no había sesión iniciada y el clon no tenía remoto
configurado. La identidad del repositorio se contrastó con los merges del
historial local y luego se consultó exclusivamente en modo lectura mediante la
API REST pública de GitHub, con `Accept: application/vnd.github+json` y
`X-GitHub-Api-Version: 2022-11-28`:

```text
GET /repos/Alphonsus411/card_duel
GET /repos/Alphonsus411/card_duel/branches/main
GET /repos/Alphonsus411/card_duel/branches/main/protection
GET /repos/Alphonsus411/card_duel/rulesets
GET /repos/Alphonsus411/card_duel/rules/branches/main
GET /repos/Alphonsus411/card_duel/releases?per_page=100
GET /repos/Alphonsus411/card_duel/tags?per_page=100
GET /repos/Alphonsus411/card_duel/actions/workflows
GET /repos/Alphonsus411/card_duel/actions/workflows/318753635/runs?branch=main&per_page=20
GET /repos/Alphonsus411/card_duel/commits/main/check-runs?per_page=100
GET /repos/Alphonsus411/card_duel/commits/main/status
```

No se recibió ningún **404**. La consulta detallada de protección clásica fue
la única respuesta no satisfactoria: **401 `Requires authentication`**. Por ello
no se interpreta esa respuesta como una opción desactivada. Los demás endpoints
enumerados devolvieron **200**.

## Estado observado en GitHub

### Gobierno de `main`

* El repositorio es público, `main` es la rama predeterminada y
  `GET /branches/main` devolvió `protected: false`, `protection.enabled: false`,
  nivel de checks `off` y listas `contexts`/`checks` vacías.
* `GET /rulesets` devolvió `[]` y `GET /rules/branches/main` devolvió `[]`:
  no hay rulesets del repositorio ni reglas de ruleset aplicables a `main` que
  la API pública muestre.
* En consecuencia observable, actualmente no se exige pull request ni checks
  mediante reglas aplicables. Tampoco existe en esas reglas una exigencia de
  rama actualizada, un bloqueo de force-push, un bloqueo de eliminación o un
  actor de bypass configurado. Esto describe la ausencia de reglas devuelta por
  los endpoints 200; no pretende rellenar los campos del endpoint clásico 401.
* El objeto público del repositorio **no incluyó** el campo
  `delete_branch_on_merge`. Su valor queda **no consultable con los permisos de
  esta sesión**: no se infiere `false` de la ausencia del campo.

### CI existente

El workflow activo del repositorio se llama `tests`. En el commit de `main`
`a868df157493697b174106a4054a85a118c35a0f`, GitHub registró cuatro check runs,
todos completados con `success`:

* `runtime (3.11)`;
* `runtime (3.12)`;
* `runtime (3.13)`;
* `full`.

Los 20 runs más recientes consultados del workflow `tests` sobre `main` también
terminaron en `success`. Existe además el workflow dinámico `Dependency Graph`,
pero no aparece como check run del commit examinado y no debe inventarse como
requisito. El estado combinado tradicional no contenía contextos (`statuses:
[]`); los nombres anteriores proceden de Checks API.

### Tags, releases y evidencia publicada

* `GET /releases?per_page=100` devolvió `[]`: no existe ninguna GitHub Release.
* `GET /tags?per_page=100` devolvió `[]`: no existe ningún tag remoto.
* Por tanto, en GitHub no hay release, tag `v0.20.1` ni artefacto asociado que
  constituya evidencia publicada de 0.20.1. La evidencia versionada dentro de
  `main` es evidencia candidata conservada en el repositorio, no una publicación
  de GitHub Releases.

## Coherencia local de la candidata 0.20.1

La comparación local dio este resultado:

| Fuente | Resultado |
| --- | --- |
| `pyproject.toml` | `version = "0.20.1"` |
| `CHANGELOG.md` | primera sección de versión: `0.20.1` |
| wheel reconstruido | `card_duel_engine-0.20.1-py3-none-any.whl` |
| `*.dist-info/METADATA` del wheel | nombre `card-duel-engine`, versión `0.20.1`, Python `>=3.11` |
| verificación nueva | versión `0.20.1`, perfil `full`, estado `ok`; instalación probada en 3.11, 3.12 y 3.13 |
| cuatro JSON versionados | versión `0.20.1` y estado `ok` (runtime 3.11/3.12/3.13 y full 3.13) |

Se ejecutó:

```text
uv sync --locked --extra dev
uv run python scripts/verify_release.py --profile full --json dist/release-verification.json
```

La primera ejecución directa de `verify_release.py` falló correctamente antes
de validar porque el entorno aún no contenía `mypy`; después de sincronizar el
extra `dev`, la ejecución completa terminó con código 0. El JSON transitorio
acredita todas las etapas (`metadata`, `lockfile`, `security`, `quality`, fuentes
de reglas, simulaciones, persistencia y paquete), con cobertura 89 %, 2 fuentes
verificadas y wheel instalable en las tres versiones de Python.

El SHA-256 del wheel reconstruido desde el `main` actual es
`02896b0e3a7f1a02ee0673c8d4dbe1dc177add5b61077dd4fd97d20515b8611f`; el JSON
versionado de la verificación full conserva
`4239907c2b5744c605d57410b05ba0c62e00f5b137727f62ebdd65f4d26a8d62`.
Esta diferencia no es una contradicción de versión: el repositorio ha recibido
cambios después de generarse la evidencia conservada y un wheel puro incorpora
esos archivos. La auditoría de reproducibilidad compara dos construcciones del
mismo árbol; la verificación nueva la superó. Para publicar, debe conservarse el
hash producido por el commit/tag definitivo, sin reutilizar el hash histórico.

**Conclusión:** los metadatos locales son coherentes como candidata 0.20.1 y la
verificación actual pasa, pero 0.20.1 **no está publicada en GitHub** porque no
hay tag ni release. Esta auditoría no consultó PyPI ni afirma nada sobre su
estado allí.

## Recomendación futura y pragmática

Para un repositorio de una sola persona, configurar un ruleset dirigido a
`main`, sin tocar la configuración durante esta auditoría:

1. Exigir pull request antes del merge. Mantener el mínimo operativo de cero
   aprobaciones obligatorias si no hay segundo revisor, pero impedir pushes
   directos ordinarios.
2. Exigir **exactamente** `runtime (3.11)`, `runtime (3.12)`, `runtime (3.13)` y
   `full`, que son los cuatro checks existentes, estables en la muestra y
   ejecutados tanto en `push` como en `pull_request`. No exigir `tests` ni
   `Dependency Graph`, porque no son nombres de check runs observados.
3. Bloquear force-push y bloquear la eliminación de `main`.
4. Activar la exigencia de rama actualizada con `main` si el volumen de cambios
   hace tolerable reejecutar la matriz completa; en caso de fricción excesiva,
   conservar los checks obligatorios y reevaluar esta opción por separado.
5. Evitar bypass permanente. Si se necesita recuperación, limitar el bypass al
   propietario/administrador, usarlo sólo para incidentes y documentar después
   el motivo y el commit de reparación.
6. Si al revisarlo con permisos administrativos
   `delete_branch_on_merge` está desactivado, activar **Automatically delete head
   branches**. GitHub no elimina la rama predeterminada, pero conviene además
   identificar ramas especiales de larga vida y no usarlas como ramas head de
   PR. Antes del merge, taggear o copiar cualquier rama que deba conservarse;
   para recuperación, conservar el SHA/PR y restaurar con `git branch <nombre>
   <sha>` seguido de un push normal autorizado.

Antes de aplicar nada, repetir las consultas autenticado como administrador,
especialmente `/branches/main/protection` y el campo
`delete_branch_on_merge`. Esa segunda observación debe sustituir los estados
marcados aquí como no consultables, no asumirse de antemano.
