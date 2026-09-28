#!/bin/sh
# Regenera app/static/css/tailwind.css (reemplaza al CDN de Tailwind). Correr tras cambiar clases Tailwind o tailwind-config.js.
set -e
cd "$(dirname "$0")/.."
T=$(mktemp -d)
cat > "$T/cfg.js" <<EOF
global.tailwind = {}
new Function('tailwind', require('fs').readFileSync('app/static/js/tailwind-config.js', 'utf8'))(global.tailwind)
module.exports = {
  ...global.tailwind.config,
  content: ['app/templates/**/*.html', 'app/static/js/**/*.js'],
  plugins: [require('@tailwindcss/forms'), require('@tailwindcss/container-queries')],
}
EOF
printf '@tailwind base;\n@tailwind components;\n@tailwind utilities;\n' > "$T/in.css"
cd "$T" && npm i --silent tailwindcss@3.4 @tailwindcss/forms @tailwindcss/container-queries
cd - >/dev/null
"$T/node_modules/.bin/tailwindcss" -c "$T/cfg.js" -i "$T/in.css" -o app/static/css/tailwind.css --minify
