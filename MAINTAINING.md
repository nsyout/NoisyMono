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
| Release archive construction | [`.github/workflows/build-font.yml`](.github/workflows/build-font.yml) |
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

Local font builds are optional and are not release artifacts. They are useful
when a design change needs a short feedback loop, but the accepted candidate
must be produced by `.github/workflows/build-font.yml` so its operating system,
toolchain, timestamps, validation, and provenance are consistent. Iosevka
command concurrency is deliberately capped in CI because each command job can
consume more than 1 GiB at peak.

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
