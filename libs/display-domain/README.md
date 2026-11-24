# display-domain

Models individual displays and their settings. The caller supplies stable identities.

Each domain module in `src/display_domain` contains `domain` and `application` modules.
Application code may depend on domain code; domain code may not depend on application code.
Application layers may not import other application layers.
Import Linter checks these boundaries as part of `just lint`.

Run tasks from the repo root:

- `just lint`

The task definitions live in `.moon/tasks/python.yml`.
