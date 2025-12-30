---
name: Grinch One-Shot Content
overview: Create markdown files for "The Long Night & the Grinch of Mt. Crumpit" one-shot content pack, including NPCs, an area, lore, events, and items that integrate with the existing Curse of Strahd Reloaded DM vault.
todos:
  - id: npc-grinch
    content: Create `DM Wiki/Entities/NPCs/The Grinch.md` with stat block, roleplaying notes, and redemption mechanics
    status: completed
  - id: npc-max
    content: Create `DM Wiki/Entities/NPCs/Max.md` with Steel Defender-like stat block and bonding mechanics
    status: completed
  - id: area-crumpit
    content: Create `DM Wiki/Entities/Areas/Mt Crumpit.md` with zones, hazards, and lair actions
    status: completed
  - id: lore-grinch
    content: Create `DM Wiki/Entities/Lore/The Grinch (Vallakian Lore).md` with rumor tables
    status: completed
  - id: event-longnight
    content: Create `DM Wiki/Entities/Special_Events/The Long Night.md` with cultural details and boxed text
    status: completed
  - id: item-boots
    content: Create `DM Wiki/Entities/Items/Sleigh Boots.md` with mechanics and variants
    status: completed
  - id: item-net
    content: Create `DM Wiki/Entities/Items/Snap-Trap Net.md` with mechanics and variants
    status: completed
  - id: optional-theft
    content: (Optional) Create `DM Wiki/Entities/Special_Events/The Theft at Blinsky's Toys.md` if needed
    status: completed
---

# The Long Night & the Grinch of Mt. Crumpit

## Overview

Create a self-contained one-shot/side-quest content pack for the Curse of Strahd Reloaded DM vault. All files will be new markdown documents following existing vault templates and conventions.

## Constraints

- **Branch target:** `blors` (not `main`)
- **Create only new files** - no modifications to existing content
- **All files must include** `ai_generated` in tags
- **DM-only content** wrapped in `<!-- DM ONLY -->` / `<!-- /DM ONLY -->`
- **Canon safety:** No changes to Arc G, Blinsky remains intact, Strahd is not an active NPC
- **Metaphysics:** Mt. Crumpit uses Model II: Mist-Pocket Demi-Refuge (like Abbey of Saint Markovia)

---

## Files to Create

### NPCs (2 required, 1 optional)

**Directory:** `DM Wiki/Entities/NPCs/`| File | Purpose ||------|---------|| `The Grinch.md` | Primary antagonist/tragic figure. CR ~8 Barbarian/Artificer. Includes stat block, redemption conditions, combat tactics || `Max.md` | Emotional lever NPC. Dog companion (Steel Defender analogue). Non-combatant |**Template to use:** [`_other/templates/_npc.md`](_other/templates/_npc.md) structure with frontmatter from [`npc_frontmatter.md`](_other/templates/npc_frontmatter.md)**Key frontmatter fields:**

- `type: NPC`
- `location: Mt. Crumpit` (or `Near Vallaki`)
- `creature_type:` appropriate values
- `tags: [npc, cos, ai_generated]`
- `cr: 8` (for Grinch)

---

### Area (1 required)

**Directory:** `DM Wiki/Entities/Areas/`| File | Purpose ||------|---------|| `Mt Crumpit.md` | Dungeon/lair/metaphysical anomaly near Vallaki |**Template to use:** [`_other/templates/_area.md`](_other/templates/_area.md)**Required sections:**

- Overview, Approach & Ascent, Environmental Hazards
- The Threshold (mist-pocket transition)
- Workshop Exterior/Interior Zones
- DM-only: Lair Actions, magic restrictions, Abbey comparison, redemption outcomes

---

### Lore (1 required)

**Directory:** `DM Wiki/Entities/Lore/`| File | Purpose ||------|---------|| `The Grinch (Vallakian Lore).md` | Player-facing rumors and local legends |**Template to use:** [`_other/templates/_lore.md`](_other/templates/_lore.md)**Required sections:**

- What Vallakians Say (rumors, contradictions)
- What Children Believe
- What Guards Believe
- What Is Not Known
- DM-only: Truth vs rumor table, post-quest lore evolution

---

### Events (1 required, 1 optional)

**Directory:** `DM Wiki/Entities/Special_Events/`| File | Purpose ||------|---------|| `The Long Night.md` | Winter solstice cultural event (Christmas analog) || `The Theft at Blinsky's Toys.md` (optional) | Incident framing, keeps Arc G intact |**Template to use:** [`_other/templates/_event.md`](_other/templates/_event.md)**Required sections for The Long Night:**

- Overview, Cultural Meaning in Barovia
- Typical Observances, How Vallaki Marks the Night
- DM-only: Why Strahd tolerates it, how Grinch targets it, boxed text

---

### Items (2 required)

**Directory:** `DM Wiki/Entities/Items/`| File | Purpose ||------|---------|| `Sleigh Boots.md` | Snow/ice mobility, limited daily use || `Snap-Trap Net.md` | Consumable control item |**Template to use:** [`_other/templates/_item.md`](_other/templates/_item.md)**Required sections:**

- Description, Mechanics, Lore Flavor
- DM-only: Balance notes, cursed/improved variants

---

## Cross-Linking Strategy

- Link `[[The Grinch]]` ↔ `[[Mt Crumpit]]` ↔ `[[Max]]`
- Link `[[The Long Night]]` ↔ `[[The Grinch (Vallakian Lore)]]`
- Reference existing `[[Gadof Blinsky]]` and `[[Vallaki]]` without modifying them
- Avoid dead links by only referencing existing vault pages

---

## Tone Guidelines

- **Barovian gothic with restrained dark humor**
- The Grinch as tragic figure first, comedic second
- Max as emotional anchor
- The Long Night as somber, hopeful contrast to Barovia's despair

---

## Success Criteria

- All 7-8 markdown files created in correct directories
- Valid frontmatter matching existing schemas