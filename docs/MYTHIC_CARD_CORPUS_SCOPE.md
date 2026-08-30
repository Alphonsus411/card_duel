# Alcance del futuro corpus de cartas Míticas

## Frontera normativa y de contenido

En `Fantasy Tokens Edicion Mitica.pdf`, la sección normativa termina tras
Desafío. En la página física 4 / interna 3 aparece `EDICION MITICA`, se anuncia
el descriptivo de la colección y comienza el catálogo con la carta nº 001.
Desde esa frontera el documento contiene un **corpus de cartas concretas**, no
evidencia automática de reglas universales. El inventario histórico y su
clasificación D se conservan en `MYTHIC_RULES_AUDIT.md`.

Esta entrega **no importa ninguna carta Mítica** y las cartas Míticas **no
pertenecen actualmente al paquete** `card_duel_engine`. El código de producción
ofrece modelos, motor y registro; no debe incluir instancias, listas o
definiciones concretas del catálogo del PDF.

## Contrato de una integración futura

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
