# Release Announcements

This directory contains release announcement content for social media (LinkedIn, X/Twitter).

## Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `feature-highlights.md` | Long-lived feature list (~3k chars) | When major features ship |
| `current-release.md` | Active release announcement | Each release |
| `archive/` | Past announcements | Auto-archived by `/release-prep` |

## Workflow

### Using `/release-prep`

The `/release-prep` skill automates announcement generation:

```
/release-prep v0.1.34
```

This will:
1. Archive `current-release.md` → `archive/v0.1.33.md`
2. Generate new `current-release.md` for v0.1.34
3. Generate CHANGELOG.md draft entry
4. Validate documentation is updated

### Manual Process

If not using the skill:

1. Copy `current-release.md` to `archive/vX.X.X.md`
2. Edit `current-release.md` with new version info
3. Update links after posting to social media

## Posting to Social Media

### LinkedIn (~3000 char limit)

1. Copy content from `current-release.md`
2. Append content from `feature-highlights.md`
3. Post to LinkedIn
4. Update the LinkedIn link in `current-release.md`

### X/Twitter (280 char limit for single tweet)

Use just the first paragraph from `current-release.md`, or create a thread.

## Character Counting

LinkedIn has a ~3000 character limit. The `/release-prep` skill warns if the combined announcement exceeds this.

To check manually:
```bash
wc -m docs/announcements/current-release.md docs/announcements/feature-highlights.md
```
