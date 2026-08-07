#!/bin/zsh
# Visor del proyecto: sirve la carpeta y abre el navegador.
cd "$(dirname "$0")"
PORT=8000
( sleep 1; open "http://localhost:$PORT" ) &
echo "Visor en http://localhost:$PORT  —  Ctrl+C para cerrar"
python3 -m http.server "$PORT"
