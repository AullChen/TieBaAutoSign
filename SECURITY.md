# Security Policy

## Sensitive credentials

`BDUSS` is authentication material and must be treated as a secret.

Always store credentials in **Settings → Secrets and variables → Actions**. Never commit them to source files, workflow YAML, README content, Issues, pull requests, screenshots, or ordinary environment files.

The application applies basic redaction to configured credentials before writing console or persistent error logs. This reduces accidental disclosure risk, but it is not a substitute for protecting the underlying secret.

## Failure logs

`run.log` is reserved for ERROR/CRITICAL events. Successful runs do not append to it.

If a log entry ever contains information you consider sensitive:

1. Rotate or invalidate the affected credential immediately.
2. Remove the sensitive data from the current repository state.
3. If the repository has ever been shared, consider the credential compromised even after deleting the log.
4. Rewrite Git history only when necessary, because history rewrites change commit SHAs and can disrupt clones and references.

## Reporting a security issue

Do not include real BDUSS values or other credentials in a bug report. Reproduce issues with secrets removed or replaced by placeholders.
