# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-04-29

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **Project:** via_stitching
- **KiCad PCM custom repos must be served publicly.** PCM fetches `repository.json` anonymously with no credential support, so a private GitHub repo causes the generic error "The given repository URL does not look like a valid KiCad package repository." Always verify the raw URL with an anonymous fetch (curl / WebFetch / incognito browser) before troubleshooting JSON schema issues — `git ls-remote` succeeds with stored creds and will mislead you.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
