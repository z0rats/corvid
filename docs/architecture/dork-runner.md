# Dork Runner

Deep-dive referenced from AGENTS.md. User-facing description: `website/src/content/docs/features/dork-runner.md`.

Runs a static library of parameterized dork templates (`site:`, `filetype:`, `intext:`, ...) against
a domain, username, or email. Ephemeral like `domain_finder` and `youtube`: nothing is persisted and
there is no history.

## Pieces

- `config/dork_templates.py` - the template library (a `DorkTemplate` per entry: `key`, a `pattern` with a `{target}`
  placeholder, the `target_types` it applies to, and a `description`). `GET /api/dork-runner/templates` lists them.
- `config/search_engines_config.py` - engine URLs and pacing constants: `REQUEST_DELAY_SECONDS`,
  `MAX_RETRIES`/`RETRY_DELAY`, `REQUEST_TIMEOUT`, `MAX_QUERIES_PER_RUN` (12, a hard cap regardless of
  how many templates are requested) and `MAX_RESULTS_PER_QUERY`.
- `service/dork_query_service.py` - `perform_dork_run` resolves the requested templates and runs the
  queries; `POST /api/dork-runner/run`.
- `service/engines/` - one module per engine behind `base.py`'s interface (`duckduckgo_engine.py`,
  `google_engine.py`, `bing_engine.py`).

## Behavior worth knowing

- **DuckDuckGo's HTML endpoint is the default engine.** Google and Bing block scripted queries
  almost immediately; both are still selectable but best-effort, since they CAPTCHA/block quickly.
  A failing query doesn't abort the run: its error is collected into the response's `errors` list
  and the remaining queries still run.
- **Queries run sequentially, never in parallel**, with `REQUEST_DELAY_SECONDS` between them - each
  one is a real outbound request, and a burst is what gets an IP blocked.
- The engines' hosts are fixed; user input only ever lands in the query string.
