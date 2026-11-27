import '.just/format/Justfile'
import '.just/lint/Justfile'

mod build '.just/build'
mod test '.just/test'
mod start '.just/start'

[private]
default:
    just --list --list-submodules

# Install Python dependencies
sync:
    @for project in apps/*; do uv sync --project "$project" || exit; done
