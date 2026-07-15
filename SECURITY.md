# Security policy

## Supported version

After publication, the latest tagged release is the supported public version. Until then, the release-candidate branch is pre-release material.

## Reporting

Do not place credentials, private vault material, personal data, unpublished research, or exploit details in a public issue. Use the repository host's private vulnerability-reporting channel when available, or contact maintainers through the organization profile.

## Threat boundary

`bvm-lint` reads files and computes hashes. It does not intentionally execute vault-provided code. The fictional tutorial's probe is separate and is executed only by the repository verification script against repository-owned fixtures.

The checker is not a sandbox, malware scanner, secret manager, signature-verification system, or defense against a hostile filesystem. Run it only on content you are permitted to inspect.
