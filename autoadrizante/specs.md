# Especificacion — variante auto-adrizante

Velero abierto HDPE 6.48 m, identico al baseline en casco, cockpit, quilla,
aparejo y sistemas, mas el **paquete de flotabilidad de tope de mastil**. La
decision que encierra esta variante: mantener el daysailer abierto y liviano,
y comprar los grados de adrizado que faltan con **volumen sellado en altura**,
no con plomo.

## Dimensiones y pesos

| | |
|---|---|
| LOA / LWL | 6.48 m / 6.30 m |
| Manga | 2.35 m (se mantiene el cockpit de 6 plazas) |
| Calado | 0.30 m quilla arriba — 1.29 m abajo |
| Desplazamiento rosca | 750 kg (tope 750) |
| Quilla (plomo) | 211 kg (28.1 %) |
| Lastre de agua | 2 × 244 L en bancos-tanque — **vacios para la condicion de diseno** |
| Superficie velica | 22.0 m² (mayor 14 + foque 8) |
| Estructura | HDPE doble piel 2×5 mm / 50 mm, 9.5 kg/m² |

## El paquete auto-adrizante (lo unico que cambia)

| Elemento | Especificacion |
|---|---|
| Flotador de tope | 60 L, elipsoide PE rotomoldeado 1.00 × 0.34 m, carenado proa-popa, 2.5 kg con soporte |
| Mastil sellado | 30 L utiles: espuma de cierre en pie, tope y cajeras; drizas externas o en conducto |
| Traba de quilla | obligatoria en posicion BAJA (ya en L4): una orzada no debe retraerla |
| Costo en plomo | el flotador se paga con 2.5 kg de quilla (213 → 211 kg) |

## Resultado de estabilidad (condicion gobernante: rosca, cockpit inundado, tanques vacios)

| | Sin flotador (base) | Con mastil sellado + flotador |
|---|---|---|
| AVS | 110° | GZ sigue positivo mas alla de 110° |
| Limite de recuperacion sin ayuda | 110° | **155.8°** |
| Energia que sostiene la tortuga | 2516 J | 302 J |
| Equilibrio invertido estable | si — el barco queda tortuga | reducido a un bolsillo de 24.2° junto a 180° |

**La afirmacion honesta**: con quilla abajo y trabada y tanques vacios, el
barco vuelve solo desde cualquier escora hasta 156°. El bolsillo
invertido residual (24.2° de ancho, 302 J) no es un
estado de reposo en ninguna mar capaz de dar vuelta el barco: para entrar hay
que atravesar toda la barrera positiva de la curva; para salir alcanza con
24° de perturbacion. A efectos operativos: **anti-tortuga +
retorno autonomo**, y las cinchas de piso quedan como respaldo (y para la
condicion quilla-arriba en playa).

## Condicion de diseno — placa junto a la quilla (grabar)

> AUTO-ADRIZANTE SOLO CON: QUILLA ABAJA Y TRABADA · TANQUES VACIOS
> QUILLA ARRIBA = SOLO BOTADURA / PLAYA · LLENAR TANQUES = VER PLACA DE LASTRE

El lastre de agua queda como sistema de rendimiento (tanque de barlovento con
poca tripulacion), nunca como dependencia de seguridad: la curva verde se
calcula con tanques vacios.

## Lo que esta variante NO cambia

Cockpit 3.20 × 1.72 m de 6 plazas, piso autoachicable (+56 mm a plena carga),
espejo semiabierto, bancos-tanque sellados, cuddy con doble tambucho, aparejo
sin winches 2:1, timon unico abatible, motor electrico con bateria bajo el
piso, remolque sin permiso especial. Desplazamiento rosca sigue en
750 kg.

## Archivos de esta carpeta

| Archivo | Contenido |
|---|---|
| `specs.md` / `cambios.md` | esta especificacion + registro de cambios vs baseline |
| `report.txt` | corrida completa del modelo (pesos, curvas, dimensionado del flotador) |
| `audit.txt` / `costs.txt` | auditoria 22 verificaciones (15 base + 7 del flotador); costos con delta |
| `gz_curves.png` / `hull_lines.png` | curvas GZ con y sin paquete de tope; plano de lineas |
| `boat_autoadrizante.3dm` | modelo Rhino por capas, con flotador de tope |
| `preview_3dm.png` / `preview_cockpit.png` | vistas rapidas del 3DM |
| `hull_autoadrizante.stl` | malla del casco (identica al baseline, m) |
| `offsets_autoadrizante.txt` | tabla de puntos para loftear |
| `planos.pdf` | 8 laminas: las 7 constructivas + L8 flotador y condicion de diseno |
| `selfrighting.gif` + `anim_*.png` | animacion fisica: soltados a 150°, con y sin paquete de tope |
| `foto_*.png` / `diseno_*.png` | el bote en el agua y estudio de color, flotador a la vista |
| `opciones.txt` / `.json` / `opciones_gz.png` / `opciones_board.png` | exploracion ampliada: 8 opciones de auto-adrizado contra notes.txt (insumos de la seccion 4 de la presentacion) |
| `presentacion.pdf` | resumen para el cliente en castellano, con la comparacion de opciones y recomendacion integradas |

Generado por `python3 -m calc.autoadrizante`, `geom.autoadrizante`,
`geom.render_autoadrizante`, `geom.animate_autoadrizante`,
`calc.audit_autoadrizante` y `calc.presentacion_autoadrizante`. Mismas
advertencias que el modelo base: el caso inundado no agrega el peso del agua
atrapada (optimista; cuantificado en docs/03), y el proyecto requiere firma
de ingeniero naval.
