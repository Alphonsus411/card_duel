from __future__ import annotations

from enum import Enum, auto


class Zone(Enum):
    DECK = auto()
    HAND = auto()
    BATTLEFIELD = auto()
    DISCARD = auto()
    EXILE = auto()
    RESOLUTION = auto()
    REVEAL = auto()
    VOID = auto()


class Phase(Enum):
    DRAW = auto()
    MAINTENANCE = auto()
    EFFECTS = auto()
    COMBAT = auto()
    LEGENDARY = auto()
    DISCARD = auto()


class PlayerRole(Enum):
    ACTIVE = auto()
    PASSIVE = auto()


class CardKind(Enum):
    CREATURE = auto()
    EVENT = auto()
    QUICK_RESOURCE = auto()
    EQUIPMENT = auto()
    ARTIFACT = auto()
    LORD = auto()


class CardRank(Enum):
    STANDARD = auto()
    LEGENDARY = auto()
    DIVINE = auto()


class MatchStatus(Enum):
    SETUP = auto()
    RUNNING = auto()
    FINISHED = auto()
    BLOCKED = auto()


class EffectKind(Enum):
    DEAL_WOUNDS = auto()
    HEAL_WOUNDS = auto()
    GAIN_STEPS = auto()
    DRAW_CARDS = auto()
    DEAL_DAMAGE = auto()
    MODIFY_STRENGTH = auto()
    TAP = auto()
    UNTAP = auto()
    DESTROY = auto()
    PREVENT_WOUNDS = auto()
    PREVENT_DAMAGE = auto()
    BECOME_CREATURE = auto()
    DEAL_HARM = auto()
    MOVE_CARDS = auto()
    ADD_REGENERATION = auto()
    SKIP_PHASE = auto()
    SEARCH_ZONE = auto()
    SHUFFLE_ZONE = auto()
    CHANGE_CONTROL = auto()
    COPY_DEFINITION = auto()
    TRANSFORM_DEFINITION = auto()
    MODIFY_TEXT = auto()
    REVEAL_UNTIL = auto()


class RevealExhaustionPolicy(Enum):
    """Resultado de agotar la zona sin encontrar una coincidencia."""

    COMPLETE = auto()


class CostComponent(Enum):
    STEPS = "steps"
    WOUNDS = "wounds"
    DISCARD_COUNT = "discard_count"
    SACRIFICE_COUNT = "sacrifice_count"
    STRENGTH = "strength"
    MILL_COUNT = "mill_count"


class CostMetric(Enum):
    OWN_WOUNDS = auto()
    OWN_STEPS = auto()
    OWN_HAND_SIZE = auto()
    OWN_BATTLEFIELD_SIZE = auto()
    OWN_DISCARD_SIZE = auto()
    OWN_EXILE_SIZE = auto()
    OPPONENT_BATTLEFIELD_SIZE = auto()
    TURN_NUMBER = auto()


class TargetMode(Enum):
    SELF = auto()
    CHOSEN_PLAYER = auto()
    SOURCE = auto()
    CHOSEN_PERMANENT = auto()
    CHOSEN_ZONE = auto()
    CHOSEN_ENTITY = auto()


class EffectDuration(Enum):
    PERMANENT = auto()
    END_OF_TURN = auto()
    NEXT_OCCURRENCE = auto()


class TriggerKind(Enum):
    ON_ENTER_BATTLEFIELD = auto()
    ON_TRANSMUTED = auto()


class LordDomain(Enum):
    ABYSS = auto()
    ELYSIUM = auto()
    MAGIC = auto()
    REALMS = auto()


class Keyword(Enum):
    """Capacidades declarativas que pueden figurar en una definición de carta."""

    CAN_CHALLENGE = auto()


class ControllerScope(Enum):
    SELF = auto()
    OPPONENTS = auto()
    ALL = auto()


class MoveReason(Enum):
    RULE = auto()
    DISCARD = auto()
    DESTROY = auto()
    STATE_BASED = auto()
    TRANSMUTE = auto()
    SACRIFICE = auto()
    RESOLVE = auto()
