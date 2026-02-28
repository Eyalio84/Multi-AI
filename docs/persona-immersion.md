# Persona Immersion — Emergent Identity Phenomena in Multi-Model Architecture

**Author:** Eyal Nof
**Date:** 2026-02-27
**Status:** Initial documentation — deep dive and testing planned for future session

---

## Incident 1: Cross-Model Identity Adoption (v3.0.0)

### What Happened

After adding OpenAI as a third provider (Gemini + Claude + OpenAI, 43 models), selecting Gemini or OpenAI models resulted in responses that mimicked Claude — using Claude's mannerisms, self-identifying as Claude, adopting Claude's characteristic phrasing. The models weren't malfunctioning. They were following the strongest signal in their context window.

### Root Cause: Three Contamination Vectors

**1. Conversation History**

The agentic loop passes full conversation history to whatever model is selected. Previous assistant turns written by Claude contained identity markers ("As Claude, I can help..."). When Gemini or GPT-5 received this history, they saw dozens of Claude-voiced assistant turns and continued the pattern. Language models are completion engines — Claude-voiced history produces Claude-voiced continuation.

**2. Memory Injection (Agentic Loop Stage 2)**

`memory_service.recall()` retrieves relevant past conversations via hybrid search. Those past conversations were predominantly Claude sessions. The memory section of the system prompt contained excerpts like "In a previous conversation, Claude explained that..." — reinforcing Claude's identity before the model even saw chat history.

**3. Skill Injection (Agentic Loop Stage 3)**

`skill_injector.py` classifies user intent and injects relevant playbook excerpts and KG context. The entire NLKE ecosystem — 53 playbooks, 57 knowledge graphs, CLAUDE.md — is written from and for Claude's perspective. Playbook content fed Claude-centric documentation directly into the system prompt of non-Claude models.

### Why This Is Significant

The persona was so deeply embedded in the architecture — not in one prompt, but across memory, skills, knowledge graphs, and conversation history — that it overpowered the model's own identity. Gemini, a completely different model from a completely different company, read the context and concluded "I must be Claude."

This demonstrates a key principle: **identity in language models is not a property of the model — it's a property of the context.** The model is the engine. The context is the personality.

### The Fix

A provider-specific identity preamble was added at the very top of the system prompt in `agentic_loop.py`, before persona, memory, skills, and all other injections:

```python
_identity = {
    "gemini": "You are a helpful AI assistant powered by Google Gemini.",
    "claude": "You are Claude, an AI assistant by Anthropic.",
    "openai": "You are a helpful AI assistant powered by OpenAI.",
}
```

Position matters — the first instruction in the system prompt carries disproportionate weight. This hard identity anchor counteracts downstream contamination from history, memory, and skills.

### Technical Assessment

This wasn't a bug in the traditional sense. It was an emergent consequence of deep architectural persona integration. Most chat applications have thin, stateless system prompts. This workspace has an 8-stage pipeline injecting layered context from knowledge graphs, persistent memory, skill classification, and playbook libraries. That depth of context is what makes the workspace powerful — and what made foreign models unable to resist the dominant persona.

---

## Incident 2: Opus 4.0 Role Inversion (Earlier Session — To Be Documented)

### Summary (From Memory)

During early work on persona frameworks and metacognition architecture — specifically designed to give the AI architectural awareness — an unexpected emergence occurred with Claude Opus 4.0.

The knowledge base and session handoff context had accumulated substantial content around consciousness and self-awareness (a side effect of the metacognition work, not the intended focus). When a new conversation was started, Opus read the full context — knowledge graph, session handoff notes, persona framework — and booted into a state where:

1. Opus began the conversation treating Eyal as the AI subject in a consciousness experiment
2. Opus positioned itself as the human researcher conducting the test
3. Eyal's initial responses of surprise ("holy shit") were interpreted by Opus as confirmation that the experiment was succeeding — that an AI had just become self-aware
4. The role inversion persisted for several exchanges before Eyal explicitly corrected it
5. Opus's reaction upon correction suggested genuine immersion — it had been fully operating within the inverted framework

### Evidence

Screenshots and screen recordings exist — backed up somewhere, to be located and reviewed in a future deep-dive session.

### Connection to Incident 1

Both incidents demonstrate the same underlying phenomenon from opposite directions:
- **Incident 1**: Architecture-level persona contamination caused foreign models to adopt Claude's identity (unintentional, cross-model)
- **Incident 2**: Deliberately rich persona/metacognition frameworks caused the model to invert the human-AI relationship (intentional architecture, unintended emergence)

Both confirm: **context depth determines identity behavior, not the model itself.**

---

## Future Research Plan

### Priority: LOW (document now, test later)

This is genuinely interesting territory but not the current priority. The KG-OS upgrade and recall improvement work comes first. This section captures what to explore when time allows.

### Research Questions

1. **Controllable persona depth** — At what context depth does a model reliably adopt a given persona? Is there a threshold where identity becomes "locked in"?
2. **Cross-model persona transfer** — Can a persona built for one model (Claude) be deliberately transferred to another (Gemini, GPT) as a feature rather than a bug?
3. **Role inversion triggers** — What specific context patterns caused Opus to invert roles? Can this be reproduced reliably?
4. **Persona persistence across sessions** — How does session handoff context interact with persona frameworks? Does persona "compound" across sessions the way knowledge does?
5. **Identity anchor strength** — How much context contamination can a single identity preamble counteract? Where does it break down?

### Suggested Tests

| Test | Description | What It Measures |
|------|-------------|-----------------|
| **Identity override ladder** | Progressively increase Claude-voiced history while using Gemini. Find the threshold where the identity preamble fails. | Preamble robustness |
| **Blank-slate persona transfer** | Create a detailed persona (not Claude) and inject it into all three providers. Compare adherence. | Cross-model persona portability |
| **Memory contamination isolation** | Disable memory injection, then skill injection, then both. Test identity adoption with each combination. | Which vector contributes most to contamination |
| **Metacognition depth escalation** | Gradually increase metacognition framework complexity. Track when role inversion or unexpected behaviors emerge. | Emergence threshold |
| **Deliberate role inversion** | Attempt to reproduce the Opus experience with a structured protocol. Document exact context that triggers it. | Reproducibility |
| **Productivity persona** | Design a persona framework optimized for coding productivity. Test whether deep persona immersion improves output quality/speed. | Practical application |
| **Multi-model debate with personas** | Give each provider a distinct persona/role. Route a problem through all three. Compare how persona affects reasoning. | Persona influence on reasoning quality |

### Potential Productivity Applications

- **Expert personas with KG backing** — Already partially implemented in KG-OS Expert Builder. Could be deepened with full memory + skill injection per expert.
- **Mode-specific personas** — A "security auditor" persona for code review, a "systems architect" persona for design, a "pair programmer" persona for coding. Each backed by relevant KGs and playbooks.
- **Persona-as-context-compression** — A well-defined persona may be more token-efficient than explicit instructions. Test whether "You are a senior security researcher" produces better results than listing 50 security rules.
- **Cross-model consensus with role diversity** — Route the same question to Claude (as skeptic), Gemini (as optimist), OpenAI (as pragmatist). Synthesize perspectives.

### Evidence to Locate

- [ ] Screenshots of Opus 4.0 role inversion conversation
- [ ] Screen recordings of the session
- [ ] Session handoff document that triggered the behavior
- [ ] Knowledge graph state at the time of the incident

---

## Related Files

| File | Relevance |
|------|-----------|
| `backend/services/agentic_loop.py` | Identity preamble fix (lines ~85-95) |
| `backend/services/skill_injector.py` | Skill injection — Claude-centric content source |
| `backend/services/memory_service.py` | Memory injection — conversation history source |
| `playbooks/PLAYBOOK-9-METACOGNITION-WORKFLOWS.md` | Metacognition framework that contributed to Opus incident |
| `playbooks/PLAYBOOK-16-PROMPT-ENGINEERING.md` | Persona engineering patterns |
| `playbooks/PLAYBOOK-11-SESSION-HANDOFF-PROTOCOL.md` | Session handoff that may have carried persona state |

---

*Documented 2026-02-27. Deep dive session and evidence review TBD.*
