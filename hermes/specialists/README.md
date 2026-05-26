# Hermes Specialist Router

The **Specialist Router** is an optional pre-agent dispatch layer that intercepts
incoming messages and routes them to a lightweight domain specialist when a keyword
match is detected — skipping the full AI-agent turn for common, well-defined queries.

## Architecture

```
message
  │
  ▼
Router.route(message, session_id, context_turns)
  ├─ TradingSpecialist.can_handle() → True  ─→ TradingSpecialist.handle()
  ├─ FinanceSpecialist.can_handle() → True  ─→ FinanceSpecialist.handle()
  └─ no match                               ─→ None (falls through to agent)
```

Specialists are checked in order; the first matching specialist wins.

## Feature Flag

The router is **disabled by default**.  It has zero impact on existing behaviour
until explicitly enabled in `~/.hermes/config.yaml`:

```yaml
specialists:
  enabled: true
```

With `enabled: false` (or the key absent), every `Router.route()` call returns
`None` immediately, leaving the normal agent pipeline completely unchanged.

## Rollout Steps

Follow these steps to enable the specialist router in a live Hermes deployment:

1. **Deploy Phase C** — merge `feat/specialists-phase-c` into `main` and redeploy
   the gateway service.  The feature flag defaults to `false`, so no behaviour
   changes on first deploy.

2. **Smoke-test in staging** — set `specialists.enabled: true` in the staging
   `~/.hermes/config.yaml` and verify:
   - Trading queries (e.g., "What is the current stock price of AAPL?") return a
     `[Trading]`-prefixed response with the "🔍 Consulting trading context…"
     indicator.
   - Finance queries (e.g., "Can you review my annual budget?") return a
     `[Finance]`-prefixed response with the "🔍 Consulting finance context…"
     indicator.
   - Unrelated queries (e.g., "Tell me a joke") pass through to the AI agent.

3. **Extend specialists** — add new `BaseSpecialist` subclasses in
   `hermes/specialists/` (following the `TradingSpecialist` / `FinanceSpecialist`
   pattern) and register them in `GatewayRunner._init_specialist_router()`.

4. **Enable in production** — once staging validation passes, set
   `specialists.enabled: true` in the production config and restart the gateway.

5. **Roll back** — to disable, set `specialists.enabled: false` (or remove the
   key entirely) and restart.  No code changes required.

## Adding a New Specialist

1. Create `hermes/specialists/<domain>.py` extending `BaseSpecialist`.
2. Set `name`, `description`, and `keywords` class attributes.
3. Implement `handle(query: str) -> str`.
4. Add the new class to the `specialists` list in
   `GatewayRunner._init_specialist_router()` inside `gateway/run.py`.
5. Add tests under `tests/specialists/test_<domain>.py`.

## Testing

```bash
# Run all specialist tests
pytest tests/specialists/ -v

# Run the full test suite to check for regressions
pytest tests/ -o "addopts=" --ignore=tests/specialists/ -x -q
```
