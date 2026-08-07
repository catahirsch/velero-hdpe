# Diseño y estilo — colores, terminaciones y detalles

Renders en `out/diseno_colores.png` (4 paletas), `out/diseno_perfil.png`
(elementos de estilo numerados) y **escenas en el agua** en
`out/foto_patagonia_navegando.png` / `out/foto_aira_fondeado.png` — el modelo
real flotando en su línea de flotación de cálculo, con velas y escora
(`python3 -m geom.render_scene`). Regenerables con `python3 -m geom.render_ideas`.

La restricción que ordena todo: **en HDPE el color va en la resina** (masterbatch
al momento de moldear). No hay pintura ni gelcoat — nada adhiere al PE — así que
el esquema de color es una decisión *previa al molde*, y a cambio el color es
pasante: los rayones y el uso no se notan como en gelcoat.

---

## 1. Las tres reglas técnicas del color en PE

1. **Cubierta, bancos y piso siempre claros.** El PE oscuro al sol toma 20–30 °C
   más que el claro; en un material que fluye con la temperatura eso significa
   más dilatación, más creep en herrajes, y quemarse al sentarse. Los costados
   pueden ser oscuros (verticales, menos insolación).
2. **El negro/carbono es el PE más longevo al UV** — por eso los kayaks de
   expedición son oscuros. Un casco grafito con cubierta clara es la combinación
   más durable.
3. **Blanco/claro es el más estable dimensionalmente** — si la prioridad es
   minimizar movimiento térmico (tolerancias de herrajes), la base clara gana.

## 2. Cuatro paletas propuestas (render en `diseno_colores.png`)

| Paleta | Costados | Franja | Cubierta | Bancos | Carácter |
|---|---|---|---|---|---|
| **PATAGONIA** | grafito | naranja | gris claro | naranja | máxima vida UV, no muestra el uso, acentos de alta visibilidad SAR |
| **CHILOÉ** | petróleo | crema | crema | pads "teca" | clásico de canal, esconde algas en la franja |
| **AIRA** | blanco roto | azul | gris perla | azul | el más fresco al sol, look astillero |
| **ARENA** | arena | oliva | crema | oliva | discreto en fondeaderos australes |

Recomendación: **PATAGONIA** para uso intensivo/alquiler (durabilidad + no
muestra uso), **AIRA** para clima cálido o si mandan las tolerancias.

## 3. Elementos de estilo (perfil numerado en `diseno_perfil.png`)

1. **Defensa perimetral de PE soldada** en la borda — perfil D extruido, soldado
   sobre el cordón casco-cubierta: lo protege, remata la línea y es el "trim"
   natural del material.
2. **Nombre en bajorrelieve ruteado + inlay de soldadura** en color de contraste
   — el rótulo que no se despega nunca. (El vinilo sobre PE requiere flameado y
   dura poco; evitarlo.)
3. **Franja de flotación en color de acento** — esconde la zona que se ensucia
   y estiliza el perfil bajo.
4. **Matrícula grabada** en amuras + nombre en aletas + puerto en espejo — la
   exigencia CL/AR (A-41/014 II.E) resuelta con el mismo grabado del punto 2.
5. **Apéndices en gris oscuro** (quilla, timón galvanizado pintado no — el acero
   va galvanizado y puede llevar recubrimiento epoxi sobre el galvanizado).
6. **Antideslizante moldeado** — textura guijarro/diamante EN el molde para
   cubierta, tapas de banco y piso. Sin pinturas antideslizantes (no adhieren).

## 4. Confort y detalles de cockpit

- **Pads EVA tipo teca en las tapas de banco** (el look madera de la paleta
  CHILOÉ): se fijan con pernos de PE soldados por debajo o botones a presión
  pasantes — nunca adhesivo. Aíslan térmicamente el asiento (resuelve el PE
  caliente/frío) y son el "cushion" que no se vuela.
- **Respaldo bajo continuo**: la brazola de la cubierta lateral, redondeada en
  el molde a r ≥ 40 mm.
- **Estiba**: el volumen de banco sobre el nivel de llenado (0.57→0.80 m) queda
  utilizable como estiba seca por las tapas registro — bolsos estancos.
- **Cuddy**: estante de tela (notes línea 20) + bolsillos de red en las paredes;
  los dos tambuchos dan luz y ventilación.
- **Bañera nocturna**: la carpa sobre la botavara a 1.80 m da altura de asiento
  en todo el cockpit — 3.2 m de "camarote" de lona.
- **Piso**: listón 1"×1" soldado (notes línea 47) en el eje + textura moldeada.

## 5. Lo que NO hacer en PE (anti-ideas)

- Pintar o gelcoatear cualquier superficie — se despega, siempre.
- Vinilos grandes — flameado + vida corta; solo aceptable para numerales de
  regata temporales.
- Herrajes "decorativos" atornillados al PE sin placa — fluencia y pérdida.
- Teca real atornillada — dilatación diferencial 10× la arranca; EVA o PE
  texturado.
- Colores oscuros en superficies horizontales — regla 1.

## 6. Cómo se pide esto en producción

Rotomoldeo: el masterbatch define **un** color por pieza moldeada. El esquema
multicolor se logra por: (a) casco y cubierta moldeados por separado en colores
distintos (ya son dos piezas), (b) franja y defensa como perfiles PE soldados en
color de acento, (c) tapas de banco moldeadas aparte (color 3), (d) inlays de
soldadura para gráfica. En chapa (prototipo): cada plancha PE500 viene de color
de fábrica — el esquema se arma por despiece, con la misma lógica.
