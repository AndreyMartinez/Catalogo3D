# Plan de implementación — Vocabulario de formas

El orden sale de tres criterios, en este orden de prioridad:

1. **El vigilante primero.** El medidor de voladizo tiene un hueco —sólo mira
   cuando la pared se abre— y el cuello lo destapa el primer día. Se arregla
   antes de agregar nada, para que todo lo que venga después nazca vigilado.
2. **Lo probado antes que lo especulado.** El cuello ya se prototipó y se
   renderizó: es el eje de mayor valor y menor riesgo, y va segundo.
3. **Lo barato antes que lo caro.** El borde reusa `tope[]`, que ya existe. El
   pie escribe código nuevo pero con herramientas que ya están. El calado es el
   único que inventa mecanismo, y va al final de los ejes.

Cada eje termina con su prueba de **valor neutro**: con el eje apagado, la pieza
tiene que dar exactamente los mismos vértices, triángulos y gramos que antes de
que el eje existiera. Es lo que convierte «no rompimos nada» en algo
comprobable.

La pestaña «Idea» queda pausada en su tarea 4 mientras dure este plan.

- [x] 1. El vigilante, antes que nada
  - [x] 1.1 Medir el voladizo en los dos sentidos
    - En `nucleo/cuerpo.py`, cambiar el chequeo de `if r1 > r0` a comparar
      `abs(r1 - r0)`, guardando además en qué sentido ocurre.
    - El aviso dice los grados y si la pared «se abre» o «se cierra».
    - _Requisitos: 6.1, 6.2_
  - [x] 1.2 Probar que acierta en los dos sentidos
    - Tabla de siluetas con su ángulo calculado a mano, una que se abre y otra
      que se cierra, más el caso medido en el prototipo: boca 0.30 con hombro en
      0.80 cierra a 57.7° y tiene que avisar.
    - Correr la línea base: las tres recetas no pueden cambiar ni un gramo.
    - _Requisitos: 6.1, 6.2, 7.1_

- [x] 2. El cuello
  - [x] 2.1 Escribir `nucleo/cuello.py`
    - Clase `Cuello(fn, varia_z, neutro)` con la misma forma que `Perfil`.
    - Familias: `ninguno`, `suave`, `abrupto`, `botella`.
    - La curva es un smoothstep `t²(3−2t)` entre hombro y boca: derivada nula en
      los dos extremos, que es lo que evita la esquina en el hombro.
    - _Requisitos: 1.1, 1.2, 1.3_
  - [x] 2.2 Declarar los parámetros
    - `cuello`, `boca` (0.25–1.00) y `cuello_hombro` (0.30–0.95) en
      `disenos.PARAMETROS`, grupo «Cuello», con su ayuda escrita.
    - _Requisitos: 7.2_
  - [x] 2.3 Engancharlo en el motor
    - Componer el factor dentro de `escala(z)`, junto al perfil y el filete.
    - Subir `capas` cuando `cuello.varia_z`, junto a las condiciones que ya
      existen para el acabado y el perfil.
    - Cuando el cuello es neutro, **no** componer el factor ni agregar
      fracciones: multiplicar por 1.0 es exacto, pero las capas extra no.
    - Evaluar `_pared_se_cruza` también a la escala mínima que alcance el cuello.
    - _Requisitos: 1.5, 1.7_
  - [x] 2.4 Las reglas de convivencia
    - Con cuello no neutro, forzar `ranuras` y `filas` a 1 y avisar por qué.
    - Avisar cuando el hombro se cierra a más de 45°.
    - _Requisitos: 1.4, 1.6, 7.3_
  - [x] 2.5 Pruebas del cuello
    - Que el radio de la boca sea el pedido con menos del 2% de error.
    - Que la derivada del perfil sea continua en el hombro: diferencias finitas
      a los dos lados, sin salto.
    - Que la malla salga cerrada en todo el rango de `boca` y `cuello_hombro`.
    - Valor neutro: geometría idéntica a la de antes del eje.
    - Que con cuello no queden divisores, y que el aviso llegue.
    - _Requisitos: 1.1, 1.3, 1.6, 1.7, 6.5_

- [x] 3. El borde
  - [x] 3.1 Escribir `nucleo/borde.py`
    - `remate(p, anillo, alto)` devuelve una altura por columna.
    - Familias: `recto`, `diagonal` (rumbo y pendiente), `ondulado` (coseno de
      `s`) y `petalos` (arcos de valle vivo).
    - Las frecuencias que corren a lo largo del contorno son enteras a la
      fuerza: el contorno se cierra sobre sí mismo y una onda que no dé vueltas
      enteras deja un escalón en la costura.
    - _Requisitos: 4.1, 4.2, 4.3_
  - [x] 3.2 Declarar los parámetros y engancharlo
    - `borde`, `borde_hondura`, `borde_ondas` y `borde_rumbo` en `PARAMETROS`.
    - Componer con el escalón que ya existe **por mínimo**: los dos son alturas
      de remate y el material sobra donde alguno corta.
    - _Requisitos: 4.4, 7.2, 7.4_
  - [x] 3.3 Los divisores bajo un borde recortado
    - Recortar cada divisor a la altura mínima del remate que tiene encima, y
      avisar cuando se recortó.
    - _Requisitos: 4.5_
  - [x] 3.4 Pruebas del borde
    - Que la altura máxima y la mínima del remate sean las pedidas.
    - Que la malla cierre con cada familia y en los extremos de hondura.
    - Que ningún divisor asome por encima del borde.
    - Valor neutro: con `recto`, geometría idéntica.
    - _Requisitos: 4.1, 4.5, 4.6, 6.5_

- [ ] 4. El pie
  - [ ] 4.1 Escribir `nucleo/pie.py` con el aro de apoyo
    - Firma `construir(anillo, escala, p)`, la misma que `bandeja.construir`:
      devuelve la pieza o el motivo por el que no se pudo.
    - El aro sale de `M.placa(exterior, [interior], 0, alto)`, que ya construye
      un prisma con huecos.
    - El cuerpo se levanta `pie_alto` y sólo el aro toca la mesa.
    - _Requisitos: 2.1, 2.2_
  - [ ] 4.2 El plinto
    - `_loft` de dos secciones: abajo retranqueada, arriba a ras del cuerpo.
    - El cuerpo vuela sobre el plinto, así que la transición sube en talud;
      exigir `retranqueo ≤ alto` para no pasar de 45°, recortar y avisar si no.
    - _Requisitos: 2.1, 2.3, 2.5_
  - [ ] 4.3 Las patas
    - De tres a seis, repartidas parejo, colocadas **bajo la pared** y no bajo la
      cavidad, para que apoyen sobre material.
    - Omitir y avisar las que no encuentren material encima.
    - _Requisitos: 2.1, 2.4, 2.6_
  - [ ] 4.4 Declararlo y engancharlo
    - `pie`, `pie_alto`, `pie_retranqueo` y `patas` en `PARAMETROS`.
    - Unir la pieza al conjunto como se unen hoy los divisores.
    - La bandeja recibe la altura del pie y la suma a su `apoyo`; comprobar que
      el aro no caiga en el hueco entre costillas y girar el reparto si cae.
    - _Requisitos: 2.7, 7.2, 7.4_
  - [ ] 4.5 Pruebas del pie
    - Que todos los puntos de apoyo estén exactamente en `z = 0` y que el cuerpo
      no toque la mesa.
    - Que el área de contacto sea la esperada para cada familia.
    - Que un plinto con retranqueo excesivo se recorte y lo avise.
    - Valor neutro: geometría idéntica.
    - _Requisitos: 2.5, 2.6, 2.8, 6.4_

- [ ] 5. El calado
  - [ ] 5.1 La máscara, sin tocar todavía la malla
    - `nucleo/calado.py` con `abierto(s, z)` y `cerca_del_borde(s, z)`.
    - Familias `ventanas` y `celosia`, con columnas, hileras y holgura.
    - Declarar `capas_minimas`, igual que hacen los acabados que dibujan con la
      altura.
    - Probarla como función pura antes de que corte nada.
    - _Requisitos: 3.1, 3.2_
  - [ ] 5.2 Los remates, que es donde manda la física
    - Remate ojival: dos rectas a 45°, autoportante siempre.
    - Remate de medio punto: permitido, midiendo la corona; si el tramo a menos
      de 20° de la horizontal pasa de 8 mm, avisar y sugerir el ojival.
    - El borde inferior sí puede ser plano: por ahí no cuelga nada.
    - _Requisitos: 3.3_
  - [ ] 5.3 Cortar el casco y coser las jambas
    - En `cuerpo.py`, omitir los quads exteriores e interiores de las celdas
      abiertas.
    - Por cada arista donde una celda abierta toca una cerrada, emitir el quad
      que une el anillo exterior con el interior: ése es el canto de la ventana
      y es lo que deja la malla cerrada.
    - _Requisitos: 3.1, 6.5_
  - [ ] 5.4 Que el marco quede limpio
    - Desvanecer el relieve del acabado a cero en el último milímetro y medio
      antes de un hueco, con `cerca_del_borde()`.
    - _Requisitos: 3.7_
  - [ ] 5.5 Los recortes y las reglas de convivencia
    - Dejar marco completo arriba y abajo; ningún puente más angosto que dos
      paredes; reducir cantidad o tamaño hasta que quepan, diciendo qué se
      recortó.
    - Con calado, no ofrecer drenaje ni bandeja, y explicar que la pieza no
      retiene agua.
    - _Requisitos: 3.4, 3.5, 3.6, 7.3_
  - [ ] 5.6 Pruebas del calado
    - Que el número de aberturas sea el pedido y que el volumen baje al abrirlas.
    - Que la malla cierre con cada familia, cada remate y en los extremos.
    - Que ningún puente quede más angosto que dos paredes.
    - Que un arco de medio punto de corona larga avise.
    - Valor neutro: geometría idéntica.
    - _Requisitos: 3.3, 3.4, 3.8, 6.5_

- [ ] 6. Los topes que se mueven
  - [ ] 6.1 Ampliar los rangos
    - `perfil_intensidad` de 0.35 a 0.75 y `pliegue_profundidad` de 0.16 a 0.30.
    - Dejar libre la amplitud de los acabados que sólo suman material —el junco
      no talla, pone lomos— manteniendo el recorte para los que tallan.
    - _Requisitos: 5.1, 5.2, 5.3_
  - [ ] 6.2 Probar que el rango entero es sano
    - Barrer cada parámetro ampliado de mínimo a máximo comprobando que la malla
      cierra en todo el recorrido.
    - Que las recetas existentes no muevan ni un valor.
    - _Requisitos: 5.2, 5.4_

- [ ] 7. Que todo conviva
  - [ ] 7.1 Fijar el orden de aplicación
    - Planta → perfil → cuello → acabado → calado → borde → pie, escrito en un
      solo lugar del código y no repartido.
    - _Requisitos: 7.4_
  - [ ] 7.2 El barrido combinatorio
    - Clase de pruebas aparte —puede tardar y la vuelta rápida debe seguir
      siendo rápida— que cruza los valores extremos e intermedios de cada eje
      con los de los demás y exige malla cerrada en todos.
    - _Requisitos: 6.5, 7.6_
  - [ ] 7.3 Una prueba por regla de convivencia
    - Cuello con divisores, calado con bandeja, borde con divisores, plinto
      excesivo, patas sin material. Cada una comprueba también que el aviso llegó.
    - _Requisitos: 7.3_
  - [ ] 7.4 Cerrar con la línea base y el README
    - Las tres recetas, idénticas vértice por vértice.
    - Una sección por eje en el `README.md`, en el tono del resto: qué es, por
      qué está, y qué lo hace verse caro o barato.
    - _Requisitos: 7.1, 7.5_

- [ ] 8. Ver lo que se elige
  > Nota: una parte de esto ya se hizo, pero por otro camino y sólo para la
  > planta. En vez de miniaturas por opción sobre una pieza de referencia
  > (8.1), el botón «▦ Verlas todas» del selector de planta abre un muestrario
  > que renderiza **la pieza que el usuario tiene puesta** en todas las
  > plantas, de una en una y llenando la rejilla. Se prefirió así porque la
  > pregunta real no es «cómo es un riñón» sino «cómo se ve mi portacubiertos
  > en riñón». Falta: los demás selectores de forma (perfil, cuello, borde,
  > acabado), y el guardado en disco de 8.2 — hoy la caché es de la sesión del
  > navegador, que alcanza porque una miniatura cuesta un cuarto de segundo.
  - [ ] 8.1 Generar las miniaturas
    - Una miniatura por opción de cada selector de forma —planta, perfil,
      cuello, pie, calado y borde—, renderizada por el propio motor sobre una
      pieza de referencia.
    - Calcularlas una sola vez y guardarlas en disco, no en cada arranque.
    - _Requisitos: 8.1, 8.2_
  - [ ] 8.2 Enseñarlas en la pestaña «Crear»
    - Sustituir los `<select>` de forma por una rejilla de miniaturas con su
      etiqueta.
    - Sacar la ayuda del `title=` y ponerla a la vista, que es donde está escrito
      lo bueno.
    - _Requisitos: 8.1_
  - [ ] 8.3 Que no se ponga lenta
    - Comprobar que la vista previa responde como hoy con todos los ejes activos.
    - _Requisitos: 8.3_
