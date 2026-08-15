# Getting started

Kotoba Vault can be used as an Obsidian plugin, a standalone migration CLI, or
both. Start with synthetic notes or a copy of your vault.

## Install the plugin

1. Download `main.js` and `manifest.json` from the latest GitHub release.
2. Create `<vault>/.obsidian/plugins/kotoba-vault/`.
3. Put both files in that directory.
4. Reload Obsidian, enable **Kotoba Vault**, and open its settings.
5. Configure a vocabulary inbox and vocabulary root.

The command palette provides:

- **Preview vocabulary inbox filing** — counts proposed moves without changing
  files.
- **Sort current vocabulary note by reading** — moves the active managed note.
- **Sort all vocabulary notes in inbox** — processes direct inbox children.

## Minimal note

```yaml
---
reading: がっこう
aliases:
  - 学校
---
```

The normalized initial `が` maps to the base gojūon folder `か`.

## Try the CLI safely

```bash
python tools/migrate_word_notes.py --root examples/demo-vault/Words
```

The default is a dry run. Copy the demo directory elsewhere before testing
`--apply`, so the repository stays clean.

Continue with [Migration safety](migration-safety.md) before using real data.
