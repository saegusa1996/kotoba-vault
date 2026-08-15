# Architecture

## Data flow

```text
Obsidian metadata event
        |
        v
configured path check
        |
        v
reading normalization ----> unresolved: no mutation
        |
        v
gojūon destination
        |
        +----> collision: fail closed
        |
        v
Obsidian fileManager.renameFile
```

The plugin deliberately uses explicit metadata rather than guessing a kanji
reading. This keeps live behavior deterministic. The migration CLI may recover
existing readings from conservative, reviewable sources, but it reports
unresolved notes instead of fabricating values.

## Performance boundaries

- Metadata events are debounced by file path.
- Startup resolves the configured inbox folder directly and checks only its
  direct children; it does not enumerate every Markdown file in the vault.
- Existing notes already inside gojūon folders are not scanned on startup.
- No global index, background network request, or continuous polling is used.

## Mutation safety

- All destination paths are rooted in the configured vocabulary directory.
- Existing destinations are never overwritten.
- The CLI previews by default and stops before all writes if it detects a
  collision, including two planned notes targeting the same path.
- Strict mode also stops before all writes when any reading is unresolved.
- Metadata is replaced atomically in the source directory; UTF-8 BOM state and
  note bodies are preserved.
