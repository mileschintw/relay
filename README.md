# relay

Lightweight multi-session coordination for Claude Code, built to sit beside [mattpocock-skills](https://github.com/mattpocock/skills).

- `skills/setup`: turn relay on in a repo (`/relay:setup`).
- `skills/coordinate`: the coordinator session (`/relay:coordinate`).
- `skills/work`: what each worker session follows.
- `tools/relay.py`: `status` (a worker's status file) and `ready` (what the coordinator can do next). Tests: `python3 -I tools/tests/test_relay.py`.
- [`GLOSSARY.md`](GLOSSARY.md): the terms.

Install: `/plugin marketplace add <this folder>`, then `/plugin install relay@relay-local`. Start with [docs/getting-started.md](docs/getting-started.md).
