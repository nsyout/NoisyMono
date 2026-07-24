# Releasing Noisy Mono

Noisy Mono uses Semantic Versioning for this repository's design, packaging,
and compatibility contract. That version is independent of Iosevka's embedded
font version.

- Stable: `v1.0.0`, `v1.0.1`, `v1.1.0`
- Candidate: `v1.0.0-rc.1`

Do not reuse or push inherited Ioskeley Mono tags.

## What the release workflows do

The release is deliberately split so an accepted font build is never repeated:

- `Build Release Candidate` is a manual workflow that builds and validates a
  private Actions artifact. It creates no tag and no GitHub Release.
- `Publish Validated Release` runs when a valid `vX.Y.Z` tag is pushed. It
  locates the unexpired successful candidate for the exact tagged commit and
  version, verifies its checksums, reruns the 720-font release validator, and
  publishes those same files. It does not rebuild Iosevka or patch fonts again.

Every successful run preserves:

- Eight advertised ZIP archives
- `SHA256SUMS`
- `release-manifest.json`, containing the source commit, pinned toolchain,
  archive sizes, hashes, font counts, embedded versions, and PostScript-name
  counts

The validator rejects missing or extra archives, unsafe ZIP paths, unexpected
files, incomplete face matrices, stale family names, missing glyphs, incorrect
ligature behavior, invalid fixed-pitch metadata, and incorrect package layouts.

## Release gate

Do not tag a release until all of these are true:

- `main` is clean and pushed.
- The dependency pins represent deliberately accepted stable versions.
- A candidate from the exact intended source commit completed successfully.
- All eight archives passed `scripts/validate-release.py`.
- `SHA256SUMS` verifies after downloading the candidate.
- Regular, Italic, and Bold were visually checked in all three widths.
- Standard, Term, NL, and Nerd Font behavior was tested in representative apps.
- The candidate's curated webfonts were synced into `site/fonts`.
- `scripts/sync-site-webfonts.py --check` passes.
- The comparison images and their provenance reflect the tracked Regular
  webfont.
- `README.md`, `FONTLOG.txt`, and package guidance describe the candidate.
- There are no known release-blocking regressions.

## 1. Build a candidate

First run the complete local release preflight in
[`MAINTAINING.md`](MAINTAINING.md). It must produce all eight archives and end
with:

```text
Release candidate v1.0.0 is structurally valid (720 fonts)
```

Verify the generated `SHA256SUMS` locally. These archives are diagnostic and
must not be uploaded as the release.

Only after local preflight passes, run the workflow from GitHub's Actions page,
or with the CLI:

```bash
gh workflow run build-font.yml \
  --ref main \
  -f version=v1.0.0
```

Watch the run:

```bash
gh run list --workflow build-font.yml --limit 1
gh run watch RUN_ID --exit-status
```

The manual run does not reserve the version. It is safe to repeat after fixes.

The release archives of record must come from the pinned Ubuntu workflow.
Local preflight exists to catch deterministic source, hinting, patching, and
packaging failures before CI. `Build font` is the longest step and the compact
`gh run watch` view does not show its live compiler output. A long period
without a step transition is therefore not evidence that the job is stuck.
Iosevka concurrency and Nerd Font patching are deliberately bounded, and the
job has a four-hour timeout for genuine runaways.

## 2. Download and verify it

```bash
mkdir -p /tmp/noisy-mono-candidate
gh run download RUN_ID \
  --name NoisyMono-v1.0.0-candidate \
  --dir /tmp/noisy-mono-candidate

cd /tmp/noisy-mono-candidate
shasum -a 256 -c SHA256SUMS
jq . release-manifest.json
```

Confirm that `release-manifest.json` names the intended commit and current
toolchain. Inspect every archive's top-level layout and install fonts only from
this candidate during testing.

## 3. Test the candidate

At minimum:

1. Install Normal Regular, Italic, and Bold.
2. Confirm the family and styles appear correctly on macOS, Windows, or Linux.
3. Test `0O 1Il gq {}[]()`, combining accents, arrows, and box drawing.
4. Confirm default ligatures in Noisy Mono.
5. Confirm the same source stays unligated in Noisy Mono NL.
6. Confirm Noisy Mono Term is accepted by strict fixed-width pickers.
7. Test one Nerd Font archive in a terminal with icons.
8. Load `noisy-mono.css` from the curated web archive in a browser.
9. Confirm all three web widths and all ten weights select real faces rather
   than browser-synthesized styles.

Record any failure before changing the source. A source fix requires a new
candidate run.

## 4. Sync the showcase

Extract the accepted curated web archive and sync it:

```bash
unzip NoisyMono-Web.zip -d /tmp/noisy-mono-web
python3 scripts/sync-site-webfonts.py \
  --from /tmp/noisy-mono-web/fonts
python3 scripts/sync-site-webfonts.py --check
```

Regenerate the comparison images when Noisy Mono Regular changes:

```bash
python3 scripts/generate-comparison-images.py \
  --berkeley /path/to/BerkeleyMono-Regular.ttf
```

Commit the synchronized site and provenance, then run one final candidate from
that commit. That final run is the release candidate of record.

## 5. Publish

After explicit approval, create an annotated tag on the exact accepted commit:

```bash
git switch main
git pull --ff-only
git status --short
git tag -a v1.0.0 ACCEPTED_COMMIT_SHA -m "Noisy Mono v1.0.0"
git push origin v1.0.0
```

The lightweight publication workflow must find the accepted candidate from the
exact tagged commit. Candidate artifacts are retained for 14 days, so publish
before the accepted artifact expires. Stable tags become the latest release;
hyphenated versions are marked prerelease.

Never move or reuse a pushed release tag.

## 6. Verify publication

After the tag workflow succeeds:

1. Open the GitHub Release and confirm all ten assets are present.
2. Download the published assets and re-run `shasum -a 256 -c SHA256SUMS`.
3. Confirm `/releases/latest` resolves to the stable version.
4. Test the README and showcase download links.
5. Install one published desktop archive on a clean profile or machine.
6. Confirm GitHub Pages completed successfully for the release commit.

## Failure and recovery

- If a candidate fails, fix the source and rerun the same candidate version.
- Reproduce the failure and pass the complete local preflight before starting
  another Actions run.
- In a failed Iosevka build, find the first real error in the log. The many
  subsequent `Build ... is cancelled` messages are parallel tasks unwinding,
  not separate root causes.
- A ttfautohint `0x08` or `broken table` error is not a concurrency symptom.
  Confirm that normalization ran and test the exact failing face with its
  `.ttfa.txt` control file.
- If publication cannot find an unexpired candidate and the source is
  unchanged, build a new candidate for the tagged commit and version, then
  rerun the failed publication workflow. Do not rebuild merely because the
  publication job itself had a transient failure.
- If code must change after a tag was pushed, do not move the tag. Use the next
  prerelease or patch version.
- If a bad public release exists, document the problem immediately and publish
  a corrected patch release. Do not silently replace assets under the same
  version.
- If only the showcase is broken, revert or fix the site commit; do not rebuild
  font archives unless their contents were affected.
