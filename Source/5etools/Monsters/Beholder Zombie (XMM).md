---
name: Beholder Zombie
source: XMM
source_full: 2024 Monster Manual
aliases: [Beholder Zombie (XMM)]
tags: [ai_generated, 5etools, monster, undead, cr-5]
type: monster
size: Large
monster_type: undead
alignment: Neutral Evil
armor_class: 15
hit_points: 93
challenge_rating: 5
xp: 1800
---

# Beholder Zombie

*Large undead, Neutral Evil*

---

**Armor Class** 15  
**Hit Points** 93 (11d10 + 33)  
**Speed** walk 5 ft., fly 20 ft. (hover), canHover (equal to walking)

---

| **STR** 14 (+2) | **DEX** 8 (-1) | **CON** 16 (+3) | **INT** 3 (-4) | **WIS** 8 (-1) | **CHA** 5 (-3) |

---

**Saving Throws** WIS +2  
**Skills** —  
**Damage Resistances** —  
**Damage Immunities** poison  
**Condition Immunities** exhaustion, poisoned, prone  
**Senses** Darkvision 60 ft., passive Perception 9  
**Languages** understands Deep Speech and Undercommon but can't speak  
**Challenge** 5 (1,800 XP)

---

## Traits

**Undead Fortitude.** If damage reduces the zombie to 0 [[Hit Points|XPHB]], it makes a Constitution saving throw (DC 5 plus the damage taken) unless the damage is Radiant or from a [[Critical Hit|XPHB]]. On a successful save, the zombie drops to 1 [[Hit Points|XPHB]] instead.


## Actions

**Multiattack.** The zombie uses Eye Rays twice.

**Bite.** m +5, reach 5 ft. @h16 (**4d6 + 2**) Piercing damage.

**Eye Rays.** The zombie randomly shoots one of the following magical rays at a target it can see within 120 feet of itself (roll `1d4`; reroll if the zombie has already used that ray during this turn):

- **1: Paralyzing Ray:** con DC 14. @actSaveFail The target has the [[Paralyzed|XPHB]] condition and repeats the save at the end of each of its turns, ending the effect on itself on a success. After 1 minute, it succeeds automatically.
- **2: Fear Ray:** wis DC 14. @actSaveFail 13 (**3d8**) Psychic damage, and the target has the [[Frightened|XPHB]] condition until the end of its next turn.
- **3: Enervation Ray:** con DC 14. @actSaveFail 10 (**3d6**) Necrotic damage, and the target has the [[Poisoned|XPHB]] condition until the end of its next turn. While [[Poisoned|XPHB]], the target can't regain [[Hit Points|XPHB]]. @actSaveSuccess Half damage only.
- **4: Disintegration Ray:** dex DC 14. @actSaveFail 27 (**5d10**) Force damage. If the target is a nonmagical object or a creation of magical force, a 10-foot [[Cube [Area of Effect]|XPHB]] of it disintegrates into dust. @actSaveSuccess Half damage. @actSaveSuccessOrFail If the target is a creature and this damage reduces it to 0 [[Hit Points|XPHB]], it disintegrates into dust.






---

**Source:** 2024 Monster Manual, p. 347
