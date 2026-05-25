# Hermes Specialist Router

The `hermes.specialists` package provides intent classification and specialist dispatch for Hermes Agent.  A **router** classifies incoming user messages with an LLM, then hands off the conversation to the most relevant **specialist** — a focused sub-agent configured for a particular domain (e.g. billing, technical support, onboarding).

## Architecture

```
User message
      │
      ▼
 classify()          ← uses CLASSIFIER_PROMPT + Claude
      │
      ▼
IntentClassification
      │
      ├── fetch_kb_context()   ← retrieves KB snippets for the intent
      │
      ▼
HandoffPacket
      │
      ▼
BaseSpecialist.handle()
      │
      ▼
SpecialistResult  → response sent to user
```

## `config.yaml` schema

Add a `specialists` section to your Hermes `config.yaml` to configure the router:

```yaml
specialists:
  # RouterConfig fields
  classifier_model: claude-haiku-4-5-20251001   # fast, cheap classifier
  confidence_threshold: 0.6                      # route only when confident
  default_specialist: general                    # fallback when below threshold
  kb_base_url: https://kb.example.com/api/v1    # optional base URL for kb_sources

  # List of SpecialistConfig entries
  routing:
    - name: billing
      description: >
        Handles questions about invoices, payments, subscription plans,
        refunds, and pricing.
      triggers:
        - invoice
        - payment
        - subscription
        - refund
        - pricing
      kb_sources:
        - /billing/faq
        - /billing/policies

    - name: technical_support
      description: >
        Assists with product installation, configuration errors, API
        integration, and debugging.
      triggers:
        - error
        - crash
        - install
        - configuration
        - api
      kb_sources:
        - /support/troubleshooting
        - /support/api-reference

    - name: general
      description: >
        Catches all intents that do not clearly belong to another specialist.
      triggers: []
      kb_sources: []
```

### Field reference

| Field | Type | Default | Description |
|---|---|---|---|
| `classifier_model` | `str` | `claude-haiku-4-5-20251001` | Model used to classify user intent |
| `confidence_threshold` | `float` | `0.6` | Minimum confidence to route to a non-default specialist |
| `default_specialist` | `str \| null` | `null` | Fallback specialist name |
| `kb_base_url` | `str \| null` | `null` | Base URL prepended to relative `kb_sources` paths |
| `routing[].name` | `str` | — | Unique specialist identifier |
| `routing[].description` | `str` | — | Plain-language description for the classifier prompt |
| `routing[].triggers` | `list[str]` | `[]` | Hint keywords (supplementary, not hard-matched) |
| `routing[].kb_sources` | `list[str]` | `[]` | KB paths/URLs queried by `fetch_kb_context()` |
