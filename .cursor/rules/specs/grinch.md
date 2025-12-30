
# 📜 Specification: “The Long Night & the Grinch of Mt. Crumpit”

**Target System:** Curse of Strahd Reloaded (DM Vault)
**Scope:** One-shot / side-quest content pack
**Audience:** Cursor coding agent (markdown generation + diffs)

---

## 0. Global Constraints & Conventions

### Repository / Branching

* **Base branch:** `blors`
* **Do NOT target:** `main`
* Agent should:

  * Assume files already exist in vault
  * Create **new markdown files only**
  * Avoid modifying existing files unless explicitly instructed

### Formatting & Metadata

* All new pages MUST:

  * Use existing vault frontmatter conventions
  * Include `tags: [ai_generated, ...]`
* DM-only content must be wrapped in:

  ```md
  <!-- DM ONLY -->
  ...
  <!-- /DM ONLY -->
  ```

### Tone & Canon

* Tone: **Barovian gothic, restrained dark humor**
* Canon alignment:

  * Curse of Strahd Reloaded
  * No contradiction of Arc G (Strazni Siblings)
  * Blinsky’s Toys may be impacted but **not broken**
* Metaphysics:

  * Mt. Crumpit uses **Model II: Mist-Pocket Demi-Refuge**
  * Analogous to the Abbey of Saint Markovia (localized anomaly)

---

## 1. NPC Pages

**Directory:** `DM Wiki/Entities/NPCs/`

### 1.1 `The Grinch.md`

**Purpose:** Primary antagonist / tragic figure / possible ally

**Frontmatter (example fields – match existing NPC schema):**

```yaml
---
name: The Grinch
type: NPC
location: Mt. Crumpit
alignment: Chaotic Neutral
challenge_rating: 8
tags: [npc, ai_generated]
---
```

**Required Sections:**

* Overview
* Appearance & Demeanor
* Personality Traits
* Motivations & Fears
* Relationships

  * Max
  * Vallaki (general)
  * Strahd (observational, distant)
* Roleplaying Notes (voice, cadence, insults, emotional beats)

<!-- DM ONLY -->

* **Stat Block**

  * CR ~8
  * Multiclass: Barbarian / Artificer
  * Rage + gadgets
* **Combat Tactics**
* **Redemption Conditions**
* **If Slain / If Redeemed Outcomes**
* **Connection to the Mists**

<!-- /DM ONLY -->

---

### 1.2 `Max.md`

**Purpose:** Emotional lever; noncombatant support NPC

**Frontmatter:**

```yaml
---
name: Max
type: NPC
species: Dog (Steel Defender analogue)
tags: [npc, ai_generated]
---
```

**Required Sections:**

* Overview
* Appearance
* Behavior & Loyalty
* Relationship to the Grinch

<!-- DM ONLY -->

* Simplified stat block (Steel Defender–like)
* How players can bond with Max
* Mechanical effects of kindness to Max

<!-- /DM ONLY -->

---

### 1.3 Optional NPC (Agent discretion)

Examples:

* Blinsky (addendum NPC page **only if** needed)
* Vallakian child witness

> Agent should only add new NPCs if they materially support the quest.

---

## 2. Area Pages

**Directory:** `DM Wiki/Entities/Areas/`

### 2.1 `Mt Crumpit.md`

**Purpose:** Dungeon / lair / metaphysical anomaly

**Frontmatter:**

```yaml
---
name: Mt. Crumpit
type: Area
region: Near Vallaki
tags: [area, ai_generated]
---
```

**Required Sections:**

* Overview
* Approach & Ascent
* Environmental Hazards
* The Threshold (mist-pocket transition)
* Workshop Exterior
* Workshop Interior Zones (high-level, not full map)

<!-- DM ONLY -->

* Lair Actions
* Teleportation / Magic Restrictions
* Comparison to Abbey of Saint Markovia
* What happens if the Grinch is redeemed

<!-- /DM ONLY -->

---

## 3. Lore Pages

**Directory:** `DM Wiki/Entities/Lore/`

### 3.1 `The Grinch (Vallakian Lore).md`

**Purpose:** Player-facing rumor aggregation

**Frontmatter:**

```yaml
---
name: The Grinch (Local Lore)
type: Lore
location: Vallaki
tags: [lore, ai_generated]
---
```

**Required Sections:**

* What Vallakians Say (rumors, contradictions)
* What Children Believe
* What Guards Believe
* What Is *Not* Known

<!-- DM ONLY -->

* Truth vs rumor table
* How this lore evolves after the quest

<!-- /DM ONLY -->

---

## 4. Event Pages

**Directory:** `DM Wiki/Entities/Special_Events/`

### 4.1 `The Long Night.md`

**Purpose:** Winter solstice analog (Christmas equivalent)

**Frontmatter:**

```yaml
---
name: The Long Night
type: Special Event
calendar: Winter Solstice
tags: [event, ai_generated]
---
```

**Required Sections:**

* Overview
* Cultural Meaning in Barovia
* Typical Observances
* How Vallaki Marks the Night

<!-- DM ONLY -->

* Why Strahd tolerates this observance
* How the Grinch targets this night
* Mood-setting boxed text

<!-- /DM ONLY -->

---

### 4.2 Optional: `The Theft at Blinsky’s Toys.md` (Optional but Recommended)

If included:

* Frame as **incident**, not full festival disruption
* Keep Arc G intact

---

## 5. Item Pages

**Directory:** `DM Wiki/Entities/Items/`

### Required Items (Minimum 2)

#### 5.1 `Sleigh Boots.md`

* Snow/ice mobility
* Limited daily use

#### 5.2 `Snap-Trap Net.md`

* Consumable control item

**Frontmatter (example):**

```yaml
---
name: Sleigh Boots
type: Wondrous Item
rarity: Uncommon
tags: [item, ai_generated]
---
```

**Required Sections:**

* Description
* Mechanics
* Lore Flavor

<!-- DM ONLY -->

* Balance notes
* Alternate versions (cursed / improved)

<!-- /DM ONLY -->

---

## 6. Cross-Linking Expectations

Agent should:

* Link NPCs ↔ Areas ↔ Events
* Use existing Obsidian link syntax
* Avoid dead links
* Prefer semantic consistency over over-linking

---

## 7. Explicit Non-Goals (Important)

The agent MUST NOT:

* Modify existing Arc G files
* Rename existing locations
* Add Strahd as an active NPC here
* Introduce new Dark Powers
* Canonize the Grinch as a god or Darklord

---

## 8. Success Criteria

This task is complete when:

* All required markdown files exist
* Files are in correct directories
* Frontmatter is valid
* DM-only content is clearly fenced
* Tone matches Barovia
* The one-shot is runnable *without* touching other arcs

---

## 9. Final Instruction to Cursor Agent

> *“Generate clean markdown diffs only. Assume existing templates and schemas. Do not invent new global structures. Optimize for readability, DM usability, and canon safety.”*

---

If you want, next I can:

* Produce a **test checklist** for validating the agent’s output
* Write a **player-facing redacted bundle**
* Convert this into a **Cursor system prompt** verbatim
