# Data model and config

What the profile looks like, where the local extensions are, and how paths resolve. The
vocabulary is in [`../product/concepts.md`](../product/concepts.md).

## The profile

[JSON Resume](https://jsonresume.org/schema), draft-07. One file, and the only authored one.

Sections read by the renderers: `basics` (with `location` and `profiles`), `work`,
`education`, `skills`, `projects`. Other JSON Resume sections pass through untouched but
unrendered.

```json
{
  "basics": {
    "name": "Jane Smith",
    "label": "Senior Software Engineer | Go · Python",
    "email": "jane@example.com",
    "phone": "(555) 555-0142",
    "location": { "city": "Portland", "region": "OR", "countryCode": "US" },
    "profiles": [{ "network": "GitHub", "url": "https://github.com/janesmith" }],
    "summary": "…"
  },
  "skills": [{ "name": "Languages", "keywords": ["Go", "Python"] }],
  "work": [{
    "name": "Northwind Payments",
    "position": "Senior Software Engineer",
    "location": "Portland, OR (Remote)",
    "startDate": "2021-03",
    "highlights": ["…"]
  }],
  "education": [{ "institution": "…", "studyType": "…", "area": "…", "endDate": "2016-06" }]
}
```

A complete, realistic example is [`../assets/demo-profile.json`](../assets/demo-profile.json) —
the profile every screenshot in these docs renders. It lints clean, which makes it a useful
baseline when a rule fires and you are unsure whether the rule or the content is wrong.

## Validation

Hand-rolled in `model.py`, not run against the published schema — a deliberate limit, recorded
in [`../product/platforms-and-status.md`](../product/platforms-and-status.md).

**Fatal** (`ResumeError`, exit 2): a non-object top level; a missing `basics.name`; a dated
section that is not an array, or whose entries are not objects; a date not matching `YYYY`,
`YYYY-MM` or `YYYY-MM-DD`; an entry ending before it starts; `highlights` that is not an
array.

**Non-fatal** (a note on stderr): an unrecognised top-level section. Reported rather than
ignored, so `experience` instead of `work` surfaces immediately. Keys beginning `_` or `$`
(`_comment`, `$schema`) are the universal "not data" convention and are passed over silently.

Dates are compared as **strings**, which is why the ISO format is enforced rather than
suggested — zero-padded ISO 8601 sorts lexicographically.

## Local extensions

Two fields JSON Resume has no equivalent for. Both are harmless locally; both would be
rejected by the JSON Resume **registry**, which validates against a stricter draft-04 schema
with `additionalProperties: false`. That is one more reason not to use it.

### `work[].note` — stable

A free-text line under a role, rendered in italic. Used for anything the schema cannot say:

```json
{ "note": "Promoted from Software Engineer, December 2025" }
```

### `work[].stints` — experimental

Per-title bullets within one employer, so a promotion shows *which* work was done at which
level:

```json
{
  "name": "Northwind Payments",
  "highlights": ["A bullet spanning the whole tenure."],
  "stints": [
    { "position": "Staff Engineer",  "startDate": "2023-06",
      "highlights": ["Led the platform team of 6."] },
    { "position": "Senior Engineer", "startDate": "2021-03", "endDate": "2023-06",
      "highlights": ["Shipped 14 API endpoints."] }
  ]
}
```

Newest first. Each stint requires `position`; dates and `highlights` are optional.
Employer-level `highlights` remain, for work spanning the whole tenure.

The older **`promotions`** field (prior titles, no bullets) normalises into stints on read, so
existing documents keep rendering. **Carrying both is an error** — two sources for one fact is
the drift worth preventing.

See [`../product/platforms-and-status.md`](../product/platforms-and-status.md) for why this is
experimental and RP-0024 for what would promote it. Also RP-0014: check for an upstream field
before it spreads.

## Configuration

There is no config file. Everything resolves from the environment or the filesystem.

| Variable | Effect |
|---|---|
| `CAREER_DOCS_RESUME` | Absolute path to the profile. Beaten by an explicit CLI argument. |
| `CAREER_DOCS_CHROME` | Path to the browser used for PDF export. Errors if it does not exist rather than falling back silently. |
| `XDG_CACHE_HOME` | Root for generated output. Defaults to `~/.cache`. |

**Profile resolution**, in order: explicit argument → `CAREER_DOCS_RESUME` → the nearest
`resume.json` or `Resume/resume.json` walking up from the working directory.

## Where output goes

| Kind | Location | Lifetime |
|---|---|---|
| **Deliverable** | Beside the profile, as `<Stem>.pdf` / `.html` / `.md` | Overwritten in place; there is exactly one |
| **Catalogue** | `<cache>/catalogue/` | Disposable; rebuild is deterministic |
| **Scratch exports** | `<cache>/` | Disposable |

`<cache>` is `${XDG_CACHE_HOME:-~/.cache}/career-docs/<workspace folder name>`.

**The stem is not always derived.** If a complete trio already exists in the folder,
publishing reuses that name. Otherwise it is `<Lastname>_Resume`. This exists because
publishing under a second convention does not replace a deliverable — it duplicates it.

## The workspace

What `init` writes. Generic; nothing here is anyone's actual resume.

```
CLAUDE.md                        working rules, including anti-fabrication
README.md                        orientation
.claude/skills/career-resume-update/    resume-content skill
.claude/skills/career-layouts-browse/   layout-browsing skill
Resume/resume.json               starter profile
Resume/Archive/                  pre-edit snapshots, YYYYMMDD-description.ext
Cover Letters/                   designed, unbuilt
Applications/                    designed, unbuilt
Reference/
```

`init` never overwrites an existing file and reports what it skipped, so it is safe to re-run
— which is also how `--skill-only` upgrades the skill in a workspace that already exists.
