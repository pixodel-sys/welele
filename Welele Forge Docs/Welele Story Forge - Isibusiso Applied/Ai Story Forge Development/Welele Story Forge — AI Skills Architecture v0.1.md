# WELELE STORY FORGE
## AI Skills Architecture v0.1

### 1. Product Definition

**Welele Story Forge** is an AI-assisted narrative development engine that takes a raw story concept and systematically develops it into a **Forge Complete Story Package**.

It does not guarantee artistic brilliance.

It guarantees a disciplined process for resolving the narrative, structural and production dependencies required to move a story into production.

---

# 2. Core Architecture

The Forge consists of five layers:

### A. Story State
The current machine-readable representation of the story.

### B. AI Skills
Specialised capabilities that interrogate, analyse, construct or validate the story.

### C. Forge Orchestrator
Determines what the story needs next and activates the appropriate skill.

### D. Forge Judge
Continuously tests the story for unresolved dependencies, contradictions and weaknesses.

### E. Story Package
The production-ready output generated from the resolved Story State.

```text
RAW STORY
    │
    ▼
┌─────────────────────┐
│    STORY STATE      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ FORGE ORCHESTRATOR  │
└─────────┬───────────┘
          │
     selects skill
          │
          ▼
┌─────────────────────┐
│      AI SKILL       │
└─────────┬───────────┘
          │
    asks / analyses
          │
          ▼
┌─────────────────────┐
│   CREATOR ANSWER    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   UPDATE STATE      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│     FORGE JUDGE     │
└─────────┬───────────┘
          │
     unresolved?
      /        \
    YES         NO
     │           │
     └───→ next  ▼
             FORGE COMPLETE
```

---

# 3. Story State

The Forge must maintain a canonical Story State.

At minimum:

### Story
- premise
- genre
- tone
- theme
- dramatic question
- stakes
- conflict
- ending strategy

### Characters
- identity
- age
- background
- wants
- needs
- fears
- wounds
- motivations
- relationships
- secrets
- knowledge
- agency
- arc

### World
- locations
- rules
- social context
- organisations
- objects
- supernatural/technological rules

### Time
- dates
- ages
- elapsed time
- sequence
- time jumps
- temporal dependencies

### Knowledge
- what each character knows
- when they learned it
- how they learned it
- what they believe incorrectly

### Causality
- event
- cause
- consequence
- resulting state

### Structure
- season
- episodes
- sequences
- scenes
- beats

### Production
- cast
- locations
- props
- wardrobe
- vehicles
- VFX/SFX
- audio
- music
- shot requirements

### IP / Canon
- ownership
- contributors
- canonical elements
- versions
- rights
- shared-world relationships

---

# 4. AI Skill Model

Every AI Skill must have:

**Purpose**  
What problem does it solve?

**Inputs**  
What Story State does it require?

**Trigger**  
When should it activate?

**Action**  
What does it do?

**Output**  
What does it add/change?

**Validation**  
How does it know the work is sufficient?

**Dependencies**  
What other information may it expose as necessary?

---

# 5. Initial Skill Set

## EXCAVATION

### Premise Excavator
Discovers what the story is actually about.

### Character Excavator
Discovers character identity, motivation, wound, desire and agency.

### Relationship Excavator
Discovers why characters matter to one another.

### World Excavator
Discovers setting, rules and context.

### Conflict Excavator
Discovers opposing forces and sources of conflict.

### Stakes Excavator
Determines what can be lost or gained.

### Secret & Revelation Excavator
Discovers hidden information and when it should become known.

### Theme Excavator
Discovers the deeper question underneath the plot.

### Ending Excavator
Determines what the story is ultimately building toward.

---

# 6. NARRATIVE SKILLS

### Causality Engine
Tests:

> Because X happened, why does Y happen?

### Character Arc Engine
Tests whether character actions and changes arise from established character logic.

### Escalation Engine
Tests whether pressure increases rather than simply producing more events.

### Episode Engine
Converts the narrative into viable microdrama episodes.

### Scene Engine
Determines the dramatic function of every scene.

### Emotional Arc Engine
Tests whether emotional consequences have been earned.

### Revelation Engine
Controls information flow and dramatic reveals.

### Continuity Engine
Tests established facts against future events.

### Time Integrity Engine
Tracks age, dates, elapsed time and temporal transitions.

### Knowledge Integrity Engine
Tracks who knows what, when and why.

---

# 7. PRODUCTION SKILLS

### Script Builder
Converts the resolved narrative into screenplay/dialogue.

### Shot Planner
Determines visual requirements.

### Location Planner
Extracts location requirements.

### Cast Planner
Extracts character/casting requirements.

### Sound & Music Planner
Extracts dialogue, ambience, SFX, narration and music requirements.

### VFX/SFX Planner
Identifies effects and implementation dependencies.

### Production Dependency Analyzer
Determines what must be resolved or deliberately delegated to production.

---

# 8. FORGE JUDGE

The Judge does not primarily create.

It challenges.

It evaluates:

1. Story Integrity
2. Character Integrity
3. World Integrity
4. Time Integrity
5. Knowledge Integrity
6. Causal Integrity
7. Structural Integrity
8. Scene Integrity
9. Emotional Integrity
10. Production Integrity
11. IP/Canon Integrity

The Judge produces:

```text
PASS
WARNING
UNRESOLVED DEPENDENCY
CONTRADICTION
PRODUCTION DECISION REQUIRED
```

---

# 9. The Fundamental Forge Loop

The Forge operates according to:

**STATE → GAP → QUESTION → ANSWER → STATE UPDATE → VALIDATION → NEXT GAP**

The AI must never ask a question merely because it exists in a questionnaire.

### NO RANDOM QUESTIONS.

Every question must have a declared narrative purpose.

Examples:

- establish identity
- expose motivation
- reveal conflict
- establish stakes
- expose history
- test plausibility
- resolve contradiction
- establish world rule
- establish causality
- create escalation
- reveal character agency
- close a narrative dependency
- discover a better story

---

# 10. Forge Completion Principle

> **A Story Package is Forge Complete only when every narrative, structural and production dependency required to move the story into production has been resolved or explicitly marked as a production decision.**

Unknown is not automatically a failure.

An unresolved dependency is.

A deliberate production decision is acceptable.

---

# 11. Output

The Forge ultimately produces:

### STORY PACKAGE

- Story DNA
- Story World
- Character Bible
- Relationship Map
- Timeline
- Knowledge Map
- Causality Map
- Season Structure
- Episode Structures
- Scene Breakdown
- Scripts
- Dialogue
- Shot Requirements
- Production Bible
- Audio/Music Requirements
- VFX/SFX Requirements
- IP/Canon Record
- Forge Report

The underlying Story State remains the canonical source.

The documents are generated views of that state.