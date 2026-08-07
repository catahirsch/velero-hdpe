# Cambios: baseline → variante auto-adrizante

Registro de todo lo que cambia entre el proyecto base (`out/`, `docs/`) y esta
variante, y de lo que expresamente NO cambia. Decision del cliente
(2026-08-07): mantener el daysailer abierto y liviano, y resolver el
auto-adrizado con volumen sellado en altura en vez de plomo — la "Opcion A"
de `docs/03`, ahora **modelada en la fisica** en lugar de estimada.

## 1. Hardware (3 items nuevos, 1 reclasificado)

| # | Cambio | Baseline | Variante |
|---|--------|----------|----------|
| 1 | **Flotador de tope** | no tiene | elipsoide PE 60 L, 1.00 × 0.34 m, carenado proa-popa, 2.5 kg con soporte (placa 6082-T6, 4× M6 A4), desmontable |
| 2 | **Mastil sellado** | perfil abierto | espuma de cierre en pie, tope y cajeras; drizas externas o en conducto; 30 L utiles que tambien cuentan como flotabilidad |
| 3 | **Traba de quilla** | prevista en L4 como buena practica | **item de seguridad primaria**: la afirmacion auto-adrizante supone la quilla abajo Y trabada a 120°+ de escora |
| 4 | Cinchas de piso + liston (notes 46-47) | mecanismo principal de adrizado | respaldo, y para la condicion quilla-arriba en playa |

## 2. Pesos

| Item | Baseline | Variante |
|---|---|---|
| Quilla (plomo, remanente del tope 750) | 213.0 kg | **210.5 kg** (paga el flotador) |
| Flotador de tope (z = 9.55 m) | — | +2.5 kg |
| Desplazamiento rosca | 750 kg | 750 kg (sin cambio) |
| VCG rosca | 0.256 m | 0.287 m (+31 mm — **cargado en las curvas**) |

## 3. Resultado de estabilidad (rosca, cockpit inundado, tanques vacios)

| | Baseline | Variante |
|---|---|---|
| AVS | 110° | GZ sigue positivo mas alla de 110° (salto a GZ ≈ 1.0 m al sumergirse el aparejo, ~93°) |
| Limite de recuperacion autonoma | 110° | **156°** |
| Equilibrio invertido | estable — queda tortuga | bolsillo residual 156–180°, 8× mas superficial |
| Energia que sostiene la tortuga | 2516 J | **302 J**, detras de una barrera de 2633 J |
| Veredicto operativo | NO auto-adrizante | **anti-tortuga + retorno autonomo hasta 156°** |

La afirmacion NO es "auto-adrizante desde 180.0° matematicos" (eso solo lo
cumple la variante angosta de 1.80 m, que rompe el brief). Es el barco del
brief con el vuelco resuelto y los numeros a la vista.

## 4. Condicion de diseno y operacion (nuevo)

- **Placa nueva junto a la caja de quilla**: AUTO-ADRIZANTE SOLO CON QUILLA
  ABAJO Y TRABADA · TANQUES VACIOS. QUILLA ARRIBA = SOLO BOTADURA / PLAYA.
- El **lastre de agua queda reclasificado**: de sistema mixto a sistema de
  rendimiento puro (tanque de barlovento con poca tripulacion). La curva
  auto-adrizante se calcula con tanques vacios: la seguridad nunca depende de
  llenarlos.
- Angulo de inundacion (37° a plena carga) y regla operativa del lastre (L7):
  sin cambios.

## 5. Modelo de calculo (nuevo modulo)

`calc/autoadrizante.py`: el aparejo sellado entra a la hidrostatica como
elementos de volumen a lo largo del palo + flotador; la flotacion se
re-resuelve por angulo (el casco flota mas alto con el aparejo sumergido).
Corrige la afirmacion de `docs/03` de que "el flotador no aparece en una
curva GZ". Mismo tratamiento del cockpit inundado que el base, con la misma
advertencia (no agrega el peso del agua atrapada: optimista).

## 6. Costos

Delta de la variante: **USD 240–760** (~0.5 % del costo medio USD 64,400).
Detalle en `costs.txt`.

## 7. Lo que NO cambia

Casco (2.35 m, formas, offsets identicos), cockpit 6 plazas, piso
autoachicable (+56 mm a plena carga), bancos-tanque 2×244 L, cuddy y
tambuchos, quilla pivotante 1.29 m, timon unico abatible, aparejo 22 m² sin
winches, motor electrico + bateria bajo el piso, estructura HDPE doble piel,
sobre dimensional (0 violaciones), remolque < 750 kg sin frenos.

## 8. Equivalencia de salidas (out/ → autoadrizante/)

| out/ (baseline) | autoadrizante/ (variante) | Cambio |
|---|---|---|
| report.txt | report.txt | reporte de la variante: pesos con flotador, curvas, dimensionado, condiciones |
| gz_curves.png | gz_curves.png | curvas con y sin paquete de tope |
| hull_lines.png | hull_lines.png | identico en formas (casco sin cambios) |
| hull/offsets/boat baseline | hull/offsets/boat autoadrizante | 3DM agrega capa `flotador-tope` |
| planos.pdf (7 laminas) | planos.pdf (**8 laminas**) | + L8: flotador, mastil sellado, placa |
| preview_3dm / preview_cockpit | idem | regenerados del 3DM de la variante |
| foto_patagonia / foto_aira | idem | encuadre mas alto: el flotador en cuadro |
| diseno_colores / diseno_perfil | idem | regenerados (estilo sin cambios) |
| selfrighting.gif + anim_*.png | idem | **nueva fisica**: soltados a 150°, con/sin paquete de tope (antes: base vs casco angosto 1.80 m) |
| audit.txt (15 checks) | audit.txt (**22 checks**) | + 7 verificaciones del paquete de tope |
| costs.txt | costs.txt | + delta de la variante |
| presentacion.pdf (12 pag.) | presentacion.pdf | presentacion propia de la variante |
| trade_study/options/trade_frontier | **opciones.txt / opciones.json / opciones_gz.png / opciones_board.png** | exploracion NUEVA sobre el espacio que abre el modelo con aparejo: 8 opciones (mastil sellado solo, flotador 60/80 L, bolsa inflable 150 L, tanques bajo el piso solos y combinados, casco angosto) medidas contra notes.txt; la comparacion, matriz y recomendacion van integradas en la **seccion 4 de presentacion.pdf** |

## Regeneracion

```bash
python3 -m calc.autoadrizante             # fisica: report, gz_curves, specs
python3 -m geom.autoadrizante             # stl, offsets, 3dm, planos, perfil
python3 -m geom.render_autoadrizante     # lines, previews, fotos, diseno
python3 -m geom.animate_autoadrizante    # gif + frames
python3 -m calc.audit_autoadrizante      # audit + costs
python3 -m calc.opciones_autoadrizante   # exploracion de opciones (txt/json/png)
python3 -m calc.presentacion_autoadrizante   # incluye la comparacion de opciones
```
