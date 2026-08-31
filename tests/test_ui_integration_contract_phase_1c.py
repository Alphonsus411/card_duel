"""Contrato de integración de UI de fase 1C sobre la frontera pública.

La función de composición concentra deliberadamente la infraestructura. Después
de recibir su resultado, los tests se comportan como un consumidor remoto: sólo
presentan una identidad, leen DTO públicos y reenvían un ``option_id`` opaco.
"""

import unittest

from card_duel_engine import (
    AuthenticatedMatchApplication,
    Capability,
    CardCatalog,
    CardPresentation,
    CardPresentationCatalog,
    ExternalIdentity,
    InMemoryIdentityAuthorization,
    InMemoryMatchStore,
    MatchService,
    PublicCardCatalog,
    PublicLegalAction,
    PublicMatchView,
    PublicPlayerObservation,
    WriteConflict,
)

from fixtures import test_deck


def compose_ui_contract():
    """Prepara dependencias y datos que una raíz de composición conservaría."""
    mechanical_catalog = CardCatalog()
    presentation_catalog = CardPresentationCatalog()
    decks = {
        "A": test_deck("phase-1c-A"),
        "B": test_deck("phase-1c-B"),
    }
    for definition in (*decks["A"], *decks["B"]):
        mechanical_catalog.register(definition)
        presentation_catalog.register(
            CardPresentation(
                definition.card_id,
                f"presentation-{definition.card_id}",
                definition.name,
                "Carta preparada por la infraestructura del test.",
                f"art/{definition.card_id}.webp",
            )
        )

    authorization = InMemoryIdentityAuthorization()
    application = AuthenticatedMatchApplication(
        MatchService(InMemoryMatchStore(), catalog=mechanical_catalog),
        authorization,
    )
    return (
        application,
        authorization,
        ExternalIdentity("https://identity.example", "phase-1c-user"),
        PublicCardCatalog(mechanical_catalog, presentation_catalog),
        decks,
    )


class UIIntegrationContractPhase1CTests(unittest.TestCase):
    def setUp(self):
        (
            self.application,
            self.authorization,
            self.identity,
            self.card_catalog,
            self.decks,
        ) = compose_ui_contract()
        self.match_id = "ui-contract-phase-1c"

        # Autorización y datos de creación pertenecen a la infraestructura, no
        # son elecciones que la UI reconstruya a partir de una acción legal.
        self.authorization.grant_global(self.identity, Capability.CREATE_MATCH)
        created_version = self.application.create_match(
            self.identity, self.match_id, self.decks, seed=17
        )
        self.authorization.bind_player(self.identity, self.match_id, "A")
        self.assertEqual(created_version, 1)

    def test_consumer_round_trips_only_an_option_id_and_public_dtos(self):
        self.assertIsInstance(self.card_catalog, PublicCardCatalog)
        self.assertTrue(self.card_catalog.cards)

        before = self.application.view(self.identity, self.match_id)
        self.assertIsInstance(before, PublicMatchView)
        self.assertIsInstance(before.observation, PublicPlayerObservation)
        self.assertTrue(before.legal_actions)
        self.assertTrue(
            all(isinstance(option, PublicLegalAction) for option in before.legal_actions)
        )

        # La UI elige una referencia emitida por el servidor: no construye un
        # comando ni deduce sus parámetros y tampoco proporciona player_id.
        option_id = before.legal_actions[0].option_id
        after = self.application.submit_option(
            self.identity,
            self.match_id,
            option_id,
            expected_version=before.version,
        )

        self.assertIsInstance(after, PublicMatchView)
        self.assertEqual(after.match_id, before.match_id)
        self.assertEqual(after.version, before.version + 1)
        # Una lectura nueva desde la misma frontera prueba que el resultado era
        # la proyección del estado autoritativo posterior, no una predicción UI.
        self.assertEqual(after, self.application.view(self.identity, self.match_id))

    def test_stale_expected_version_cannot_overwrite_public_snapshot(self):
        stale_view = self.application.view(self.identity, self.match_id)
        option_id = stale_view.legal_actions[0].option_id

        committed = self.application.submit_option(
            self.identity,
            self.match_id,
            option_id,
            expected_version=stale_view.version,
        )
        self.assertEqual(committed.version, stale_view.version + 1)

        with self.assertRaises(WriteConflict):
            self.application.submit_option(
                self.identity,
                self.match_id,
                option_id,
                expected_version=stale_view.version,
            )

        current = self.application.view(self.identity, self.match_id)
        self.assertIsInstance(current, PublicMatchView)
        self.assertEqual(current.version, committed.version)
        self.assertEqual(current, committed)


if __name__ == "__main__":
    unittest.main()
