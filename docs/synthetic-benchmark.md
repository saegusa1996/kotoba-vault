# Synthetic scale testing

Project evidence should be reproducible without publishing a learner's vault or
statistics. The included generator creates deterministic, non-personal Markdown
notes for smoke tests and local benchmarks.

```bash
python tools/generate_synthetic_vault.py \
  --output synthetic-vault \
  --count 2000

python tools/migrate_word_notes.py \
  --root synthetic-vault \
  --json synthetic-plan.json \
  --fail-on-unresolved
```

The generator refuses to write into a non-empty directory. The resulting notes
contain only numbered aliases, cyclic gojūon initials, and an explicit synthetic
marker. Delete the generated directory after the test.

Timing varies by filesystem and hardware, so the project does not advertise a
single universal throughput number. CI uses the same workflow as a functional
scale smoke test.
