# Repository guidance

- Preserve local-first behavior; do not add telemetry or network calls without
  an explicit design review.
- Never commit real vault content, commercial books, audio, video, or complete
  third-party subtitles. Use synthetic fixtures.
- Keep bulk operations dry-run-first and collision-safe.
- Add regression tests for kana normalization, path handling, and frontmatter
  changes.
- Run both JavaScript and Python test suites before completing a change.
