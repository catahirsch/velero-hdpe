"""PDF de presentacion de la variante auto-adrizante.

    python3 -m calc.presentacion_autoadrizante  ->  autoadrizante/presentacion.pdf

Reutiliza el maquetador de calc/presentation.py; las cifras provienen de la
corrida vigente de calc/autoadrizante.py (autoadrizante/report.txt). Regenerar
esa cadena antes de reconstruir el PDF.
"""

from __future__ import annotations

import json
import os

from .autoadrizante import DIR
from .presentation import ACCENT, INK, OK, RULE, WARN, Doc, tx

OUT_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")

FECHA = "7 de agosto de 2026"


class SRDoc(Doc):
    """Mismo maquetador, otra carpeta de imagenes y otro encabezado."""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("helvetica", "", 8)
        self.set_text_color(*RULE)
        self.cell(0, 6, tx("Velero abierto HDPE 6.48 m - VARIANTE AUTO-ADRIZANTE"),
                  align="L")
        self.cell(0, 6, FECHA, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*RULE)
        self.line(17, 22, 193, 22)
        self.ln(4)

    def img(self, name: str, w: float = 176, caption: str = ""):
        # primero la carpeta de la variante; si no, out/ (casco identico)
        path = os.path.join(DIR, name)
        if not os.path.exists(path):
            path = os.path.join(OUT_BASE, name)
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
    d = SRDoc()

    # ---------------- portada ----------------
    d.add_page()
    d.ln(10)
    d.set_font("helvetica", "B", 24)
    d.set_text_color(*ACCENT)
    d.mc(0, 10, tx("Variante auto-adrizante"), align="C")
    d.set_font("helvetica", "", 14)
    d.set_text_color(*INK)
    d.mc(0, 8, tx("Velero abierto HDPE 6.48 m - 6 plazas - 750 kg - quilla retractil"),
         align="C")
    d.ln(2)
    d.set_font("helvetica", "", 10.5)
    d.mc(0, 5.5, tx(
        "El mismo barco abierto y liviano del proyecto base, mas el paquete de "
        "flotabilidad de tope de mastil - la 'Opcion A' del estudio de "
        "auto-adrizado, ahora modelada en la fisica, no estimada."), align="C")
    d.ln(3)
    d.img("perfil_flotador.png", w=105)
    d.ln(1)
    d.set_font("helvetica", "", 10)
    d.mc(0, 5.5, tx(f"{FECHA}  -  documento generado desde el modelo de calculo"),
         align="C")
    d.ln(3)
    d.set_font("helvetica", "I", 9)
    d.set_text_color(*RULE)
    d.mc(0, 5, tx(
        "Documento de ingenieria preliminar; no sustituye el proyecto firmado "
        "por ingeniero naval ni la aprobacion de la autoridad maritima."),
        align="C")

    # ---------------- la decision ----------------
    d.add_page()
    d.h1("1. La decision que encierra esta variante")
    d.p("El estudio de auto-adrizado (docs/03) dejo una disyuntiva: el "
        "auto-adrizado literal desde 180° exige angostar el casco a 1.80 m y "
        "~450 kg de quilla (~990 kg), perdiendo las 6 plazas y el tope de "
        "750 kg - deja de ser el barco del brief. La alternativa es conservar "
        "el daysailer abierto y comprar los grados que faltan con GEOMETRIA "
        "(volumen sellado colocado en altura) en vez de plomo.")
    d.p("Esta variante toma ese camino y lo lleva hasta el final: el volumen "
        "sellado mas barato y mas alto disponible es el propio aparejo. Un "
        "mastil sellado y un flotador de tope de 60 L trabajan al final de "
        "una palanca de 9.5 m - el mismo momento adrizante que ~270 kg de "
        "plomo en el bulbo, por 2.5 kg en altura.")
    d.h2("Que cambia respecto del proyecto base (y que no)")
    d.table([
        ("Elemento", "Variante auto-adrizante"),
        ("Flotador de tope", "60 L, elipsoide PE 1.00 x 0.34 m carenado, 2.5 kg, desmontable"),
        ("Mastil", "sellado: espuma en pie/tope/cajeras, drizas externas o en conducto (30 L utiles)"),
        ("Traba de quilla", "obligatoria navegando (ya prevista en L4): la curva supone quilla abajo Y trabada"),
        ("Condicion de diseno", "quilla abajo y trabada, TANQUES VACIOS - el lastre de agua queda como opcion de rendimiento, nunca dependencia de seguridad"),
        ("Quilla (plomo)", "210 kg: el flotador se paga con 2.5 kg del remanente"),
        ("Todo lo demas", "SIN CAMBIOS: casco 2.35 m, cockpit 6 plazas, 750 kg, piso autoachicable, bancos-tanque, timon unico, electrico, sin winches"),
    ], widths=[42, 134], size=8.8)

    # ---------------- la fisica ----------------
    d.add_page()
    d.h1("2. La fisica: el flotador SI entra a la curva GZ")
    d.p("El estudio base descarto el flotador con una frase ('no aparece en "
        "una curva GZ'). Es incorrecto: un volumen sellado en el tope es "
        "flotabilidad como cualquier otra. Al sumergirse el aparejo (escora "
        "~75° en adelante) desplaza agua exactamente en el rango donde la "
        "curva del casco desnudo se hace negativa. calc/autoadrizante.py "
        "re-resuelve la flotacion en cada angulo incluyendo casco, quilla y "
        "aparejo sellado - el casco ademas flota MAS ALTO con el aparejo "
        "sumergido, lo que debilita por si solo el equilibrio invertido.")
    d.img("gz_curves.png", w=170,
          caption="La curva verde es el mismo barco con mastil sellado + 60 L en el tope; tanques vacios")
    d.table([
        ("Condicion gobernante: rosca, cockpit inundado", "Sin flotador", "Con paquete de tope"),
        ("GZ maximo", "0.64 m @ 46°", "1.03 m @ ~90°"),
        ("Limite de recuperacion autonoma", "110°", "156°"),
        ("Energia que sostiene la tortuga", "2516 J", "302 J"),
        ("Barrera de energia que protege ese bolsillo", "-", "2633 J"),
    ], widths=[80, 46, 50], size=8.8)

    d.h2("La afirmacion honesta")
    d.p("Con quilla abajo y trabada y tanques vacios, el barco vuelve solo "
        "desde cualquier escora hasta 156°. Queda un bolsillo invertido "
        "teorico de 24° junto a 180°, 8 veces mas superficial que el del "
        "casco desnudo y protegido por una barrera de 2633 J: para quedar "
        "tortuga, la mar tiene que empujar el barco a traves de TODA la "
        "barrera; para soltarlo alcanza una perturbacion de 24°. En cualquier "
        "agua capaz de dar vuelta este barco, ese bolsillo no es un estado de "
        "reposo. Operativamente: anti-tortuga + retorno autonomo. Las cinchas "
        "de piso del brief quedan como respaldo y para la condicion "
        "quilla-arriba en playa.")
    d.bullet("No es 'auto-adrizante desde 180.0°' en el sentido matematico - esa "
             "afirmacion solo la cumple la variante angosta de 1.80 m. Es el barco "
             "del brief, con el vuelco resuelto por otra via, y con los numeros a la "
             "vista.", color=WARN)

    # ---------------- animacion ----------------
    d.add_page()
    d.h1("2b. La animacion (selfrighting.gif) - fisica real del modelo")
    d.p("El MISMO casco de 2.35 m soltado tumbado a 150° - mas alla de la "
        "vertical, mastil bien hundido - en las dos configuraciones, rosca con "
        "cockpit inundado y tanques vacios. Sin el paquete de tope, GZ ya es "
        "negativo a 150° y el casco sigue rodando hasta asentarse tortuga; con "
        "mastil sellado + 60 L el aparejo empuja el barco de vuelta y termina "
        "adrizado. Los puntos sobre las curvas GZ siguen a cada bote.")
    d.img("anim_inicio.png", w=150, caption="t=0.2 s: ambos tumbados a 150°, mastil sumergido")
    d.img("anim_medio.png", w=150, caption="t=7.4 s: el desnudo ya es tortuga (180°); la variante pasa por 5°")
    d.img("anim_final.png", w=150, caption="t=22 s: estado final - el paquete de tope decide")

    # ---------------- dimensionado ----------------
    d.add_page()
    d.h1("3. Dimensionado del flotador y condiciones")
    d.h2("Por que 60 litros")
    d.table([
        ("Flotador", "Recuperacion autonoma hasta", "Energia del bolsillo"),
        ("0 L (solo mastil sellado, 30 L)", "123°", "1627 J"),
        ("20 L", "138°", "941 J"),
        ("40 L", "148°", "534 J"),
        ("60 L  <- elegido", "156°", "291 J"),
        ("80 L", "162°", "153 J"),
    ], widths=[70, 60, 46], size=8.8)
    d.bullet("Por debajo de ~40 L el flotador no sostiene el peso del aparejo "
             "sumergido con margen; 60 L da 1.7x y cuesta 2.5 kg.")
    d.bullet("Mas alla de 80 L el limite casi no se mueve: el bolsillo residual "
             "esta atrapado contra 180° por simetria, no por falta de flotador.")
    d.h2("Otras condiciones verificadas")
    d.bullet("Plena carga (6 tripulantes + 500 L), inundado, con flotador: limite "
             "de recuperacion 124° (el caso gobernante sigue siendo rosca: la "
             "tripulacion en el agua no ayuda).")
    d.bullet("Angulo de inundacion a plena carga: 37° - sin cambios; el numero "
             "para entrenar a la tripulacion sigue siendo ese.")
    d.bullet("Quilla ARRIBA: NO auto-adrizante en ninguna variante. Quilla arriba "
             "= solo botadura y playa, y asi lo dice la placa.", color=WARN)
    d.h2("Placa junto a la caja de quilla (grabar)")
    d.p("AUTO-ADRIZANTE SOLO CON: QUILLA ABAJO Y TRABADA - TANQUES VACIOS.  "
        "QUILLA ARRIBA = SOLO BOTADURA / PLAYA.  LASTRE DE AGUA: VER PLACA DE "
        "LASTRE (rendimiento, nunca seguridad).", style="B", color=WARN)

    # ---------------- opciones evaluadas ----------------
    with open(os.path.join(DIR, "opciones.json")) as f:
        R = json.load(f)

    def hasta(k):
        return "180.0°" if R[k]["true_180"] else f"{R[k]['rec_limit']:.0f}°"

    def pocket(k):
        return f"{R[k]['pocket_j']:.0f} J"

    d.add_page()
    d.h1("4. Las opciones sobre la mesa - por que esta y no otra")
    d.p("Antes de fijar el paquete de tope se barrio todo lo que se puede "
        "hacer SIN tocar el casco de 6 plazas (mas la referencia angosta de "
        "docs/03), con el volumen sellado del aparejo dentro de la "
        "hidrostatica. Cada opcion se mide en la condicion honesta post-vuelco "
        "- rosca, cockpit inundado - con tres numeros: hasta que escora "
        "vuelve solo, cuanta energia sostiene la tortuga residual (0 J = "
        "auto-adriza desde 180.0°), y cuantas lineas de notes.txt sobreviven.")
    d.img("opciones_board.png", w=176,
          caption="Las seis configuraciones evaluadas; detalle numerico completo en opciones.txt")
    d.table([
        ("", "Opcion", "Vuelve solo hasta", "Tortuga residual"),
        ("BASE", "casco desnudo (el problema)", hasta("BASE"), pocket("BASE")),
        ("A1", "mastil sellado solo (30 L, +0 kg)", hasta("A1"), pocket("A1")),
        ("A2", "sellado + flotador rigido 60 L - ELEGIDA", hasta("A2"), pocket("A2")),
        ("A3", "sellado + flotador rigido 80 L", hasta("A3"), pocket("A3")),
        ("B", "bolsa inflable de tope 150 L (disparada)", hasta("B"), pocket("B")),
        ("C0", "tanques bajo el piso llenos, sin tope", hasta("C0"), pocket("C0")),
        ("C", "tanques bajo el piso + flotador 60 L", hasta("C"), pocket("C")),
        ("D", "casco angosto 1.80 m / 500 kg (referencia)", hasta("D"), pocket("D")),
    ], widths=[14, 92, 38, 32], size=8.8)

    d.add_page()
    d.h2("Las curvas que ordenan la decision")
    d.img("opciones_gz.png", w=172)
    d.h2("Lectura, opcion por opcion")
    d.bullet(f"A1 - sellar el mastil es gratis (espuma y prolijidad, ~USD 150) y "
             f"ya compra {R['A1']['rec_limit'] - R['BASE']['rec_limit']:.0f}° "
             "sobre el casco desnudo. Se hace en CUALQUIER escenario.", color=OK)
    d.bullet(f"A2 - la elegida: pasiva, 2.5 kg, USD 240-760 total. Vuelve sola "
             f"hasta {hasta('A2')} y deja la tortuga en {pocket('A2')} detras "
             "de una barrera de ~2600 J. Es el paquete especificado, auditado "
             "(22/22) y dibujado (L8) en este documento.", color=OK)
    d.bullet(f"A3 - 20 L mas compran ~6° (hasta {hasta('A3')}). Rendimiento "
             "decreciente: el bolsillo residual esta atrapado contra 180° por "
             "simetria, no por falta de litros.")
    d.bullet(f"B - la unica via al 180.0° LITERAL sin tocar el casco "
             f"({pocket('B')} de tortuga). El costo no es dinero (USD 800-1500): "
             "es que deja de ser pasivo - disparo hidrostatico, botella de CO2, "
             "rearme tras cada uso, inspeccion anual. Camino de upgrade sobre "
             "A2 si la certificacion exige el literal.", color=WARN)
    d.bullet(f"C0 - el mecanismo RNLI solo (tanques bajos llenos) NO alcanza a "
             f"esta manga: {hasta('C0')} y la tortuga casi intacta "
             f"({pocket('C0')}). Confirma docs/03.")
    d.bullet(f"C - tanques bajos + flotador combina PEOR que A2 sola "
             f"({hasta('C')} vs {hasta('A2')}): los 500 kg extra hunden el casco "
             "y el flotador trabaja contra mas desplazamiento. Ademas solo vale "
             "con tanques llenos, revisa la decision bancos-tanque y roba "
             "~55 mm de piso. Descartada.", color=WARN)
    d.bullet(f"D - el unico 180.0° literal Y pasivo. Precio: 4 plazas, ~1040 kg, "
             "remolque con frenos - deja de ser el barco del brief. Queda "
             "modelada (hull_selfrighting.stl / boat_selfrighting.3dm) por si "
             "el requisito se endurece.", color=WARN)

    d.add_page()
    d.h2("Matriz contra notes.txt")
    d.table([
        ("Requisito", "A1", "A2", "A3", "B", "C0", "C", "D"),
        ("6 plazas / cockpit grande", "si", "si", "si", "si", "si", "si", "NO (4)"),
        ("DIS < 750 rosca", "si", "si", "si", "si", "si", "si", "NO (~1040)"),
        ("bancos-tanque = asientos (dec. cliente)", "si", "si", "si", "si", "NO", "NO", "si"),
        ("pasivo / sin sistemas armados", "si", "si", "si", "NO", "si", "si", "si"),
        ("tope de mastil limpio", "si", "no", "no", "si", "si", "no", "si"),
        ("anti-tortuga efectivo", "parcial", "si", "si", "si", "NO", "si", "si"),
        ("auto-adriza desde 180.0 literal", "no", "no", "no", "SI", "no", "no", "SI"),
    ], widths=[64, 16, 16, 16, 16, 16, 16, 16], size=8.2)
    d.h2("La escalera de decision")
    d.bullet("HOY: A2 (sellado + flotador rigido 60 L) - la variante de este "
             "documento, con A1 incluido por definicion.", color=OK)
    d.bullet("SI la certificacion o el cliente exigen el 180.0° literal sin "
             "cambiar el barco: agregar B (bolsa inflable) sobre A2 y aceptar "
             "el regimen de mantenimiento.", color=OK)
    d.bullet("SI el requisito se endurece a 180.0° literal Y pasivo: variante D "
             "- es otro barco (4 plazas, ~1040 kg) y asi hay que presentarlo.",
             color=WARN)
    d.p("Los caminos A1/A2/A3/B comparten el 90% del trabajo ya hecho: casco, "
        "estructura, quilla, cockpit, planos y normativa no cambian. La "
        "decision se puede tomar - y revertir - despues de navegar el "
        "prototipo.", style="I")

    # ---------------- el bote en el agua ----------------
    d.add_page()
    d.h1("5. El bote en el agua")
    d.p("Renders estilizados desde el modelo de calculo: flotacion y escora "
        "reales, y ahora el flotador de tope en el color de acento de cada "
        "paleta - un elemento de seguridad se lleva a la vista, no se esconde.")
    d.img("foto_patagonia_navegando.png", w=148,
          caption="PATAGONIA navegando: escora 14°, flotador de 60 L en el tope")
    d.img("foto_aira_fondeado.png", w=148,
          caption="AIRA fondeado en calma: flotacion rosca de calculo (0.217 m)")

    # ---------------- entregables ----------------
    d.add_page()
    d.h1("6. Entregables de esta carpeta y proximos pasos")
    d.table([
        ("Archivo", "Contenido"),
        ("specs.md / cambios.md", "especificacion de la variante y registro de cambios contra el baseline"),
        ("report.txt / audit.txt / costs.txt", "corrida del modelo; auditoria 22/22 (15 base + 7 del paquete de tope); costos con el delta de la variante (USD 240-760, ~0.5%)"),
        ("gz_curves.png / hull_lines.png", "curvas GZ con y sin el paquete de tope; plano de lineas"),
        ("boat_autoadrizante.3dm + preview_3dm.png / preview_cockpit.png", "modelo Rhino por capas (capa nueva: flotador-tope) y sus vistas rapidas"),
        ("hull_autoadrizante.stl / offsets_autoadrizante.txt", "malla y tabla de puntos del casco (identico al baseline)"),
        ("planos.pdf", "8 laminas: L1-L7 constructivas del base + L8 flotador y condicion de diseno"),
        ("selfrighting.gif + anim_*.png", "animacion fisica: soltados a 150°, con y sin paquete de tope"),
        ("foto_*.png / diseno_*.png", "el bote en el agua y el estudio de color, con el flotador"),
        ("opciones.txt / .json / opciones_*.png", "insumos de la comparacion de opciones (seccion 4): corrida completa y figuras"),
        ("presentacion.pdf", "este documento"),
    ], widths=[76, 100], size=8.4)
    d.h2("Proximos pasos")
    d.table([
        ("#", "Accion", "Quien"),
        ("1", "Validar la afirmacion 'anti-tortuga + retorno autonomo hasta 156°' como cierre del requisito auto-adrizante del brief", "Cliente"),
        ("2", "Detallar el flotador con el mastilero (sellado del perfil, soporte de tope, drizas externas)", "Proyecto"),
        ("3", "Incorporar la traba de quilla como item de seguridad primaria en la especificacion de construccion", "Proyecto"),
        ("4", "Ensayo de vuelco del prototipo en agua protegida: validar limite de recuperacion y placa", "Astillero"),
    ], widths=[8, 138, 30], size=8.6)
    d.p("El estudio completo de alternativas (angostar a 1.80 m, cubierta "
        "tortuga, mas plomo) queda en docs/03 y out/; esta carpeta define la "
        "variante elegida para mantener el concepto de daysailer abierto y "
        "liviano.", style="I")

    path = os.path.join(DIR, "presentacion.pdf")
    d.output(path)
    return path


if __name__ == "__main__":
    p = build()
    print(f"escrito: {p}  ({os.path.getsize(p) / 1e6:.2f} MB)")
