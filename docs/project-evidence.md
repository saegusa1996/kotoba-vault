# Reproducible project evidence

Kotoba Vault publishes only evidence that another contributor can reproduce
from the repository. No non-public usage statistics or learner content are used
as project metrics.

## Automated validation

- Kana normalization covers hiragana, katakana, dakuten, handakuten, small kana,
  compatibility characters, and array-valued readings.
- Path tests cover segment boundaries, unsafe traversal, and configured roots.
- Migration tests cover dry runs, metadata insertion, unresolved readings,
  existing destinations, and duplicate planned destinations.
- A deterministic synthetic-vault generator supports reproducible scale tests
  without using learner files or private statistics.
- CI runs the JavaScript and Python suites on every push and pull request.
- Release CI rebuilds the installable plugin before publishing assets.

Run the same checks locally:

```bash
pnpm install --frozen-lockfile
pnpm test
pnpm build
python -m unittest discover -s tests -p "test_*.py"
```

Public adoption metrics will be reported only when GitHub and release data make
them independently verifiable.
