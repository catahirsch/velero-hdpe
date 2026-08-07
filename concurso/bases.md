# Concurso de diseño naval con IA — velero abierto HDPE 6.48 m

**Para estudiantes y jóvenes profesionales de Ingeniería Naval (UTN)**

## 1. La idea

Diseñar con IA no es pedirle un barco a un chat: es usar modelos de lenguaje
para construir, criticar y explotar **modelos de cálculo reales** — hidrostática,
escantillonado, pesos, estabilidad — más rápido y más a fondo de lo que un
equipo llega solo. Este concurso pone esa práctica sobre un proyecto real y
verificable: el velero abierto de 6.48 m en HDPE de este repositorio, con su
cadena de cálculo paramétrica abierta (`calc/`, `geom/`).

Cada equipo recibe el mismo problema de ingeniería real (los **desafíos**), el
mismo modelo paramétrico y la misma vara de medir (el **evaluador
automático**). Lo que se compara no es quién dibuja mejor: es quién explora
mejor el espacio de diseño — y la IA es la pala.

## 2. Qué entrega un equipo

1. **Un diseño**: un archivo JSON con los parámetros del barco
   (`plantilla_diseno.json` — manga, calados, piso, bancos, aparejo, lastre,
   paquete de tope de mástil…). El evaluador lo convierte en un barco real:
   corre la hidrostática y las curvas GZ 0–180° con cockpit inundado, verifica
   el sobre dimensional y puntúa.
2. **Una bitácora de IA** (obligatoria): qué herramientas usaron, los prompts
   clave, qué propuso la IA, qué estaba mal y cómo lo detectaron, qué
   verificaron a mano. Se califica el *criterio*, no la cantidad de prompts.
   La regla de oro del concurso: **la IA propone, el ingeniero verifica**.
3. **Una memoria corta** (máx. 4 páginas): la lógica del diseño y las
   decisiones frente a los desafíos.

## 3. Cómo se participa (flujo GitHub)

1. Fork del repositorio.
2. Copiar `concurso/plantilla_diseno.json` a
   `concurso/entregas/<nombre-equipo>.json` y completarlo.
3. Probar localmente: `python3 -m concurso.evaluar concurso/entregas/<equipo>.json`
   — imprime el puntaje automático y genera la tarjeta de resultados.
4. Pull request con el JSON + bitácora (`entregas/<equipo>-bitacora.md`) +
   memoria (PDF). El PR es la inscripción.
5. La organización corre el evaluador oficial, publica la tarjeta en el
   leaderboard de la página del concurso, y el jurado califica lo no
   automatizable.

## 4. Puntaje

**Automático (hasta 100 pts)** — lo calcula `concurso/evaluar.py`, igual para todos:

| Rubro | Pts | Cómo se mide |
|---|---|---|
| Sobre dimensional | 20 | LOA<6.50, BEA<2.50, DIS<750, SQM<22, BAL<500 L, CBD<1.30 — se descuenta por violación |
| Auto-adrizado | 35 | límite de recuperación autónoma (rosca, cockpit inundado, tanques vacíos): 110°→0 pts, 180°→35 pts |
| Seguridad operativa | 20 | francobordo de piso a plena carga (autoachique) y ángulo de inundación |
| Porte de vela | 15 | SA/D a plena carga en banda sana (15–18) |
| Presupuesto de lastre | 10 | relación de lastre alcanzada dentro del tope de 750 kg |

**Jurado (hasta 40 pts)**:

| Rubro | Pts |
|---|---|
| Bitácora de IA: criterio, verificación, honestidad sobre errores de la IA | 20 |
| Innovación real y constructibilidad (¿se puede soldar/moldear?) | 12 |
| Claridad de la memoria | 8 |

Descalifican: parámetros fuera de rango físico (los valida el evaluador),
bitácora ausente o fabricada, plagio entre equipos.

## 5. El rol del Líder de IA

Figura nueva y central del concurso — dos capas:

- **Humano (Director/a de IA del concurso)**: mantiene el evaluador y el
  leaderboard, dicta el taller inicial de "IA para ingeniería" (cómo hacer que
  un LLM escriba y critique código de cálculo, cómo detectar alucinaciones
  numéricas, cómo documentar la bitácora), atiende consultas técnicas y audita
  las bitácoras.
- **Agente de IA oficial (el "Copiloto del concurso")**: un asistente
  disponible para todos los equipos por igual, cargado con este repositorio,
  que responde sobre el modelo de cálculo, explica resultados del evaluador y
  hace pre-chequeo de entregas. Que exista un copiloto común nivela la cancha:
  ningún equipo pierde por no tener acceso a herramientas.

Dentro de cada equipo se sugiere el mismo rol en miniatura: un integrante como
*líder de IA* responsable de la bitácora y de la verificación.

## 6. Cronograma sugerido (8 semanas)

| Semana | Hito |
|---|---|
| 1 | Lanzamiento + taller "IA para ingeniería naval" (obligatorio, 3 h) |
| 2–3 | Exploración: los equipos corren el modelo, entregas de práctica ilimitadas |
| 4 | Entrega intermedia (checkpoint en el leaderboard, no puntúa) |
| 5–6 | Iteración con feedback del evaluador |
| 7 | Entrega final (PR congelado) |
| 8 | Evaluación del jurado + jornada final presencial: defensa de 10 min por equipo |

## 7. Logística mínima a definir con la facultad

- Aval del departamento de Ingeniería Naval (UTN) y 2–3 jurados (un docente
  de arquitectura naval, un constructor de PE/astillero, el Director de IA).
- Equipos de 2–4; categoría estudiantes y categoría jóvenes profesionales.
- Premios (a definir): pasantía en astillero, licencias de software, y el
  compromiso de que **el diseño ganador se incorpora al proyecto real** como
  variante documentada — ese es el premio que importa.
- Acceso: el repo es público; solo hace falta una cuenta de GitHub y Python.

## 8. Por qué esto enseña IA de verdad

El evaluador es implacable: una curva GZ no se convence con un buen prompt.
Los equipos van a descubrir rápido que la IA acelera muchísimo — para leer el
código de cálculo, proponer variantes, escribir scripts de barrido, explicar
por qué un diseño falla — y que también inventa números con total confianza.
Aprender a usar lo primero y atrapar lo segundo **es** la competencia que la
profesión todavía no tiene, y es exactamente lo que este concurso mide.
