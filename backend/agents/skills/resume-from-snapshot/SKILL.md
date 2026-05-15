---
name: resume-from-snapshot
description: Build or refine a resume using the current shared resume state snapshot as the authoritative source.
---

# Resume From Snapshot

## When to use this skill

Use this skill when the user asks to:
- create a resume
- draft a resume
- refine or improve an existing resume draft
- generate resume LaTeX or PDF

The key requirement is to use the current shared state snapshot as the source of truth.

## Snapshot-first workflow

1. Read the current shared snapshot state already available to the agent.
2. Use these sections when present:
   - `profile`
   - `summary`
   - `skills`
   - `projects`
   - `experiences`
   - `achievements`
   - `educations`
3. Start from `references/ATS_RESUME_STRUCTURE.md` as the canonical LaTeX baseline, then fill it with snapshot data.
4. If the user asks for a generated PDF, prepare final LaTeX and call `generate_resume_pdf`.

## Missing-data rules

- Do not invent user-specific facts.
- If a required section is missing for the requested output, ask a targeted follow-up question for only the missing section.
- Prefer concise follow-ups such as:
  - "Please share your target role for the resume headline."
  - "Please share 2-3 measurable achievements for your latest role."

## Output behavior

- Keep structure clean and ATS-friendly.
- Prioritize recent and relevant experience.
- Keep bullets impact-focused when data allows.
- Respect user constraints on role, tone, length, and format.
- While filling LaTeX template fields, escape user data for LaTeX special characters (especially `#` as `\#` and `&` as `\&`).

## References

Use `references/ATS_RESUME_STRUCTURE.md` as the primary ATS LaTeX template and adapt placeholders using snapshot data.
