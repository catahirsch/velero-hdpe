# Los desafíos — problemas reales del proyecto

Todos salen del desarrollo real del velero (ver `docs/` y `autoadrizante/`).
No son ejercicios inventados: son los conflictos que este proyecto tuvo que
resolver, y el equipo puede atacarlos con cualquier combinación de parámetros
de la plantilla. El evaluador mide el resultado global; estos desafíos son el
mapa de dónde están los puntos.

## D1 — El conflicto central: auto-adrizado en un bote abierto (35 pts auto)

El brief pide un bote ABIERTO de 6 plazas, 750 kg, manga ~2.35 — y
auto-adrizante. El estudio del proyecto demostró que a esa manga el 180°
literal es inalcanzable con plomo (una tonelada llega a 149°) y que sellar el
cockpit mueve el AVS ~1°. La solución de referencia compra los grados con
volumen sellado en altura (mástil sellado + flotador de tope 60 L → vuelve
solo hasta 156°).

**El desafío**: superá la referencia. Palancas disponibles: volumen y altura
del paquete de tope, manga, VCG del lastre, calado, altura de bancos, piso…
Cuidado: cada palanca cobra en otro rubro (una manga angosta pierde porte de
vela y plazas; un flotador enorme castiga el VCG). El evaluador corre la
curva GZ real 0–180° con cockpit inundado — acá no se argumenta, se mide.

## D2 — Autoachique: la cota más justa del barco (10 pts auto)

El piso del cockpit debe quedar sobre la flotación a plena carga (6 tripulantes
+ 500 L = ~1730 kg) para drenar por gravedad al espejo. En la referencia el
margen es +56 mm — la cota más justa de todo el proyecto. Subir el piso ayuda…
y roba profundidad de cockpit y sube el VCG de todo lo que va arriba.

## D3 — Ángulo de inundación (10 pts auto)

Un bote abierto embarca agua cuando la regala se sumerge. El ángulo de
inundación a plena carga de la referencia es 37°. Formas, francobordo y
distribución de pesos lo mueven.

## D4 — Porte de vela sin pasarse (15 pts auto)

SA/D a plena carga en banda 15–18: suficiente vela para las tardes de poco
viento, sin volcar a la primera racha. Jugá con superficie vélica (tope
22 m²), altura de aparejo y estabilidad de formas.

## D5 — El presupuesto de lastre (10 pts auto)

DIS < 750 kg **incluyendo** el lastre: el plomo de quilla es lo que sobra
después de estructura y sistemas. Todo kilo que el diseño gasta en otra cosa
sale de la quilla — y la quilla es lo único que adriza a ángulos chicos.
El evaluador resuelve el remanente con el modelo de pesos real (HDPE doble
piel, eléctrico incluido).

## D6 — El sobre no se negocia (20 pts auto)

LOA < 6.50 · manga < 2.50 (ruta sin permiso) · DIS < 750 · vela < 22 m² ·
lastre de agua < 500 L · calado < 1.30. Cada violación descuenta. El arte es
usar el sobre completo sin pincharlo.

## D7 — Para el jurado: constructibilidad e IA (40 pts jurado)

- ¿El diseño se puede **construir en HDPE**? (nada se pega al PE: soldadura o
  bulón con placa; paneles desarrollables o rotomoldeo; ver docs/04)
- ¿La **bitácora de IA** muestra criterio real? Los mejores puntajes van a
  quienes documentan dónde la IA se equivocó y cómo lo atraparon.
- ¿Hay una idea propia, o solo un barrido de parámetros?

---

### Pistas honestas (las mismas para todos)

- Leé `autoadrizante/opciones.txt` antes de tocar nada: el espacio de opciones
  ya barrido te ahorra semanas.
- El evaluador usa la MISMA física que `calc/autoadrizante.py` — podés
  reproducir cada número localmente y pedirle a tu IA que te explique el
  código. Está pensado para eso.
- Los barridos de parámetros son baratos (~20 s por diseño). Un buen script de
  barrido escrito con ayuda de IA es probablemente tu mejor inversión de la
  semana 2.
