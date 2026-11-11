# Workspace

Your own work. Everything here except this file is ignored by git: source
documents and decks may be confidential, so they never enter the repository.

| Folder | Holds |
|--------|-------|
| `projects/` | Decks in progress. `project_manager.py init` creates new projects here |
| `archive/` | Finished decks you no longer touch, and experiment runs |
| `inbox/` | Raw source documents (PDF, DOCX, …) waiting to become a project |

```bash
uv run python3 scripts/project_manager.py init <project_name> --format ppt169
uv run python3 scripts/project_manager.py import-sources workspace/projects/<project> workspace/inbox/<file>.pdf
```

`import-sources` copies files from `inbox/`; pass `--move` to move them instead.
A project folder holds `sources/`, `design_spec.md`, `templates/`, `images/`,
`svg_output/`, `svg_final/`, `notes/` and the exported `.pptx`.

When a deck is done, move its folder from `projects/` to `archive/`.
