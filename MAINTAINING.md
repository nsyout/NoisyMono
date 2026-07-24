# Maintaining Noisy Mono

This handbook describes what is authoritative, how the repository fits
together, and how to make changes without letting the font packages, showcase,
and documentation drift apart. The release procedure is in
[`RELEASING.md`](RELEASING.md).

## Project invariants

Every change must preserve these unless the change explicitly revises the
product:

- The public families are `Noisy Mono`, `Noisy Mono Term`, and `Noisy Mono NL`.
- Each family has 10 weights, 3 widths, and Upright and Italic styles.
- The slashed zero is the default glyph.
- `Noisy Mono` keeps the complete glyph repertoire and programming ligatures.
- `Noisy Mono Term` uses strict one-cell Fontconfig-compatible spacing.
- `Noisy Mono NL` contains no ligature substitutions.
- Nerd Font packages use Mono patching and fixed-pitch metadata.
- The curated web package contains 60 unhinted WOFF2 faces.
- The showcase uses the curated webfonts from the same pinned Iosevka build as
  the next release.
- No Berkeley Mono font binary is ever committed or distributed.
- `Ioskeley` may appear only in lineage or historical documentation, never in
  generated font metadata.

## Sources of truth

| Concern | Authoritative file |
|---|---|
| Character variants, metrics, families, weights, widths, slopes | [`private-build-plans.toml`](private-build-plans.toml) |
| Iosevka, Nerd Fonts, FontTools, and runtime pins | [`.github/font-toolchain.json`](.github/font-toolchain.json) |
| Release orchestration | [`.github/workflows/build-font.yml`](.github/workflows/build-font.yml) |
| Font normalization, hinting, patching, and packaging | [`scripts/`](scripts) |
| Release archive contract | [`scripts/validate-release.py`](scripts/validate-release.py) |
| Curated web glyph ranges | [`scripts/subset-webfonts.sh`](scripts/subset-webfonts.sh) |
| Generated webfont CSS | [`scripts/generate-webfont-css.py`](scripts/generate-webfont-css.py) |
| Font lineage and copyright | [`FONTLOG.txt`](FONTLOG.txt) |
| User-facing package guidance | [`README.md`](README.md) |
| Showcase implementation | [`site/`](site) |

Do not edit generated fonts or `site/css/fonts.css` by hand.

## Repository map

- `private-build-plans.toml` configures the three Iosevka build plans.
- `scripts/` contains package validation, web subsetting, site synchronization,
  Nerd Font finalization, and comparison rendering.
- `site/` is the static GitHub Pages showcase.
- `assets/` contains images rendered by the README.
- `webfonts/README.md` is included in the curated web archive.
- `.github/workflows/build-font.yml` builds candidates and publishes tagged
  releases.
- `.github/workflows/check-font-dependencies.yml` reports stable dependency
  updates without applying them.
- `.github/workflows/deploy-pages.yml` deploys the tracked `site/` directory.

## Lightweight local checks

Use Python 3 with `fonttools[woff]` installed. The release workflow uses the
exact version in `.github/font-toolchain.json`.

```bash
python3 -m py_compile scripts/*.py
python3 scripts/validate-webfonts.py site/fonts --expected-count 60
python3 scripts/sync-site-webfonts.py --check
node --check site/js/main.js
git diff --check
```

The site-font checks intentionally fail if `site/fonts` has not yet been synced
from the current pinned build.

The accepted release artifact must still be produced by
`.github/workflows/build-font.yml`, so its operating system, pinned runtime,
timestamps, and provenance are consistent. However, any change to the build
plan, dependency pins, font-processing scripts, archive layout, or release
workflow must pass a complete local candidate before consuming Actions time.

## Complete local release preflight

Use an empty temporary work directory and the exact versions in
`.github/font-toolchain.json`. The local machine needs Node.js, Python with the
pinned `fonttools[woff]`, `ttfautohint`, FontForge, `curl`, `jq`, and `zip`.
Download Nerd Fonts' `FontPatcher.zip` at the pinned tag and verify its SHA-256
against the manifest before extracting it.

The local pipeline is the same sequence used by Actions:

1. Clone the pinned Iosevka tag and copy `private-build-plans.toml` into it.
2. Run `npm ci`, then build `ttf-unhinted` for all three families and
   `woff2-unhinted` for Noisy Mono with `--jCmd=2`.
3. Run `scripts/normalize-ttf.py` on all three `TTF-Unhinted` directories.
4. Run `scripts/hint-ttf.py IOSEVKA_ROOT`, then
   `scripts/convert-ttf-to-woff2.py` for Noisy Mono's hinted TTF directory.
5. Run `scripts/validate-build-output.py IOSEVKA_ROOT`. It must report 180
   hinted and unhinted TTF faces and 120 full-glyph WOFF2 faces.
6. Run `scripts/patch-nerd-fonts.py IOSEVKA_ROOT PATCHER OUTPUT_ROOT`, then
   `scripts/finalize-nerd-fonts.py` on the three patched directories.
7. Build the curated web directory with `scripts/subset-webfonts.sh`,
   `scripts/generate-webfont-css.py`, and `scripts/validate-webfonts.py`.
8. Package the curated directory with `scripts/package-directory.py` and the
   other seven archives with `scripts/package-release-archives.py`.
9. Run `scripts/validate-release.py` with the intended version and source SHA,
   write `release-manifest.json` and `SHA256SUMS`, then verify the checksums
   independently.

Do not launch an Actions candidate if any local step fails. The local archives
are diagnostic preflight output, not publishable release assets.

The TrueType normalization step is intentional. Iosevka 34.7.0 emits compact
records for `uni221D` and `infinity` that ttfautohint 1.8.4 rejects as a broken
table. The script forces canonical FontTools encoding and refuses the result
unless glyph order, cmap entries, outlines, and horizontal metrics are
identical. Do not remove this step merely because unhinted fonts open in an
application.

## Changing the font design

1. Change `private-build-plans.toml`.
2. Build all three plans, not only `NoisyMono`.
3. Check all 60 faces per family and both hinted and unhinted desktop output.
4. Run a release candidate through GitHub Actions.
5. Inspect Regular, Italic, and Bold in each width.
6. Test the slashed zero, ambiguous glyphs (`0O`, `1Il`, `gq`), punctuation,
   operators, box drawing, and combining marks.
7. Test default ligatures in Noisy Mono and their absence in Noisy Mono NL.
8. Test Noisy Mono Term in a strict fixed-width picker and Kitty.
9. Sync the candidate webfonts into the showcase.
10. Update `FONTLOG.txt` when the generated font changes.

## Updating pinned dependencies

The weekly dependency workflow reports updates for Iosevka, Nerd Fonts, and
FontTools. Updates are always manual.

1. Update one dependency at a time in `.github/font-toolchain.json`.
2. Confirm the release is stable rather than a prerelease.
3. For Nerd Fonts, download `FontPatcher.zip`, calculate its SHA-256, and
   update `nerdFonts.patcherSha256`.
4. Read upstream release notes for build-plan, naming, metadata, or patcher
   changes.
5. Run a complete candidate; a source parse or one Regular build is
   insufficient.
6. Compare archive counts, font names, metrics, glyph coverage, sizes, and
   rendered specimens with the previous accepted candidate.
7. Sync the accepted curated webfonts into `site/fonts`.
8. Record user-visible changes in `FONTLOG.txt`.

Never combine an Iosevka update with unrelated design changes. Keeping them
separate makes regressions attributable.

## Keeping the showcase aligned

The showcase must use `NoisyMono-Web.zip` from an accepted candidate:

```bash
unzip NoisyMono-Web.zip -d /tmp/noisy-mono-web
python3 scripts/sync-site-webfonts.py \
  --from /tmp/noisy-mono-web/fonts
python3 scripts/sync-site-webfonts.py --check
```

The sync script verifies all 60 faces, checks their embedded version against
the pinned Iosevka tag, replaces `site/fonts`, and regenerates
`site/css/fonts.css`.

The side-by-side images are generated with the tracked Noisy Mono Regular
webfont and a locally licensed Berkeley Mono Regular:

```bash
python3 scripts/generate-comparison-images.py \
  --berkeley /path/to/BerkeleyMono-Regular.ttf
```

The generator writes the two site images, their README copies, and
`site/imgs/comparison-provenance.json`. It does not copy the Berkeley font.

The Flexoki social card is canonical at both `assets/SocialPreview.png` and
`site/imgs/SocialPreview.png`. Keep those files identical.

## Working with upstream history

`origin` is Noisy Mono. `upstream` is Ioskeley Mono and is reference-only:

```bash
git remote -v
git fetch upstream --tags
```

Do not rebase `main` wholesale onto upstream and do not push upstream's tags to
origin. Review upstream commits and port only changes that still apply to Noisy
Mono's families, validation, documentation, and release contract.

Relevant inherited decisions:

- Term spacing and exported glyph names address strict terminal and Kitty
  behavior.
- Nerd Fonts are patched and validated as Mono families.
- The slashed zero is a build default rather than an application setting.
- No variable-font package is advertised because the configured Iosevka build
  does not produce one.
- Curated and full web archives remain separate.

## Licensing and credits

The formal Iosevka copyright line uses “Renzhi Li (Belleve Invis)” because that
is the wording in Iosevka's license. Reader-facing copy uses the current public
identity, Renzhi Li (`be5invis`). Preserve both accurately in their respective
contexts.

All distributed archives must include `LICENSE` and `FONTLOG.txt`.
