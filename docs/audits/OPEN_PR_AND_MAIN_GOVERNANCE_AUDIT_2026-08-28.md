# Auditoría de PR abiertas y gobierno de `main` — 2026-08-28

- **Fecha de consulta UTC:** `2026-08-28T12:30:15Z`.
- **Repositorio consultado:** `Alphonsus411/card_duel`.
- **Modo:** lectura exclusiva mediante la API REST pública de GitHub; la sesión de
  GitHub CLI no estaba autenticada.
- **Auditoría de candidatas A comparada:**
  `docs/audits/CODEX_BRANCH_AUDIT_2026-08-28.md` (157 ramas únicas con
  clasificación `A — SAFE_TO_DELETE`).

## Resultado ejecutivo

| Comprobación | Resultado |
|---|---|
| Total de PR abiertas | **0** |
| Heads de PR abiertas | Ninguno |
| Coincidencias entre candidatas A y heads abiertos | **0** |
| Reclasificaciones `KEEP_OPEN_PR` | **0** |
| Candidatas retiradas de la lista de eliminación | **0** |

La consulta paginada a `GET /repos/Alphonsus411/card_duel/pulls` devolvió `[]`.
Por tanto, no hay filas que enumerar con número, URL, `headRefName` y repositorio
propietario del head, ni coincidencias que reclasificar. Se conserva la lista A
existente sin cambios: ningún tip fue excluido por `KEEP_OPEN_PR` en este corte.

## Procedimiento paso a paso

1. Se comprobó `gh auth status`; la CLI indicó que no había sesión autenticada.
2. Se intentó la consulta con `gh api --paginate`; la CLI local exigió
   autenticación y no produjo datos. Este fallo no se utilizó para inferir ningún
   valor de configuración.
3. Se consultó la API REST pública con `state=open&per_page=100`. La respuesta
   fue HTTP `200`, sin cabecera `Link` y con cuerpo `[]`; el conjunto completo
   contiene cero PR abiertas.
4. Se proyectaron, para cada resultado, los campos `number`, `html_url`,
   `head.ref`, `head.repo.owner.login`, `head.repo.full_name` y `head.sha`. Al ser
   vacío el conjunto, el inventario también quedó vacío.
5. Se extrajeron las 157 candidatas A únicas de la auditoría de ramas y se
   compararon literalmente con todos los `headRefName` abiertos mediante
   conjuntos ordenados. La intersección quedó vacía.
6. Se consultaron por separado el recurso público de la rama `main`, la
   protección detallada, los rulesets del repositorio, las reglas aplicables a
   `main` y la configuración pública del repositorio.

## Inventario de PR abiertas

No hay PR abiertas en el corte. En consecuencia, no existen valores de número,
URL, `headRefName` o repositorio propietario del head que registrar.

## Coincidencias con candidatas A

No hay coincidencias. La regla de precedencia queda documentada para futuras
ejecuciones: toda candidata A cuyo nombre coincida con el `headRefName` de una PR
abierta debe reclasificarse como **`KEEP_OPEN_PR`** y excluirse de cualquier lista
de eliminación, aunque su tip sea ancestro de `origin/main`.

## Gobierno observable de `main`

| Campo solicitado | Resultado observado | Evidencia / límite |
|---|---|---|
| ¿`main` está protegida? | **No** (`protected: false`) | `GET /branches/main` devolvió HTTP `200`, `protection.enabled: false`. |
| Rulesets del repositorio | **Ninguno visible** (`[]`) | `GET /rulesets` devolvió HTTP `200`. |
| Rulesets/reglas aplicables a `main` | **Ninguno visible** (`[]`) | `GET /rules/branches/main` devolvió HTTP `200`. |
| Checks requeridos | **Ninguno en el resumen público de rama** | `required_status_checks.enforcement_level: off`, `contexts: []`, `checks: []`. El recurso detallado no fue accesible. |
| Política de force-push | **NOT OBSERVABLE** | `GET /branches/main/protection` devolvió HTTP `401 Requires authentication`; no se infiere un valor del error. |
| Política de eliminación de la rama protegida | **NOT OBSERVABLE** | El mismo recurso detallado devolvió HTTP `401`; no se infiere un valor del error. |
| `delete_branch_on_merge` / “Automatically delete head branches” | **NOT OBSERVABLE** | El recurso público `GET /repos/Alphonsus411/card_duel` devolvió HTTP `200`, pero omitió el campo; no se interpreta la omisión como `false`. |

La ausencia visible de rulesets se registra únicamente como resultado de los
endpoints públicos consultados. No sustituye por inferencia los campos marcados
**NOT OBSERVABLE**.

## Garantía de sólo lectura

No se invocó ningún método `POST`, `PUT`, `PATCH` o `DELETE` contra GitHub. No se
editaron protecciones, rulesets, configuración del repositorio ni políticas de
merge, y no se eliminó ninguna rama.

