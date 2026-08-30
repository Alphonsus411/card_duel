from pathlib import Path
import hashlib, json, subprocess, sys
sys.path.insert(0, 'src')
from card_duel_engine import GameEngine, RuleSet
from card_duel_engine.domain import AbilityDefinition, CardDefinition, CardKind, CompositeCost, EffectDefinition, EffectKind, Phase, TargetMode, Zone
from card_duel_engine.engine import ActivateAbility, AdvancePhase, PassPriority, PlayCard
from card_duel_engine.persistence import dump_replay

OUT=Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent

def make(sacrifice):
    ability=AbilityDefinition('pending_shot',(EffectDefinition(EffectKind.DEAL_WOUNDS,1,TargetMode.CHOSEN_PLAYER),),cost=CompositeCost(sacrifice_count=1 if sacrifice else 0))
    source=CardDefinition('SOURCE_SAC' if sacrifice else 'SOURCE_PRESENT','Fuente histórica',CardKind.CREATURE,0,base_strength=2,abilities=(ability,),set_id='legacy-profile')
    filler=CardDefinition('FILLER_SAC' if sacrifice else 'FILLER_PRESENT','Relleno',CardKind.CREATURE,0,base_strength=1,set_id='legacy-profile')
    engine=GameEngine(RuleSet(version='0.20.1'))
    engine.new_match({'A':[source]*12,'B':[filler]*12},seed=421 if sacrifice else 420)
    while engine.state.phase is not Phase.EFFECTS:
        engine.execute(PassPriority(engine.state.priority_player_id)); engine.execute(PassPriority(engine.state.priority_player_id)); engine.execute(AdvancePhase('A'))
    source_id=engine.state.players['A'].zones[Zone.HAND][0]
    engine.execute(PlayCard('A',source_id)); engine.execute(PassPriority('B')); engine.execute(PassPriority('A'))
    engine.execute(ActivateAbility('A',source_id,'pending_shot',chosen_player_ids=('B',),sacrifice_card_ids=(source_id,) if sacrifice else ()))
    name='pending-ability-source-sacrificed.replay-v2.json' if sacrifice else 'pending-ability-source-present.replay-v2.json'
    raw=dump_replay(engine)
    (OUT/name).write_text(raw,encoding='utf-8')
    doc=json.loads(raw); state=engine.state
    return {'file':name,'file_sha256':hashlib.sha256(raw.encode()).hexdigest(),'final_digest':doc['body']['final_digest'],'commands':len(state.command_history),'events':len(state.event_log),'last_event':state.event_log[-1].event_type,'stack':[{'item_id':x.item_id,'source_card_id':x.source_card_id,'ability_id':x.ability_id,'chosen_player_ids':list(x.chosen_player_ids)} for x in state.stack], 'source_zone':state.cards[source_id].zone.name,'final':{'phase':state.phase.name,'turn_serial':state.turn_serial,'priority_player_id':state.priority_player_id,'next_instance':engine._next_instance,'next_stack_item':engine._next_stack_item}}

records=[make(False),make(True)]
(OUT/'metadata.json').write_text(json.dumps({'provenance':{'git_commit':'c0c1ee1^','resolved_commit':subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),'engine_version':'0.20.1','python':sys.version.split()[0]},'artifacts':records},indent=2,sort_keys=True)+'\n')
