# Replays 0.20.x anteriores a `AbilitySourceProfile`

Estos registros se generaron ejecutando el motor real del commit padre de
`c0c1ee1` (`8535c0da4027df974d4b88855c3caf1b5b6df037`), versión 0.20.1. No se editaron
los sobres ni sus huellas después de `dump_replay`.

## Reproducción

```bash
git worktree add --detach /tmp/card-duel-pre-profile c0c1ee1^
cd /tmp/card-duel-pre-profile
python /workspace/card_duel/tests/artifacts/0.20.x-pre-source-profile/generate_legacy_replays.py \
  /workspace/card_duel/tests/artifacts/0.20.x-pre-source-profile
sha256sum /workspace/card_duel/tests/artifacts/0.20.x-pre-source-profile/*.replay-v2.json
```

El generador usado se conserva como `generate_legacy_replays.py`. `metadata.json`
registra por archivo el SHA-256, el digest histórico, comandos, eventos, pila y
estado final. Los casos dejan una habilidad en pila: uno conserva la fuente en el
campo de batalla y el otro paga el coste sacrificando esa fuente.
