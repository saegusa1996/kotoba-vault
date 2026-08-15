# Security policy

## Supported versions

Security fixes are applied to the latest released version.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could cause data
loss, unsafe path handling, arbitrary file access, or unintended disclosure.
Use GitHub's private vulnerability reporting feature after the public
repository is created. Include a minimal synthetic reproduction and expected
impact; never include a real vault or personal content.

## Security model

Kotoba Vault is local-first and performs no network requests. Its main
risk is unintended file movement, so mutations are restricted to configured
vault paths, destination collisions fail closed, and the migration CLI is a dry
run unless `--apply` is explicitly supplied.
