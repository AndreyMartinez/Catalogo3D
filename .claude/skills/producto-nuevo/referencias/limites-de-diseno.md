# Lo que sé hacer bien, lo que no, y cómo no meterme en problemas

Escrito para decidir **antes** de proponer. Cada propuesta lleva semáforo
según esto. Está basado en lo que ya pasó en este proyecto (ver memorias), no
en teoría.

## Verde — lo resuelvo bien y rápido

| Tipo de pieza | Cómo | Prueba de que funciona |
|---|---|---|
| **Recipiente de una pieza** con planta cualquiera (rectángulo, óvalo, superelipse, hoja, arco, guijarro, riñón, lóbulos, polígono…) | Motor `generadores/` — contorno + acabado + perfil + ranuras + base | Portacontroles, portacubiertos, portalápices, portacepillos 02RAPIDO |
| **Relieves periódicos** sobre la pared: ondulado, estría/canal, torsión, torsión de lado, rombo, espiga, junco, lino, martillado, escalonado | Acabados del motor | Torsión «le gusta montón»; canal del portacepillos |
| **Compartimentos** (ranuras/divisores rectos) | `ranuras`, `divisor_grosor`, `divisor_alto` | Portacontroles 4 espacios, portacubiertos 3 |
| **Poliedro low-poly / facetado** de silueta simple (huevo, vaso, maceta) | Script dedicado tipo `huevo_lowpoly.py` | Huevo low-poly «otro nivel, perfecto» |
| **Bandeja de goteo** como segunda pieza | `bandeja: goteo` | Motor |
| Ajustar un `.3mf` existente: escala, perfil, placa llena, costura, capa variable | `/transform`, `optimizar-pieza` | Más de 15 piezas en `.claude/optimizaciones/` |

## Amarillo — se puede, con una ronda de prueba física

- **Cosas que deben ajustar con un objeto real** (celular, control, cepillo
  eléctrico, audífonos): necesito las medidas del usuario y una impresión de
  prueba. No las saco de internet.
- **Piezas con cuello o boca que se cierra** (jarrones, floreros): el motor
  tiene el cuello, pero la medición de voladizo al cerrar tiene un hueco
  conocido (spec `vocabulario-de-formas`). Verificar ángulo a mano.
- **Formas nuevas que el motor no tiene** (una planta trazada de una foto):
  existe el contorno `trazado`, pero se prueba más.
- **Peso fuera de 120–250 g**: abajo de ~100 g el margen se lo comen la
  paquetería fija (~$14); arriba de ~300 g se alarga la placa. Se puede, pero se dice.
- **Patrones calados** (ventanas en la pared): están en diseño en la spec, no
  en producción.

## Rojo — evitarlo o ir por otro camino

| Qué | Por qué me sale mal | Camino alternativo |
|---|---|---|
| **Figuras orgánicas / animales escritos a mano** | Tres versiones del golden fallaron; la proporción anatómica con pocos planos se pierde | Modelo base con licencia comercial + adaptarlo (escala, placa, soporte) |
| **Caras, expresiones, texto chico, logos finos** | Bajo la boquilla de 0.4 se pierden; en render se ven, impresos no | Grabado grande ≥ 1 mm de profundo y ≥ 6 mm de alto, o nada |
| **Mecanismos**: bisagras, giratorios, cajones, clips, tapas a presión, roscas | Dependen de tolerancias que solo se encuentran imprimiendo y fallan | Pieza de una sola parte; si gira, que gire sobre una base comprada |
| **Piezas que cargan peso** (repisas, ganchos de pared) | Capas en la dirección débil; riesgo de reclamo | No entrar |
| **Multicolor / AMS** | Más tiempo y desperdicio; no está en la línea | Un color por pieza; la variedad va en variantes de color |
| **Sobre la placa: > 256 mm** o algo que solo entra 1 por placa y tarda > 10 h | Mata la capacidad (una sola P2S) | Achicar o partir en módulos que no necesiten encastre |
| **Cosas que tocan comida** con promesa sanitaria | PLA con capas no es apto; reclamos | Portacubiertos sí (cubiertos secos/limpios), recipientes de comida no |
| **Copias de un diseño de marca** | Propiedad intelectual | Inspiración de función, nunca de forma registrada |

## Debilidades mías que hay que compensar en el proceso

1. **No veo la pieza impresa.** Un render bonito no garantiza capas limpias.
   Por eso existe la fase 4 y por eso pido foto.
2. **Tiendo a sobre-iterar parámetros** cuando el problema es el concepto
   (huevo: cuatro rondas de acabado antes de cambiar a poliedro). Regla: si dos
   rondas seguidas no convencen, cambiar de concepto, no de número.
3. **Puedo estimar mal el tiempo**: lo manda el número de trazos, no los
   gramos (memoria `tiempo-lo-manda-el-numero-de-trazos`). Laminar por CLI
   antes de prometer horas.
4. **Medidas de objetos de terceros**: las invento si no las pido. Pedirlas.
5. **Gusto**: propongo, el usuario decide. Elegante / moderno / minimalista
   significa en esta línea: una sola idea de forma, superficie con relieve
   fino y regular, colores sólidos (negro, gris, blanco y algún tono), sin
   textos ni personajes.

## Reglas de imprimibilidad (recipientes)

- Una sola pieza, base plana, **cero soportes** (las figuras sí pueden
  llevarlos — memoria `soportes-en-figuras`).
- Voladizo ≤ 45° medido; filete de base cortado a 45°.
- Pared ≥ 1.6 mm; con relieve hondo, 1 perímetro + Arachne.
- Entra en la placa con margen; buscar ≥ 2 copias por placa.
- Peso objetivo 120–250 g para precio $198–219.
