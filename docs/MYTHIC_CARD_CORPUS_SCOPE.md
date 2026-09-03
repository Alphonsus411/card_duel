# Límite actual del corpus de cartas Míticas

## Frontera normativa y de contenido

En `Fantasy Tokens Edicion Mitica.pdf`, la sección normativa termina tras
Desafío. En la página física 4 / interna 3 aparece `EDICION MITICA`, se anuncia
el descriptivo de la colección y comienza el catálogo con la carta nº 001.
Desde esa frontera el documento contiene un **corpus de cartas concretas**, no
evidencia automática de reglas universales. El inventario histórico y su
clasificación D se conservan en `MYTHIC_RULES_AUDIT.md`.

Fase 2-C integró explícitamente el límite auditado de **dos razas, Elfo y
Ángel**, no el corpus entero: la revisión 1 de la colección `mythic` publica
únicamente 023 y 025, cuya semántica completa fue clasificada `SUPPORTED`. Las
once cartas restantes de esas razas siguen bloqueadas como `PARTIAL` o `GAP`;
las demás razas y cartas del PDF también continúan pendientes y fuera del
paquete. El detalle carta por carta, incluida la clasificación y el motivo de
cada exclusión, vive en [`PHASE_2C_MYTHIC_CORPUS.md`](PHASE_2C_MYTHIC_CORPUS.md).

La importación del paquete sólo expone constructores y constantes: no rellena
registros ni catálogos creados por el consumidor. Por ello este límite actual
no permite declarar completas ni Fase 2-C ni Fase 2.

## Contrato para ampliar la integración

Una integración posterior deberá publicar cada colección mediante los
manifiestos de colección ya definidos, con identidad, revisión, versión mínima
del motor, digest y, cuando la política lo exija, firma verificable. La carga
seguirá siendo explícita, validada y atómica: encontrar una carta en el PDF no
autoriza a incorporarla silenciosamente al catálogo de producción.

Las cartas son **datos, no código ejecutable**. Sus costes, tipos, texto y
efectos deberán serializarse en un formato de contenido acotado y convertirse a
los modelos declarativos admitidos. No se aceptarán módulos Python, callbacks,
expresiones evaluadas ni otra ejecución suministrada por una colección.

## Mecánicas antes que cartas

Cada mecánica nueva descubierta al recorrer el corpus deberá, antes de cargar
la primera carta que la use:

1. separarse del texto particular y justificarse como capacidad necesaria;
2. abstraerse como contrato o efecto declarativo general, sin nombres de carta;
3. definir validación, resolución, persistencia, replay y límites de seguridad;
4. probarse aisladamente, incluyendo rechazo, atomicidad y determinismo; y
5. documentar su trazabilidad y compatibilidad.

Sólo después podrá un manifiesto referenciar esa abstracción. Este orden evita
que una carta concreta se convierta en una rama especial del motor o que el
catálogo introduzca comportamiento ejecutable no auditado.
