# Maintaining Noisy Mono

## Remotes

Keep Noisy Mono as `origin` and the original Ioskeley Mono repository as
fetch-only `upstream`:

```bash
git remote add origin https://github.com/nsyout/NoisyMono.git
git remote add upstream https://github.com/ahatem/IoskeleyMono.git
git remote set-url --push upstream DISABLED
git fetch upstream --tags
git rebase upstream/main
```

Review upstream changes before rebasing when a release is in progress. Never
move an existing release tag; publish a new semantic version after rebuilding
and checking the archives.

## Font toolchain updates

`.github/font-toolchain.json` is the source of truth for the stable Iosevka,
Nerd Fonts, and FontTools versions used by the release workflow. The Nerd Fonts
patcher is also pinned by SHA-256 because release assets can be replaced without
changing their download URL.

The `Check Stable Font Dependencies` workflow runs weekly and can be dispatched
manually. It compares the pinned Iosevka and Nerd Fonts tags with GitHub's latest
non-prerelease releases. When an update exists, it opens or refreshes a single
issue in this repository; it never creates or updates anything upstream. GitHub
Issues must be enabled on the fork.

Do not update these dependencies automatically. For each update:

1. Change one pinned dependency at a time.
2. Update the Nerd Fonts patcher checksum when its tag changes.
3. Run the complete build and validation workflow.
4. Compare archive contents, font names, glyph coverage, metrics, and sizes with
   the previous release.
5. Close the dependency issue only after the updated artifacts are accepted.

## Releases

The release workflow builds all desktop, terminal, Nerd Font, no-ligature, and
web variants. A version tag publishes a release; a manual run creates a draft.

Before tagging:

1. Review `private-build-plans.toml` and the generated specimen site.
2. Run the webfont subsetter against an Iosevka build and inspect its size
   report.
3. Confirm the default web archive contains curated, unhinted fonts and CSS.
4. Confirm the `Web-Full` archive still contains the complete glyph builds.
5. Confirm every archive contains `LICENSE` and `FONTLOG.txt`.
6. Test Regular, Italic, and Bold in a browser, including arrows, box drawing,
   ligatures, slashed zero, numeral styles, and Latin Extended characters.
7. Confirm every Nerd Font has one nonzero advance width, fixed-pitch `post`
   metadata, and monospaced Panose metadata.
8. Test the Term family in Kitty and confirm it appears in a Fontconfig
   `:mono` query.

## Local decisions informed by upstream reports (2026-07-23)

These links are reference material only. Maintenance happens in this fork; do
not update upstream issues or pull requests as part of the local workflow.

- [Issue #18](https://github.com/ahatem/IoskeleyMono/issues/18): the Term plan
  exports glyph names for Kitty ligatures.
- [Issue #19](https://github.com/ahatem/IoskeleyMono/issues/19): the Term plan
  uses strict Fontconfig-compatible spacing, and Nerd Fonts are patched and
  validated as Mono families.
- [Issue #20](https://github.com/ahatem/IoskeleyMono/issues/20): the existing
  OpenType `zero` feature is documented instead of adding another build.
- [Issue #21](https://github.com/ahatem/IoskeleyMono/issues/21): variable fonts
  are not adopted because Iosevka does not support that output.
- [Issue #22](https://github.com/ahatem/IoskeleyMono/issues/22): curated
  Latin/technical subsets preserve all applicable OpenType layout features;
  the full-glyph web archive remains available separately.
- [PR #23](https://github.com/ahatem/IoskeleyMono/pull/23): the
  quasi-proportional families are not adopted because they do not implement a
  variable font and substantially expand the release matrix.
- [Issue #2](https://github.com/ahatem/IoskeleyMono/issues/2), Homebrew and
  winget: revisit after the fork has a stable release URL and version history.
