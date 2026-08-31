"""Contrato de integración de UI de fase 1C sobre la frontera pública.

La función de composición concentra deliberadamente la infraestructura. Después
de recibir su resultado, los tests se comportan como un consumidor remoto: sólo
presentan una identidad, leen DTO públicos y reenvían un ``option_id`` opaco.
"""

import ast
import inspect
from pathlib import Path
import tomllib
from typing import get_type_hints
import unittest

import card_duel_engine.application as application_module
import card_duel_engine.public_catalog as public_catalog_module

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
    OptionRejected,
    PublicCardCatalog,
    PublicLegalAction,
    PublicMatchView,
    PublicPlayerObservation,
    WriteConflict,
)

from fixtures import test_deck


ROOT = Path(__file__).resolve().parents[1]


def tamper_option_id(option_id: str) -> str:
    """Altera siempre el MAC opaco sin asumir nada sobre su contenido."""
    replacement = "0" if option_id[-1] != "0" else "1"
    return f"{option_id[:-1]}{replacement}"


def nested_keys(value):
    """Recorre las claves de un payload JSON sin acoplarse a su forma."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


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
    def test_phase_1c_boundary_is_in_process_and_adds_no_transport_dependencies(self):
        """Acota la fase a tipos Python, sin adoptar ningún transporte."""
        forbidden_imports = {
            "expo",
            "fastapi",
            "httpx",
            "jwt",
            "orjson",
            "requests",
            "simplejson",
            "typescript",
            "ujson",
            "websocket",
            "websockets",
        }
        forbidden_annotation_terms = forbidden_imports | {
            "http",
            "reactnative",
            "request",
            "response",
            "rest",
            "statuscode",
        }

        for module in (application_module, public_catalog_module):
            path = Path(inspect.getsourcefile(module) or "")
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported_roots = set()
            public_annotations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(
                        alias.name.split(".", 1)[0].lower() for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    imported_roots.add((node.module or "").split(".", 1)[0].lower())
                elif (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not node.name.startswith("_")
                ):
                    public_annotations.extend(
                        annotation
                        for annotation in (
                            node.returns,
                            *(argument.annotation for argument in node.args.posonlyargs),
                            *(argument.annotation for argument in node.args.args),
                            *(argument.annotation for argument in node.args.kwonlyargs),
                        )
                        if annotation is not None
                    )
                elif (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and not node.target.id.startswith("_")
                ):
                    public_annotations.append(node.annotation)
            with self.subTest(module=module.__name__):
                self.assertTrue(forbidden_imports.isdisjoint(imported_roots))
                for annotation in public_annotations:
                    annotation_names = {
                        name.id.lower().replace("_", "")
                        for name in ast.walk(annotation)
                        if isinstance(name, ast.Name)
                    } | {
                        name.attr.lower().replace("_", "")
                        for name in ast.walk(annotation)
                        if isinstance(name, ast.Attribute)
                    }
                    self.assertFalse(
                        forbidden_annotation_terms & annotation_names,
                        ast.unparse(annotation),
                    )

        view_signature = inspect.signature(AuthenticatedMatchApplication.view)
        view_hints = get_type_hints(AuthenticatedMatchApplication.view)
        self.assertEqual(tuple(view_signature.parameters), ("self", "identity", "match_id"))
        self.assertEqual(view_hints["identity"], ExternalIdentity | None)
        self.assertIs(view_hints["match_id"], str)
        self.assertIs(view_hints["return"], PublicMatchView)

        submit_signature = inspect.signature(
            AuthenticatedMatchApplication.submit_option
        )
        submit_hints = get_type_hints(AuthenticatedMatchApplication.submit_option)
        self.assertEqual(
            tuple(submit_signature.parameters),
            ("self", "identity", "match_id", "option_id", "expected_version"),
        )
        self.assertEqual(submit_hints["identity"], ExternalIdentity | None)
        self.assertIs(submit_hints["match_id"], str)
        self.assertIs(submit_hints["option_id"], str)
        self.assertIs(submit_hints["expected_version"], int)
        self.assertIs(submit_hints["return"], PublicMatchView)
        self.assertIs(
            submit_signature.parameters["expected_version"].kind,
            inspect.Parameter.KEYWORD_ONLY,
        )

        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertEqual(project["dependencies"], [])

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

    def test_public_boundary_hides_private_state_and_rejects_all_invalid_options_equally(self):
        """Prueba el contrato completo como lo consumiría una UI no confiable."""
        # La segunda partida conserva exactamente el mazo propio, pero cambia
        # las identidades y además invierte el orden de entrada del mazo rival.
        # Son diferencias privadas que no deben poder distinguirse al observar A.
        equivalent_match_id = "ui-contract-phase-1c-equivalent"
        rival_variant_in_deck_order = test_deck("private-rival-variant")
        rival_variant = list(reversed(rival_variant_in_deck_order))
        self.assertTrue(
            {card.card_id for card in self.decks["B"]}.isdisjoint(
                card.card_id for card in rival_variant
            )
        )
        self.assertEqual(
            [card.card_id for card in rival_variant],
            [card.card_id for card in reversed(rival_variant_in_deck_order)],
        )
        equivalent_decks = {"A": self.decks["A"], "B": rival_variant}
        self.application.create_match(
            self.identity, equivalent_match_id, equivalent_decks, seed=17
        )
        self.authorization.bind_player(self.identity, equivalent_match_id, "A")

        original = self.application.view(self.identity, self.match_id)
        equivalent = self.application.view(self.identity, equivalent_match_id)
        self.assertEqual(original.observation, equivalent.observation)
        self.assertEqual(
            [option.action for option in original.legal_actions],
            [option.action for option in equivalent.legal_actions],
        )

        for public_view in (original, equivalent):
            payload = public_view.to_dict()
            observation = payload["observation"]
            self.assertEqual(
                set(observation),
                {
                    "player_id",
                    "active_player_id",
                    "phase",
                    "own_hand",
                    "own_steps",
                    "own_wounds",
                    "opponent_hand_sizes",
                    "public_event_count",
                    "own_battlefield",
                    "opponent_battlefields",
                    "stack_size",
                },
            )
            self.assertEqual(
                observation["opponent_hand_sizes"],
                original.observation.opponent_hand_sizes,
            )
            self.assertGreater(observation["opponent_hand_sizes"]["B"], 0)
            self.assertTrue(
                all(
                    set(option) == {"option_id", "action"}
                    for option in payload["legal_actions"]
                )
            )
            keys = set(nested_keys(payload))
            self.assertTrue({"cards", "catalog"}.isdisjoint(keys))
            self.assertTrue(
                {
                    "command",
                    "commands",
                    "candidate",
                    "candidates",
                    "opponent_hand",
                    "opponent_deck",
                    "deck_order",
                    "rules_text",
                    "art",
                    "token",
                    "mechanical_name",
                }.isdisjoint(keys)
            )

        # Este catálogo se compone aparte: describe referencias de cartas y no
        # recibe partida, identidad, instantánea ni zonas durante su creación.
        reference_mechanics = CardCatalog()
        reference_presentations = CardPresentationCatalog()
        for definition in test_deck("public-reference", size=2):
            reference_mechanics.register(definition)
            reference_presentations.register(
                CardPresentation(
                    definition.card_id,
                    f"reference-token-{definition.card_id}",
                    definition.name,
                    "Texto público de referencia.",
                    f"reference/{definition.card_id}.webp",
                )
            )
        independent_catalog = PublicCardCatalog(
            reference_mechanics, reference_presentations
        )
        catalog_payload = independent_catalog.to_dict()
        self.assertEqual(len(catalog_payload["cards"]), 2)
        self.assertTrue(
            all(
                {"card_id", "kind", "name", "rules_text", "art"} <= set(card)
                for card in catalog_payload["cards"]
            )
        )
        self.assertTrue(
            {
                "match_id",
                "player_id",
                "zone",
                "zones",
                "quantity",
                "count",
                "position",
                "order",
                "deck_order",
                "owner",
                "match_membership",
            }.isdisjoint(set(nested_keys(catalog_payload)))
        )

        # Todos estos tokens tienen el mismo CAS vigente. Ni el tipo de fallo
        # ni sus datos públicos revelan por qué el token no pertenece al scope.
        rival_identity = ExternalIdentity(
            "https://identity.example", "phase-1c-rival"
        )
        self.authorization.bind_player(rival_identity, self.match_id, "B")
        rival_option = self.application.view(
            rival_identity, self.match_id
        ).legal_actions[0].option_id
        other_match_option = equivalent.legal_actions[0].option_id
        valid_option = original.legal_actions[0].option_id
        invalid_options = (
            "inexistente",
            tamper_option_id(valid_option),
            other_match_option,
            rival_option,
        )
        baseline = self.application.view(self.identity, self.match_id)
        observed_errors = []
        for option_id in invalid_options:
            with self.subTest(option_id=option_id), self.assertRaises(
                OptionRejected
            ) as caught:
                self.application.submit_option(
                    self.identity,
                    self.match_id,
                    option_id,
                    expected_version=baseline.version,
                )
            observed_errors.append(
                (type(caught.exception), caught.exception.code, str(caught.exception))
            )
            self.assertEqual(
                self.application.view(self.identity, self.match_id), baseline
            )
            self.assertEqual(vars(caught.exception), {})
        self.assertEqual(
            set(observed_errors),
            {
                (
                    OptionRejected,
                    "option_rejected",
                    "La alternativa pública fue rechazada",
                )
            },
        )

        committed = self.application.submit_option(
            self.identity,
            self.match_id,
            valid_option,
            expected_version=baseline.version,
        )
        with self.assertRaises(WriteConflict):
            self.application.submit_option(
                self.identity,
                self.match_id,
                valid_option,
                expected_version=baseline.version,
            )
        self.assertEqual(self.application.view(self.identity, self.match_id), committed)

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
