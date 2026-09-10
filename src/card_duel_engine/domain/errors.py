class GameRuleError(Exception):
    """Base para los rechazos normativos del motor."""


class InvalidDeckDefinition(ValueError):
    """Las definiciones de mazo no permiten preparar una partida."""


class IllegalAction(GameRuleError):
    """El comando no es legal en el estado actual."""


class PendingDecisionError(IllegalAction):
    """Base para rechazos del ciclo de vida de una decisión pendiente."""

    code = "pending_decision_error"


class DecisionSlotEmpty(PendingDecisionError):
    """No hay una decisión en el slot autoritativo."""

    code = "decision_slot_empty"


class DecisionIdMismatch(PendingDecisionError):
    """La identidad aportada no corresponde a la decisión del slot."""

    code = "decision_id_mismatch"


class UnauthorizedDecisionElector(PendingDecisionError):
    """El actor no está autorizado para resolver la decisión."""

    code = "unauthorized_decision_elector"


class UnauthorizedDecisionOption(PendingDecisionError):
    """La opción aportada no está autorizada para la decisión."""

    code = "unauthorized_decision_option"


class DecisionAlreadyClosed(PendingDecisionError):
    """La decisión del slot ya alcanzó su estado terminal."""

    code = "decision_already_closed"


class DecisionSlotOccupied(PendingDecisionError):
    """El slot autoritativo ya contiene una decisión."""

    code = "decision_slot_occupied"


class StaleDecisionVersion(PendingDecisionError):
    """La versión conocida no corresponde a la decisión vigente."""

    code = "stale_decision_version"


class InvariantViolation(GameRuleError):
    """El estado interno ha quedado corrupto."""


class PaymentError(IllegalAction):
    """El jugador no puede pagar un coste completo."""


class UnsupportedEffectError(GameRuleError):
    """La resolución recibió un tipo de efecto fuera del registro cerrado."""
