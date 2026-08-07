"""Genera el PDF de presentacion:  python3 -m calc.presentation

Escribe out/presentacion.pdf -- resumen ejecutivo completo del proyecto, en
castellano, listo para presentar al cliente. Las cifras se citan de los
resultados vigentes en out/ (regenerar la cadena antes de reconstruir el PDF).
"""

from __future__ import annotations

import datetime
import os

from fpdf import FPDF

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

INK = (35, 45, 55)
ACCENT = (40, 90, 130)
RULE = (150, 165, 178)
WARN = (150, 60, 50)
OK = (30, 105, 70)

FECHA = "6 de agosto de 2026"


def tx(s: str) -> str:
    """A latin-1: la fuente base de PDF no cubre todo unicode."""
    repl = {"—": "-", "–": "-", "→": "->", "≥": ">=",
            "≤": "<=", "≈": "~", "×": "x", "’": "'",
            "“": '"', "”": '"', "•": "-", "✓": "si",
            "❌": "NO", "⚠": "!"}
    for a, b in repl.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


class Doc(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(17, 15, 17)
        self.alias_nb_pages()

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("helvetica", "", 8)
        self.set_text_color(*RULE)
        self.cell(0, 6, tx("Velero abierto en HDPE 6.48 m - Resumen de proyecto"),
                  align="L")
        self.cell(0, 6, FECHA, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*RULE)
        self.line(17, 22, 193, 22)
        self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("helvetica", "", 8)
        self.set_text_color(*RULE)
        self.cell(0, 8, tx(f"pagina {self.page_no()} / {{nb}}"), align="C")

    # ---- building blocks -------------------------------------------------

    def mc(self, w, h, txt, align="L"):
        """multi_cell que vuelve al margen izquierdo (fpdf2 >=2.7 se queda a la derecha)."""
        self.multi_cell(w, h, txt, align=align, new_x="LMARGIN", new_y="NEXT")

    def h1(self, s: str):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(*ACCENT)
        self.mc(0, 8, tx(s))
        self.ln(1.5)

    def h2(self, s: str):
        self.ln(1.5)
        self.set_font("helvetica", "B", 11.5)
        self.set_text_color(*ACCENT)
        self.mc(0, 6, tx(s))
        self.ln(0.5)

    def p(self, s: str, size=9.5, style="", color=INK):
        self.set_font("helvetica", style, size)
        self.set_text_color(*color)
        self.mc(0, 4.6, tx(s))
        self.ln(1)

    def bullet(self, s: str, color=INK):
        self.set_font("helvetica", "", 9.5)
        self.set_text_color(*color)
        self.cell(5, 4.6, "-")
        self.multi_cell(0, 4.6, tx(s), new_x="LMARGIN", new_y="NEXT")
        self.ln(0.6)

    def _wrap(self, text: str, width: float) -> list[str]:
        """Corte de linea por ancho real de la fuente activa."""
        words = text.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.get_string_width(trial) <= width - 2.2:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
        return lines or [""]

    def table(self, rows: list[tuple], widths: list[float], header=True,
              size=9.0, aligns=None):
        aligns = aligns or ["L"] * len(widths)
        self.set_draw_color(*RULE)
        line_h = 4.4
        for r_i, row in enumerate(rows):
            bold = header and r_i == 0
            self.set_font("helvetica", "B" if bold else "", size)
            self.set_text_color(*(ACCENT if bold else INK))
            wrapped = [self._wrap(tx(str(c)), widths[i])
                       for i, c in enumerate(row)]
            n_lines = max(len(w) for w in wrapped)
            h = n_lines * line_h + 1.4
            if self.get_y() + h > 281:
                self.add_page()
                self.set_font("helvetica", "B" if bold else "", size)
            x0, y0 = self.get_x(), self.get_y()
            x = x0
            for c_i, lines in enumerate(wrapped):
                for l_i, line in enumerate(lines):
                    self.set_xy(x, y0 + 0.7 + l_i * line_h)
                    self.cell(widths[c_i], line_h, line, align=aligns[c_i])
                x += widths[c_i]
            self.set_xy(x0, y0)
            self.cell(sum(widths), h, "", border="B")
            self.set_xy(x0, y0 + h)
        self.ln(2)

    def img(self, name: str, w: float = 176, caption: str = ""):
        path = os.path.join(OUT, name)
        if not os.path.exists(path):
            self.p(f"[falta {name}]", color=WARN)
            return
        x = (210 - w) / 2
        self.image(path, x=x, w=w)
        if caption:
            self.set_font("helvetica", "I", 8.5)
            self.set_text_color(*RULE)
            self.mc(0, 4.2, tx(caption), align="C")
        self.ln(2)


def build() -> str:
    d = Doc()

    # ---------------- portada ----------------
    d.add_page()
    d.ln(14)
    d.set_font("helvetica", "B", 26)
    d.set_text_color(*ACCENT)
    d.mc(0, 11, tx("Velero abierto en HDPE"), align="C")
    d.set_font("helvetica", "", 15)
    d.set_text_color(*INK)
    d.mc(0, 8, tx("6.48 m - 6 plazas - quilla retractil - electrico"),
                 align="C")
    d.ln(2)
    d.set_font("helvetica", "", 10.5)
    d.mc(0, 5.5, tx(
        "Basado en el RS Aira 22 y el Flow 19 - Resumen de proyecto para presentacion"),
        align="C")
    d.ln(4)
    d.img("preview_3dm.png", w=170)
    d.ln(2)
    d.set_font("helvetica", "", 10)
    d.mc(0, 5.5, tx(f"{FECHA}  -  documento generado desde el modelo de calculo"),
                 align="C")
    d.ln(6)
    d.set_font("helvetica", "I", 9)
    d.set_text_color(*RULE)
    d.mc(0, 5, tx(
        "Documento de ingenieria preliminar. Las cifras provienen del modelo "
        "parametrico del proyecto (hidrostatica, estabilidad, escantillonado, "
        "pesos y costos); no sustituye el proyecto firmado por ingeniero naval "
        "ni la aprobacion de la autoridad maritima."), align="C")

    # ---------------- resumen ejecutivo ----------------
    d.add_page()
    d.h1("1. Resumen ejecutivo")
    d.p("Velero abierto de 6.48 m en polietileno de alta densidad (HDPE), "
        "cockpit autoachicable de 6 plazas, quilla retractil pivotante, timon "
        "unico abatible, auxiliar electrico y 500 L de lastre de agua alojados "
        "dentro de los bancos del cockpit. El diseno cumple 30 de las 33 lineas "
        "de requisitos del cliente (notes.txt); las 3 restantes estan resueltas "
        "como decisiones documentadas, no como omisiones.")
    d.table([
        ("Eslora / manga / calado", "6.48 m / 2.35 m / 0.30 m quilla arriba - 1.29 m abajo"),
        ("Desplazamiento", "750 kg rosca - 1730 kg plena carga (6 tripulantes + 500 L)"),
        ("Lastre", "213 kg plomo (28.4%) + 500 L agua en bancos-tanque"),
        ("Superficie velica", "22.0 m2 (mayor 14 + foque enrollable 8), SA/D 15.5"),
        ("Estructura", "HDPE rotomoldeado doble piel 2x5 mm / 50 mm - 9.5 kg/m2"),
        ("Cumplimiento dimensional", "0 violaciones del sobre LOA/BEA/DIS/SQM/BAL/CBD"),
        ("Cockpit autoachicable", "si: +56 mm de francobordo de piso a plena carga"),
        ("Auto-adrizado desde 180°", "NO en 2.35 m de manga - decision pendiente (seccion 6)"),
        ("Costo Chile (prototipo soldado)", "USD 45-96 mil (medio 64) IVA incluido"),
        ("Auditoria de constructibilidad", "15/15 verificaciones fisicas PASS (calc/audit.py + out/audit.txt)"),
    ], widths=[62, 114], header=False, size=9.0)
    d.h2("Los tres hallazgos que ordenan el proyecto")
    d.bullet("El HDPE no cuesta peso: la doble piel rotomoldeada (346 kg) empata el "
             "casco GRP implicito del Aira (358 kg). Lo que compra el lastre es el "
             "motor electrico (+58 kg). La piel simple NO es viable (23 mm, 710 kg).")
    d.bullet("El sobre de requisitos es la ficha del RS Aira 22 casi textual; ya "
             "codifica estructura GRP y sin motor electrico. Por eso el lastre queda "
             "en 213 kg contra los 250 del Aira.")
    d.bullet("El auto-adrizado verdadero es un problema de manga, no de lastre ni de "
             "cockpit abierto: sellar el cockpit mueve el AVS ~1°; 1000 kg de plomo "
             "llegan a 149°, no a 180°. Lo unico que funciona es angostar el casco.")

    # ---------------- correcciones ----------------
    d.add_page()
    d.h1("2. Correcciones pedidas por el cliente - verificadas")
    d.table([
        ("Pedido", "Estado", "Donde"),
        ("Un timon, no dos", "APLICADO", "Timon unico central abatible, pala mas profunda (0.85 m); 3DM, especificacion, pesos, costos"),
        ("Quilla retractil", "APLICADO", "Quilla pivotante = retractil: 1.28 m abajo / 0.30 m arriba; traba de posicion"),
        ("Tanques = asientos", "APLICADO", "Bancos-tanque sellados piso->asiento (0.385->0.80 m); reserva de flotabilidad"),
        ("Lastre agua 500 L", "APLICADO", "2 x 244 L (488 L, dentro del tope); llenado por cuchara, vaciado por bomba de aire"),
        ("Normativa AR + CL", "APLICADO", "Ordenanza PNA 1-18 y Circulares DIRECTEMAR A-41/014 + O-71/010 (seccion 8)"),
        ("Animacion auto-adrizado", "APLICADO", "out/selfrighting.gif - fisica real sobre las curvas GZ del modelo (seccion 6)"),
    ], widths=[38, 24, 114], size=8.6)
    d.p("Consecuencias absorbidas y recalculadas: el timon unico devuelve 9 kg a la "
        "quilla (204 -> 213 kg); los tanques a la altura del banco invierten el efecto "
        "del lastre de agua sobre el vuelco (llenarlos ahora cuesta ~6° de AVS en vez "
        "de ganar 4°); y el umbral de auto-adrizado subio a ~452 kg de quilla en "
        "1.80 m de manga. Todo el paquete (calculos, planos, 3DM, documentos) esta "
        "regenerado con estos numeros.")

    # ---------------- geometria ----------------
    d.add_page()
    d.h1("3. Casco y disposicion")
    d.p("Casco de codaste duro (dos paneles por banda): es la forma que piden los dos "
        "procesos de HDPE viables - el rotomoldeo necesita desmolde limpio y la "
        "chapa soldada necesita paneles desarrollables. Manga llevada a popa para el "
        "cockpit de 6 plazas y espejo semiabierto; entrada fina en proa.")
    d.img("hull_lines.png", w=150, caption="Plano de lineas: secciones, perfil y planta")
    d.table([
        ("Cockpit", "3.20 x 1.72 m, piso a 0.385 m, autoachicable al espejo"),
        ("Bancos-tanque", "0.42 m de ancho, asiento a 0.80 m; pasillo central 0.88 m"),
        ("Cubierta proa", "plana para tomar sol; cuddy con doble tambucho y estante de tela"),
        ("Timon", "unico, central, abatible, colgado del espejo, cana corta"),
        ("Quilla", "pivotante-retractil en x=3.30 m, bulbo de plomo, aparejo 4:1"),
    ], widths=[40, 136], header=False, size=9.0)

    d.img("preview_cockpit.png", w=150,
          caption="Vista alta del modelo 3DM: bancos-tanque (azul) y timon central")

    # ---------------- diseno ----------------
    d.add_page()
    d.h1("3b. Diseno: color y estilo")
    d.p("En HDPE el color va en la resina (se decide al moldear, no se pinta) y es "
        "pasante: los rayones no se notan. Regla tecnica: cubierta, bancos y piso "
        "siempre CLAROS (el PE oscuro al sol toma 20-30 °C mas -> fluencia y "
        "dilatacion); los costados pueden ser oscuros; el negro/carbono es el PE "
        "mas longevo al UV. Cuatro paletas propuestas y los elementos de estilo "
        "(defensa PE soldada, nombre en bajorrelieve con inlay, franja de "
        "flotacion, antideslizante moldeado, pads EVA en bancos) en docs/09.")
    d.img("diseno_colores.png", w=168, caption="Cuatro paletas sobre el modelo 3D")
    d.img("diseno_perfil.png", w=176,
          caption="Elementos de estilo - todo resuelto en el molde o soldado, nunca pintado")

    # ---------------- el bote en el agua ----------------
    d.add_page()
    d.h1("3c. El bote en el agua")
    d.p("Renders estilizados generados desde el modelo de calculo: el casco flota "
        "en su linea de flotacion real y la escora es la del caso simulado. No son "
        "fotografias; son el modelo verdadero puesto en escena.")
    d.img("foto_patagonia_navegando.png", w=172,
          caption="PATAGONIA navegando: escora 14°, tanque de barlovento lleno, mayor square-top y foque")
    d.img("foto_aira_fondeado.png", w=172,
          caption="AIRA fondeado en calma: flotacion rosca de calculo (0.217 m), bancos-tanque a la vista")

    # ---------------- estructura ----------------
    d.add_page()
    d.h1("4. Estructura HDPE")
    d.p("El resultado central: en HDPE manda la rigidez, no la resistencia. Con el "
        "modulo derrateado por fluencia (250 MPa, no los 1100 de corto plazo), una "
        "piel simple necesitaria 23 mm y pesaria 710 kg: inviable. La respuesta es la "
        "doble piel rotomoldeada - dos pieles de 5 mm separadas 50 mm con uniones "
        "kiss-off - que rinde como 42 mm solidos con 9.5 kg/m2.")
    d.table([
        ("Panel", "Presion", "Requerido", "Provisto", "Margen"),
        ("Fondo", "27.1 kPa", "23.0 mm", "42.2 mm", "1.8x"),
        ("Costado", "21.4 kPa", "21.2 mm", "42.2 mm", "2.0x"),
        ("Cubierta", "7.5 kPa", "17.2 mm", "42.2 mm", "2.5x"),
        ("Piso cockpit", "7.5 kPa", "13.5 mm", "42.2 mm", "3.1x"),
    ], widths=[40, 32, 34, 34, 26], size=9.0,
        aligns=["L", "R", "R", "R", "R"])
    d.p("Prototipo en chapa PE500 soldada: 12 mm sobre refuerzos omega cada 200 mm "
        "(+40 kg). Los paneles desarrollan planos desde el espejo hasta x=4.1 m; la "
        "proa se termoforma o se resuelve en tracas.")
    d.h2("La regla que gobierna cada union")
    d.p("Nada se pega al HDPE. Toda union es soldadura PE-PE o bulon con placa de "
        "respaldo de aluminio y tubos de compresion; el PE fluye bajo carga sostenida "
        "y dilata 10 veces mas que el aluminio (agujeros ovalados en tramos largos). "
        "Los puntos duros (pie de mastil, cadenotes, escota, eje de quilla) terminan "
        "en un esqueleto de aluminio 6082-T6, nunca en el plastico.")
    d.h2("Pesos")
    d.table([
        ("Item", "kg"),
        ("Casco + cubierta HDPE (doble piel)", "346"),
        ("Caja y herrajes de quilla", "22"),
        ("Timon + cana (unico)", "15"),
        ("Mastil + botavara + jarcia", "32"),
        ("Velas + enrollador + lazy bag", "16"),
        ("Herrajes cubierta + aparejos 2:1", "19"),
        ("Motor electrico + bateria 3 kWh", "58"),
        ("Capota + carpa + fondeo + seguridad", "29"),
        ("Quilla (plomo, el remanente)", "213"),
        ("ROSCA (con lastre)", "750"),
    ], widths=[130, 46], size=8.8, aligns=["L", "R"])

    # ---------------- estabilidad ----------------
    d.add_page()
    d.h1("5. Estabilidad y porte de vela")
    d.img("gz_curves.png", w=168, caption="Curvas GZ 0-180°, intactas e inundadas, rosca y plena carga")
    d.table([
        ("Condicion", "GZmax", "AVS", "Auto-adriza"),
        ("Rosca, cockpit inundado", "0.667 m @ 46°", "112°", "no"),
        ("Plena carga (6 trip + 500 L), inundado", "0.38 m @ 34°", "85°", "no"),
    ], widths=[76, 38, 30, 32], size=9.0)
    d.bullet("Cockpit autoachicable verificado: piso +168 mm sobre flotacion en rosca, "
             "+56 mm a plena carga (1730 kg). Es el numero mas justo del barco: "
             "tolerancia de construccion +10/-0 mm.")
    d.bullet("Porte de vela: 17° de escora con 20 nudos reales (12° con tanque de "
             "barlovento lleno); momento adrizante maximo a 28 nudos; primer rizo ~18 nudos.")
    d.bullet("Angulo de inundacion 37° a plena carga - el numero para entrenar a la "
             "tripulacion en un barco abierto.")
    d.h2("Regla operativa del lastre de agua (para placa junto a las valvulas)")
    d.bullet("Tripulacion completa (5-6): tanques VACIOS - la tripulacion es el lastre; "
             "con tanques llenos el AVS cargado cae a ~85°.")
    d.bullet("1-3 tripulantes: tanque de BARLOVENTO lleno = ~2 tripulantes en la borda "
             "(250 kg a 0.65 m).")
    d.bullet("Llenado simetrico: solo a motor o en mar de popa con poca gente - a la "
             "altura del banco, llenar ambos cuesta ~6° de AVS.")

    # ---------------- autoadrizado ----------------
    d.add_page()
    d.h1("6. Auto-adrizado: la decision pendiente")
    d.p("El requisito 'auto-adrizante' desde 180° NO se cumple con 2.35 m de manga, y "
        "no es un problema de esfuerzo sino de fisica: la misma estabilidad de forma "
        "que sostiene 6 personas y 22 m2 de vela hace al casco estable boca abajo. "
        "Sellar el cockpit mueve el AVS ~1°. Una tonelada de plomo llega a 149°.")
    d.img("trade_frontier.png", w=168,
          caption="Frontera: lastre minimo para auto-adrizar segun manga - y AVS vs lastre a 2.35 m")
    d.table([
        ("Manga", "Lastre necesario", "Desplazamiento"),
        ("1.75 m", "417 kg", "~954 kg"),
        ("1.80 m", "452 kg", "~988 kg"),
        ("2.00 m", "842 kg", "~1379 kg"),
        ("2.35 m (diseno)", "no alcanzable < 1400 kg", "-"),
    ], widths=[46, 66, 64], size=9.0)
    d.h2("Las dos resoluciones honestas")
    d.bullet("OPCION A - flotador de tope de mastil (45-60 L, ~2.5 kg): hace inalcanzable "
             "los 180°; el barco queda a ~112° y la tripulacion lo adriza con las cinchas "
             "de piso ya previstas. No cambia nada mas del proyecto. No es auto-adrizado "
             "literal: es anti-tortuga + adrizado por tripulacion.", color=OK)
    d.bullet("OPCION B - variante angosta 1.80 m con 452 kg de quilla (~988 kg): "
             "auto-adriza de verdad. Pierde las 6 plazas en linea (4 comodas), supera el "
             "tope de 750 kg y el remolque necesita frenos. Ya esta modelada y exportada "
             "(hull_selfrighting.stl / boat_selfrighting.3dm).", color=OK)

    d.add_page()
    d.h2("La animacion (out/selfrighting.gif) - fisica real del modelo")
    d.p("Ambos botes soltados invertidos a 178°, barco rosca con cockpit inundado "
        "(la condicion honesta despues de un vuelco). El base se asienta tortuga; la "
        "variante angosta pasa por vertical a los ~7 s y queda parada. Los puntos "
        "sobre las curvas GZ siguen a cada bote: la diferencia es el signo de GZ "
        "cerca de 180°, no la quilla en si.")
    d.img("anim_inicio.png", w=158, caption="t=0.2 s: ambos invertidos")
    d.img("anim_medio.png", w=158, caption="t=7.4 s: la variante ya paso por vertical; el base sigue tortuga")
    d.img("anim_final.png", w=158, caption="t=22 s: estado final - la manga decide")

    # ---------------- normativa ----------------
    d.add_page()
    d.h1("7. Normativa: Argentina y Chile")
    d.p("Los dos sistemas regulan distinto y eso ordena el plan: Argentina regula la "
        "CONSTRUCCION (proyecto firmado y aprobado antes de cortar material); Chile "
        "regula el BARCO TERMINADO (inspeccion local, prueba de balance, equipamiento). "
        "Disenar el papeleo para Argentina y el equipamiento para Chile satisface ambos.")
    d.table([
        ("", "Argentina (PNA)", "Chile (DIRECTEMAR)"),
        ("Antes de construir", "Proyecto + Encomienda de profesional CPIN; aprobacion PNA (Ord. 1-18)", "Barco abierto <12 m: croquis + 4 fotos ante la SCLINM (O-71/010)"),
        ("Estabilidad", "Memoria de calculo en el proyecto", "Prueba de periodo de balance en el agua"),
        ("Registro", "REJU / REY", "Capitania de Puerto + Cert. de Navegabilidad (6 anos)"),
        ("Patron", "Timonel de Yate a Vela", "Licencia deportiva segun clase"),
        ("Equipamiento", "Anexo A Ord. 1-18 por zona; ancla 7 kg + 12 mm + cadena 6 mm", "Anexo A Circ. A-41/014 por clase (bahia / costera 12-60 MN)"),
    ], widths=[30, 73, 73], size=8.2)
    d.h2("Dos puntos de friccion detectados en la norma")
    d.bullet("Chile exige lastre 'de instalacion permanente' (A-41/014 II.K.1): los "
             "tanques soldados integrales son defendibles, pero conviene acordarlo POR "
             "ESCRITO con la Capitania antes de construir. Plan B: tanques sellados "
             "permanentes de 120 kg.", color=WARN)
    d.bullet("La mayor no enrollable debe rizar >=40% del gratil (A-41/014 II.M): "
             "resuelto con 2 fajas de rizos en la especificacion.", color=OK)
    d.bullet("ISO 12215-5 no tiene via para PE rotomoldeado: la certificacion ISO es "
             "equivalencia + ensayos, no un checklist. AR/CL no exigen ISO.", color=WARN)

    # ---------------- costos ----------------
    d.add_page()
    d.h1("8. Costos de construccion en Chile")
    d.p("Bandas de planificacion 2026 (BAJO / MEDIO / ALTO), IVA 19% incluido, "
        "importados +15% flete y 0% arancel (TLC). Modelo parametrico en calc/costs.py: "
        "reemplazar las bandas por cotizaciones reales y recalcular.")
    d.table([
        ("", "Bajo", "Medio", "Alto"),
        ("RUTA A - chapa PE500 soldada, unidad unica", "", "", ""),
        ("  Materiales + componentes", "29,800", "41,400", "57,800"),
        ("  Mano de obra (650-1000 h)", "10,800", "17,100", "29,800"),
        ("  Contingencia 10%", "4,100", "5,900", "8,800"),
        ("  TOTAL USD", "44,700", "64,400", "96,300"),
        ("  TOTAL CLP (millones)", "42", "61", "91"),
        ("RUTA B - rotomoldeo, por barco en serie de 20", "", "", ""),
        ("  TOTAL USD", "43,800", "63,600", "94,900"),
    ], widths=[86, 30, 30, 30], size=8.8, aligns=["L", "R", "R", "R"])
    d.bullet("El casco no es el costo: la chapa PE es ~5% del total. El bloque mayor es "
             "el tren electrico (~USD 9,900, 24% de materiales), despues aparejo + velas.")
    d.bullet("En serie de 20, rotomoldeo empata a la chapa soldada (la amortizacion del "
             "molde cancela el ahorro de mano de obra). Para UN barco: chapa soldada; "
             "un molde de USD 60-130 mil no se carga a una unidad.")
    d.bullet("Chile es buen lugar para soldar PE: la industria salmonera ya forma "
             "soldadores y hay astilleros de HDPE en Puerto Montt/Chiloe. La cotizacion "
             "mas valiosa: casco a precio fijo de un fabricante acuicola.")
    d.p("No incluye: remolque, amarra, honorarios de ingeniero naval en Argentina "
        "(USD 2,500-6,000, solo para matricula argentina), certificado de vela, flete.")

    # ---------------- proximos pasos ----------------
    d.h1("9. Proximos pasos")
    d.table([
        ("#", "Accion", "Quien"),
        ("1", "Decidir auto-adrizado: Opcion A (flotador) u Opcion B (variante 1.80 m) - antes de cualquier molde", "Cliente"),
        ("2", "Consulta escrita a la Capitania (CL) por el lastre de agua 'permanente'", "Cliente / proyecto"),
        ("3", "Cotizar casco soldado con 2 fabricantes PE (Santiago y Puerto Montt) con la especificacion seccion 2-3", "Proyecto"),
        ("4", "Cotizar tren electrico: dealer chileno vs importacion directa", "Proyecto"),
        ("5", "Si va matricula argentina: contratar ingeniero naval (CPIN) y presentar proyecto a PNA", "Cliente"),
        ("6", "Construir prototipo -> prueba de balance (valida el modelo y el certificado chileno)", "Astillero"),
    ], widths=[8, 138, 30], size=8.6)
    d.p("Paquete tecnico completo en el repositorio: requisitos, especificacion de "
        "construccion con dimensiones y materiales, estudio de auto-adrizado, "
        "normativa con fuentes primarias, matriz de cumplimiento (30/33) y modelo de "
        "costos - mas planos de formas, STL, 3DM por capas y la animacion.",
        style="I")

    path = os.path.join(OUT, "presentacion.pdf")
    d.output(path)
    return path


if __name__ == "__main__":
    p = build()
    print(f"escrito: {p}  ({os.path.getsize(p) / 1e6:.1f} MB)")
