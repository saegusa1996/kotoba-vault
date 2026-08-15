# Compatibility

## Obsidian plugin

- Minimum Obsidian version: 1.5.0
- Desktop and mobile: supported by the manifest
- Network access: none
- Telemetry: none
- External runtime dependencies after build: none

The release `main.js` is a bundled CommonJS file. Obsidian itself remains an
external runtime dependency, as required for community plugins.

## Migration CLI

- Python 3.10 or later
- Standard library only
- UTF-8 and UTF-8 with BOM
- Windows, macOS, and Linux path layouts

## Frontmatter shapes

The migration CLI supports scalar `reading`, list-style `aliases`, and simple
top-level keys. Complex YAML anchors, folded scalars, and nested mappings are
left for a future schema-aware parser.
