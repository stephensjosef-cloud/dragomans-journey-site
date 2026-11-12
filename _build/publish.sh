#!/bin/sh
# Makes dist/: exactly the public site, for Cloudflare (T-15, Nov 12, 2026).
#   sh _build/publish.sh
# dist/ holds every git-tracked file outside _build/, except CNAME,
# wrangler.jsonc, and anything whose name (or a folder in its path) starts
# with a dot or an underscore. Plus one file of its own, dist/_redirects,
# with the line "/ /index.html 200": wrangler.jsonc sets html_handling to
# "none" so /local.html stays /local.html, and that line lets "/" still find
# index.html. Cloudflare reads _redirects and never serves it.
# Short addresses (answer from Josef, Nov 12, 2026: keep them working):
# GitHub Pages also answers /local for /local.html, so _redirects gets one
# line per page, "/local /local.html 200". The lines come from the
# git-tracked .html files at the root, so a new page gets its line on its
# own. index.html is left out (the "/" line covers it), and so is 404.html.
# A 200 line serves the page at the short address; it does not redirect.
# Fails loudly if dist/ would be empty or if anything from _build/ lands in it.
set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"
rm -rf dist
mkdir dist

git -c core.quotepath=off ls-files | while IFS= read -r f; do
  case "/$f" in
    /_build/*) continue ;;              # the build sources, never served
    /CNAME | /wrangler.jsonc) continue ;;
    */.* | */_*) continue ;;            # dot and underscore names, anywhere in the path
  esac
  mkdir -p "dist/$(dirname "$f")"
  cp "$f" "dist/$f"
done

n=$(find dist -type f | wc -l | tr -d ' ')
if [ "$n" -eq 0 ]; then
  echo "publish.sh: dist/ is empty, nothing to publish" >&2
  exit 1
fi
if [ -e dist/_build ] || find dist -name '_build*' | grep -q .; then
  echo "publish.sh: something from _build/ landed in dist/" >&2
  exit 1
fi
if [ ! -f dist/index.html ] || [ ! -f dist/404.html ]; then
  echo "publish.sh: dist/ has no index.html or 404.html" >&2
  exit 1
fi

printf '/ /index.html 200\n' > dist/_redirects
pages=0
root_pages=$(git -c core.quotepath=off ls-files -- '*.html' | grep -v / || true)
while IFS= read -r f; do
  case "$f" in
    '' | index.html | 404.html) continue ;;
  esac
  [ -f "dist/$f" ] || continue          # only pages that are published
  printf '/%s /%s 200\n' "${f%.html}" "$f" >> dist/_redirects
  pages=$((pages + 1))
done <<EOF
$root_pages
EOF

echo "publish.sh: $n files in dist/, plus dist/_redirects ($pages short addresses)"
