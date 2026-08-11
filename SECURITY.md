# Security Policy

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for security-sensitive findings. Do not open a public issue containing an exploit, credential, private document, or personally identifiable information.

For ordinary bugs that do not expose sensitive information, use the repository's bug-report template.

## Document safety

- Treat source documents and extracted text as untrusted input.
- Run the skill only on files you are authorized to access.
- Review optional third-party converters before installing them.
- Keep preparation output outside repositories that may be published.
- Do not upload confidential fixtures to issues or pull requests.
- The project does not bypass DRM or silently invoke online OCR services.

Security fixes target the latest release and the `main` branch.
