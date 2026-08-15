# Contributing

Thank you for helping improve Japanese language-learning workflows in
Obsidian.

## Before opening a change

1. Search existing issues and discussions.
2. Use only synthetic notes or text you have permission to share.
3. Never attach a real user vault, commercial ebook, full subtitle file, audio,
   video, account token, or personal path.
4. Keep transformations deterministic and dry-run-first.

## Development

Install the pinned development dependencies, then run:

```bash
pnpm install --frozen-lockfile
pnpm test
pnpm build:production
python -m unittest discover -s tests -p "test_*.py"
```

Commit the generated `main.js`; CI verifies that it matches the production
bundle.

For plugin changes, also test in a temporary Obsidian vault with synthetic
notes. Verify collision handling, link updates, and plugin unload/reload.

## Pull requests

- Explain the learner or maintainer problem.
- Add a regression test for text-processing changes.
- Document any file mutation and its recovery path.
- Keep unrelated formatting out of the change.
- Confirm that no copyrighted or personal content is included.
