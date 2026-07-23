# Noisy Mono webfonts

`NoisyMono-Web.zip` contains unhinted WOFF2 fonts curated for typical
Latin-script websites. It retains:

- Latin, Latin Extended, and combining marks
- punctuation, currency, and number forms
- arrows, math, technical, box-drawing, and geometric symbols
- common Latin ligatures
- optional OpenType features such as slashed zero, numeral styles, and
  discretionary ligatures

The archive includes all Noisy Mono weights, styles, and widths plus a
ready-to-use `noisy-mono.css`. The CSS uses `font-stretch` to expose Normal
(`100%`), SemiCondensed (`87.5%`), and Condensed (`75%`) under one family name.

Copy `fonts/` and `noisy-mono.css` to the same public directory, then load
the stylesheet:

```html
<link rel="stylesheet" href="/fonts/noisy-mono.css">
```

```css
body {
  font-family: "Noisy Mono", ui-monospace, monospace;
  font-weight: 400;
  font-stretch: 100%;
}
```

Browsers fall back to the next font for unsupported scripts. Use
`NoisyMono-Web-Full.zip` instead when the complete Iosevka glyph repertoire
is required.

The subsets are generated with a pinned FontTools version:

```bash
./scripts/subset-webfonts.sh path/to/WOFF2-Unhinted path/to/output/fonts
./scripts/generate-webfont-css.py path/to/output/fonts path/to/output/noisy-mono.css
./scripts/validate-webfonts.py path/to/output/fonts
```
