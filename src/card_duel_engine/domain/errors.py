class GameRuleError(Exception):
    """Base para los rechazos normativos del motor."""


class InvalidDeckDefinition(ValueError):
    """Las definiciones de mazo no permiten preparar una partida."""


class IllegalAction(GameRuleError):
    """El comando no es legal en el estado actual."""


class InvariantViolation(GameRuleError):
    """El estado interno ha quedado corrupto."""


class PaymentError(IllegalAction):
    """El jugador no puede pagar un coste completo."""


class UnsupportedEffectError(GameRuleError):
    """La resolución recibió un tipo de efecto fuera del registro cerrado."""
