import Gameplay as gp
from Gameplay import Canon, Repetition

gp.start()
p1, p2, p3, p4 = gp.p1, gp.p2, gp.p3, gp.p4
caster = p1
target = p2
caster.s = [Canon(), Repetition()]
target.s = [Canon(), Repetition()]

caster.spell = caster.s[0]
caster.cible = target
caster.spell.start(caster, target, [caster, target, p3, p4])
caster.spell.action(caster, target, [caster, target, p3, p4])
caster.spell.end(caster, target, [caster, target, p3, p4])
print('after canon', target.pv)

caster.spell = caster.s[1]
caster.cible = target
caster.spell.start(caster, target, [caster, target, p3, p4])
caster.spell.action(caster, target, [caster, target, p3, p4])
caster.spell.end(caster, target, [caster, target, p3, p4])
print('after repeat', target.pv)
