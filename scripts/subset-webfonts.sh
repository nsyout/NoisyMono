#!/usr/bin/env bash
set -euo pipefail

FONTTOOLS_VERSION="${FONTTOOLS_VERSION:-4.63.0}"
UNICODE_RANGES="U+0000-024F,U+0300-036F,U+1E00-1EFF,U+2000-206F,U+2070-209F,U+20A0-20CF,U+2100-214F,U+2150-218F,U+2190-23FF,U+2500-27FF,U+2900-2BFF,U+FB00-FB06,U+FEFF,U+FFFD"

usage() {
  echo "Usage: $0 SOURCE_DIR OUTPUT_DIR" >&2
  echo "Subsets every WOFF2 file in SOURCE_DIR into OUTPUT_DIR." >&2
}

if [[ "$#" -ne 2 ]]; then
  usage
  exit 2
fi

source_dir="$(cd -- "$1" && pwd)"
mkdir -p -- "$2"
output_dir="$(cd -- "$2" && pwd)"

if [[ "${source_dir}" == "${output_dir}" ]]; then
  echo "SOURCE_DIR and OUTPUT_DIR must be different." >&2
  exit 2
fi

if command -v pyftsubset >/dev/null 2>&1; then
  subset_command=(pyftsubset)
elif command -v uvx >/dev/null 2>&1; then
  export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/noisy-mono-uv-cache}"
  export UV_TOOL_DIR="${UV_TOOL_DIR:-${TMPDIR:-/tmp}/noisy-mono-uv-tools}"
  subset_command=(uvx --from "fonttools[woff]==${FONTTOOLS_VERSION}" pyftsubset)
else
  echo "pyftsubset was not found. Install fonttools[woff]==${FONTTOOLS_VERSION} or uv." >&2
  exit 1
fi

shopt -s nullglob
source_fonts=("${source_dir}"/*.woff2)

if [[ "${#source_fonts[@]}" -eq 0 ]]; then
  echo "No WOFF2 files found in ${source_dir}." >&2
  exit 1
fi

before_bytes=0
after_bytes=0

for source_font in "${source_fonts[@]}"; do
  filename="$(basename -- "${source_font}")"
  output_font="${output_dir}/${filename}"
  before_bytes=$((before_bytes + $(wc -c < "${source_font}")))

  "${subset_command[@]}" \
    "${source_font}" \
    --output-file="${output_font}" \
    --unicodes="${UNICODE_RANGES}" \
    --flavor=woff2 \
    --no-hinting \
    --layout-features='*' \
    --name-IDs='*' \
    --name-languages='*'

  after_bytes=$((after_bytes + $(wc -c < "${output_font}")))
done

printf 'Generated %d curated webfonts in %s\n' "${#source_fonts[@]}" "${output_dir}"
printf 'Size: %d bytes -> %d bytes\n' "${before_bytes}" "${after_bytes}"
