# Security Policy

## Purpose

This is an **educational / portfolio** project demonstrating Data Engineering practices. It is **not intended for production use** with real customer data or sensitive information.

## Supported versions

| Version | Supported |
| --- | :---: |
| `main` | ✅ |
| Other branches/tags | ❌ |

## Reporting a vulnerability

If you discover a security issue:

1. **Do not** open a public GitHub issue with sensitive details.
2. Report it by email: **luisayan100@gmail.com**
3. Include:
   - A clear description of the issue
   - Steps to reproduce (proof-of-concept if available)
   - Affected files/commands and environment details
   - Potential impact and severity (your best estimate)

### Response (best effort)

- Acknowledgment within **72 hours**
- Fix timeline depends on severity and availability (this is a learning project)

## Security considerations

**This project**:
- Uses a public dataset and is intended to run locally
- Should not require secrets by default
- Does not implement authentication or handle user accounts

**If you fork or deploy**:
- Never commit secrets (API keys, tokens, `.env` files)
- Use environment variables or secret managers
- Review dependency vulnerabilities and update regularly
