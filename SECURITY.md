# Security Policy

## Secret Scanning

This repository contains evaluation code for academic research that may interface with API providers. To prevent accidental exposure of API keys, tokens, or other sensitive credentials:

1. **GitHub Secret Scanning** should be enabled on this repository
2. **Pre-commit hooks** with `detect-secrets` are recommended before merging any PRs
3. All `.env` files, API keys, and private credentials must remain in `.gitignore`

## Reporting Security Issues

If you discover a security vulnerability or exposed credential in this repository, please report it privately via GitHub Security Advisories or contact the maintainer directly.

## Safe Development Practices

- Never commit `.env` files or hardcoded API keys
- Use environment variables or secure vaults for credentials
- Run `detect-secrets scan --baseline .secrets.baseline` before committing
- Review all diffs carefully before pushing to public branches
