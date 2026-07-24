# Noisy Mono

![Noisy Mono Cover](assets/SocialPreview.png)

A free, open-source monospace typeface with the compact, geometric character of
[Berkeley Mono](https://berkeleygraphics.com/typefaces/berkeley-mono/), built
from a custom [Iosevka](https://github.com/be5invis/Iosevka) configuration.

**[Try the interactive showcase](https://nsyout.github.io/NoisyMono/)** ·
**[Download the latest release](https://github.com/nsyout/NoisyMono/releases/latest)**

## Highlights

- Ten weights, three widths, and matching italics
- A slashed zero by default—no OpenType setting required
- Programming ligatures and distinctive code-focused glyphs
- Desktop, terminal, no-ligature, Nerd Font, and web packages
- Licensed under the SIL Open Font License 1.1

## Comparison

| Noisy Mono | Berkeley Mono |
| --- | --- |
| ![Noisy Mono Sample](assets/NoisyMono.png) | ![Berkeley Mono Sample](assets/BerkeleyMono.png) |

Both images use the same source, canvas, size, Flexoki Dark palette, and macOS
Core Text renderer. They show Noisy Mono Regular v34.4.0 and a locally licensed
Berkeley Mono Regular v2.004 with each font's default OpenType behavior. See the
[render metadata](site/imgs/comparison-provenance.json). No Berkeley font files
are distributed by this repository.

## Download

Start with `NoisyMono.zip` unless you need a specialized variant.

| Package | Use it for |
|---|---|
| `NoisyMono.zip` | Editors, IDEs, and general desktop use |
| `NoisyMono-NerdFont.zip` | Terminals that use Nerd Font icons |
| `NoisyMono-Term.zip` | Strict fixed-width terminals and font pickers |
| `NoisyMono-Term-NerdFont.zip` | Strict terminal spacing plus Nerd Font icons |
| `NoisyMono-NL.zip` | Apps that cannot disable ligatures |
| `NoisyMono-NL-NerdFont.zip` | No ligatures plus Nerd Font icons |
| `NoisyMono-Web.zip` | Curated Latin and technical webfonts |
| `NoisyMono-Web-Full.zip` | The complete Iosevka glyph repertoire for the web |

All desktop archives contain Normal, SemiCondensed, and Condensed widths with
hinted and unhinted TTFs. Start with `Normal/Hinted` on standard-DPI displays
and `Normal/Unhinted` on Retina or other HiDPI displays.

Install the TTFs through Font Book on macOS, **Install for all users** on
Windows, or your local font directory plus `fc-cache -fv` on Linux. Webfont
packaging details live in [`webfonts/README.md`](webfonts/README.md).

## Design

Noisy Mono uses custom metrics and Iosevka character variants for a compact
coding face: a single-storey `g`, flat-arc parentheses, a two-circle `8`, a
slashed `0`, open `6` and `9`, square punctuation dots, and a raised underscore.
The complete configuration is in
[`private-build-plans.toml`](private-build-plans.toml).

## Building from Source

Release builds use the Iosevka version pinned in
[`.github/font-toolchain.json`](.github/font-toolchain.json).

```bash
git clone https://github.com/nsyout/NoisyMono.git
IOSEVKA_TAG="$(jq -r '.iosevka.tag' NoisyMono/.github/font-toolchain.json)"
git clone --branch "$IOSEVKA_TAG" --depth 1 https://github.com/be5invis/Iosevka.git

cp NoisyMono/private-build-plans.toml Iosevka/
cd Iosevka
npm ci
npm run build -- contents::NoisyMono contents::NoisyMonoTerm contents::NoisyMonoNL
```

The generated families are written beneath `Iosevka/dist/`.

## Contributing

Issues and pull requests are welcome. Character design and metrics begin in
[`private-build-plans.toml`](private-build-plans.toml); release and upstream
notes are in [`MAINTAINING.md`](MAINTAINING.md).

## License & Credits

Noisy Mono descends from
[Ioskeley Mono](https://github.com/ahatem/IoskeleyMono) by Ahmed Hatem and is
built with [Iosevka](https://github.com/be5invis/Iosevka) by Renzhi Li
([`be5invis`](https://github.com/be5invis)) and its contributors.

Licensed under the [SIL Open Font License 1.1](./LICENSE). See
[`FONTLOG.txt`](./FONTLOG.txt) for the full copyright lineage and modification
history. No endorsement by Berkeley Graphics, Iosevka, or Ioskeley Mono is
implied.
