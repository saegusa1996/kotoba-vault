# Migration safety

The migration CLI is designed around reviewable plans and fail-closed checks.
It never calls a network service.

## Recommended workflow

1. Back up the target directory.
2. Generate a dry-run report and JSON plan.
3. Review unresolved readings and every destination.
4. Resolve all collisions.
5. Use `--fail-on-unresolved` when partial filing is not acceptable.
6. Apply once, then inspect the result in Obsidian.

```bash
python tools/migrate_word_notes.py \
  --root "/path/to/vault/Japanese/Words" \
  --json migration-plan.json \
  --fail-on-unresolved
```

After review:

```bash
python tools/migrate_word_notes.py \
  --root "/path/to/vault/Japanese/Words" \
  --apply \
  --fail-on-unresolved
```

## Guarantees

- Dry run is the default.
- Existing and case-insensitive destination collisions are reported.
- Duplicate planned destinations stop the entire apply operation.
- Strict unresolved mode stops before the first mutation.
- Metadata writes use an atomic same-directory replacement.
- UTF-8 BOM state and Markdown bodies are preserved.

## Deliberate limitations

- The parser supports the documented simple frontmatter shapes; it is not a
  general YAML implementation.
- The tool does not guess kanji readings or call an online dictionary.
- A filesystem failure after preflight can still leave a partially completed
  multi-file move. Keep a backup until a future transaction journal is added.
