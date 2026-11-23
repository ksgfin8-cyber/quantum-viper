# QV-R01 · Quantum Viper v1.5c bajo RDL-PB-001 v0.1

23 de noviembre de 2026 · [Playbook](../program/RDL-PB-001_v0.1_original_propuesta.md)

## Registro y criterios previos · M1–M2

Candidato Pine Script v6, indicador superpuesto. Base `a97f6e0d7f198d8cd2a3726a8fa598f9da476360`. Blob de `codigo` `5e21d7117aeccd8323296155623e3dafd6d63b59`. Alcance de investigación en rama dedicada. Primero se inspeccionan fórmulas y estado, luego se ejecutan controles sintéticos acotados. Se mantienen las variantes en el arnés.

| Prueba | Caso y resultado esperado | Decisión que cambiaría |
|---|---|---|
| E1 | Por álgebra, P2 activa por debajo de .2 y P3 activa por debajo de .6. Pesos construidos para acuerdos P1/P2 y P1/P3, oposición, empate, neutro estricto, ausencia de dirección y masa cero. Espero que P2 limite Γ cuando apoya, que el empate se abstenga y que el neutro pueda elevar claridad. Comprobar también trayectorias OHLC y marcar su procedencia. | Precisar el papel de P2 y la interpretación de claridad si se observan esos mecanismos. |
| E2 | Dos sucesiones con los mismos signos netos, incluido cero, y magnitudes diferentes deben dejar idéntica memoria si se fijan votos y contextos previos. Probar abstención, contexto cruzado, primera barra elegible y ventanas reconocidas y de respaldo. Comparar dos revisiones de una barra desde el mismo estado confirmado. | Definir el objetivo de memoria y el instante de consumo de la señal según las dependencias que aparezcan. |
| E3 | Derivar Q ≤ .49 sin alineación P1/P3. Buscar una creación por defecto en OHLC positivo y válido con deriva de entrenamiento, expansión de rango y transición. Si no aparece, limitar el dictamen al dominio ensayado. En estado aislado, espero decremento en la creación, precio retenido a cero, sustitución y borrado solo por caída estricta, incluida la comparación 0 con 0. | Precisar si la vigencia debe controlar la publicación o la existencia del precio y si se exige actividad observable por defecto. |
| E4 | Mantener entradas y parámetros. Comparar ganador ponderado, fórmula original y variantes que fijan a 1 el mínimo o la semántica, o retiran la masa neutra de la competición y denominador. Espero cambios aislados y también casos invariantes. | Conservar cada mecanismo como requisito únicamente si su efecto tiene un propósito de producto explícito. |
| E5 | Exigir compilación original y trazas Pine independientes alineadas por símbolo, sesión, temporalidad, parámetros, calentamiento, barra y tipo de actualización. Localizar primer campo divergente si existe. Sin esa traza, concordancia **NO EVALUADA**. | Condicionar cualquier equivalencia o traslado de implementación a esa evidencia. |

Criterio de parada: cubrir los contrastes indicados con casos mínimos, sin extender el experimento a datos de mercado ni a métricas predictivas.

## Reconstrucción del candidato · M1, M3

Se usa índice cero. En la evaluación de la barra `t`, `[1]` designa `t−1`, incluida la barra anterior cuando `t` está abierta. Las ventanas de precio incluyen `t−1` como muestra más reciente.

| Fuente | Fórmula o dependencia | Disponibilidad |
|---|---|---|
| Qué entra | Cierres para retornos, EMA, ER, desviaciones y posición. Máximos y mínimos para rangos, ATR y NRT. ATR usa además el cierre previo de cada barra vía true range. Apertura, volumen y datos externos quedan fuera de la lógica. La cadena `timeframe.period` selecciona longitudes. | Solo el cierre `C[t]` entra en las fórmulas de decisión desde la barra actual, por memoria. |
| P1 · tendencia | Signo de EMA rápida menos lenta sobre `close[1]`. ER = desplazamiento absoluto / camino absoluto en `S` retornos consecutivos de `C[t−S−1]` a `C[t−1]`, o 0 si camino cero. Vota el signo EMA si ER supera el umbral. Φ₁ = ER × (1 − min(vol/.02, 1)), con vol = desviación poblacional de `V` cierres / `C[t−1]`. | EMA y ER al cierre anterior, también para barra abierta. ER devuelve .5 si `t < S+2`. El signo EMA bruto llega a la semántica incluso si P1 se abstiene. |
| P2 · reversión | z del último cierre en los `S` cierres (0 si σ carece de dispersión), y posición `u` en máximo/mínimo de `S` barras (.5 si rango degenerado). Vota +1 si z < −1.5 y u < .2, o −1 si z > 1.5 y u > .8. Φ₂ = (1 − min(abs(z)/3, 1)) × (1 − 2 abs(u−.5)). | Hasta `t−1`. Tanto la SMA como la desviación incluyen el cierre evaluado. |
| P3 · expansión | `R = ATR(V)[1] / SMA(ATR(V)[1], S)`, respaldo 1 cuando la media no es positiva o aún falta. Requiere R mayor al umbral. La posición `b` en rango de `F` barras activa +1 arriba de .7 o −1 abajo de .3. Φ₃ = min(R/1.5, 1) × (1 − 2 abs(b−.5)). | Hasta `t−1`. ATR suaviza TR por RMA, y su media incluye el ATR del numerador. La posición es interna al rango que incluye la propia barra, según esa fórmula «breakout» significa cercanía al borde con expansión y no requiere romper el rango anterior. |
| Contexto y memoria | Contexto actual 0/1 si hay tendencia P1 alcista/bajista, luego 3 si vol supera el umbral, en otro caso 2. Cada perspectiva tiene cuatro celdas persistentes `rel_i`, todas .5 al inicio. Persisten también los tres votos previos, el contexto previo (inicial 2) y la bandera `initialized` (inicial falsa). | Primero se puntúa la barra anterior usando `C[t]`, luego se leen las celdas del contexto actual para pesar Φ. Último paso de la evaluación guarda votos y contexto actuales. |
| Agregación | El peso `w_i = clip(Φ_i,0,1) × rel_i[context_current]` se suma en la clase del voto, incluido 0. La mayoría dirección requiere ganar estrictamente a ambas otras clases. `r` es el máximo de las tres masas dividido por el total, o 0 con total cero. `m` es el menor peso de los votos que coinciden con la mayoría direccional, o 0 sin ella. | Los valores Φ, los contextos y los votos dependen de `t−1` y anteriores. Los pesos pueden depender de `C[t]`. |
| Semántica y decisión | Base 1 si coinciden los signos direccionales del EMA bruto de P1 y el voto P3 activo, .7 si existe al menos uno y falla la coincidencia, .5 si ambos son cero. Factor .7 si P2 se opone a cualquiera de esos signos, incluso con peso P2 cero. `s` es su producto acotado a [.3,1]. Γ = `r × m × s × exp(−β(1−r))`. `a_final = a_maj` si Γ supera o iguala θΓ y `r ≥ .6`; en otro caso 0. | En `t`. El panel llama «Régimen» a `a_maj` y «Claridad» a `r`. La etiqueta «Producción Ready» es texto fijo. |
| Transición y NRT | `T_state` toma el signo de `a_final[t]` si pasa de cero o del signo contrario al signo actual. `Q_T = Γ × r × s` cuando hay transición, o 0. Si alcanza θNRT, escribe `low[t−1]` (alcista) o `high[t−1]` (bajista) y el contador del lado. Precios y contadores persisten por separado. | La transición se dibuja en la barra `t`. El precio se lee de `t−1`. La invalidación compara soporte del mismo lado de `t` con `t−5` después de crear y decrementar. |

Parámetros de entrada, con valor por defecto y dominio:

| Grupo | Parámetros |
|---|---|
| Core | λ .85 [.70,.95], β 2 [.5,5], θΓ .30 [.15,.60], θNRT .50 [.30,.80]. |
| Advanced | Umbral ER .60 [.30,.90], vol .025 [.01,.05], ATR 1.2 [1,2]. Mínimos F 5 [3,20] y S 10 [5,30]. Comisión .001 [.0001,.005], deslizamiento .0005 [.0001,.002]. Vigencia 20 [5,50], factor de caída .50 [.30,.80]. |
| Display | Panel y niveles, ambos activados por defecto. El interruptor de niveles controla las series dibujadas, no borra estado. |

Para temporalidad interpretada como minutos `m`, intradía usa `F=max(Fmin,round(1440/m))`, `S=max(Smin,round(2880/m))`. Día o superior según la tabla interna usa `F=max(3,round(720/m))`, `S=max(6,round(1440/m))`. Siempre `V=max(8,round(2160/m))`.

| Cadenas reconocidas | Minutos | F/S/V por defecto |
|---|---:|---:|
| 1, 5, 15, 30 | 1, 5, 15, 30 | 1440/2880/2160, 288/576/432, 96/192/144, 48/96/72 |
| 60 o 1h, 120 o 2h, 240 o 4h | 60, 120, 240 | 24/48/36, 12/24/18, 6/12/9 |
| D o 1D, W o 1W, M o 1M | 1440, 10080, 43200 | 3/6/8 en los tres casos |
| Otra, incluidas 3 y 2D | 60 de respaldo | 24/48/36 |

La tabla enumera coincidencias del código, independientemente de las cadenas que emita TradingView. EMA comienza con la primera observación utilizable. En historia completa, vol de cierres dispone de V muestras en `t=V`, z de S cierres en `t=S` y la media de ATR desplazado dispone de S ATR válidos en `t=V+S−1`. Los extremos consultan máximos y mínimos disponibles. No existe una puerta global de calentamiento para publicar señales. En particular, la memoria puede empezar en `S+1`, antes del primer ER calculado en `S+2`. Con umbral ER por debajo de .5 el respaldo puede activar P1 si hay signo EMA.

Son nombres del candidato «reliability», «claridad», «robustez», «breakout» y «vigencia». Las fórmulas establecen el comportamiento anterior. Quedan por fijar como contrato de producto la calificación de confianza, qué papel debe tener P2, el horizonte y objetivo de actualización, el instante permitido para consumir señales, la expiración visible de NRT, y las temporalidades y el calentamiento que se desean soportar. El código tampoco define una ejecución de órdenes ni un contrato de fills, tarifas o retornos de estrategia.

## E1 y E4 · Cotas, abstención y diferencial · M3–M4

Para OHLC válido el cierre está dentro de ambos rangos. Si P2 vota, `abs(z)>1.5` implica factor z en [0,.5), y `u<.2` o `u>.8` implica factor rango en [0,.4). Luego Φ₂ < .2 y peso P2 < .2, porque las memorias permanecen en [0,1] por combinación convexa. Puede pesar cero y seguir votando, e incluso penalizar la semántica como oponente. Si P3 vota, `b<.3` o `b>.7` implica factor de posición en [0,.6), y el factor ATR es a lo sumo 1. Luego Φ₃ < .6 y peso P3 < .6. Ambas son cotas superiores estrictas de las fórmulas, sin afirmación de alcanzabilidad de su supremo desde OHLC. Si P2 pertenece a la mayoría direccional, Γ ≤ m < .2, así que la decisión por defecto es nula aunque haya acuerdo. Con θΓ inferior a .2 ese argumento ya no basta. Si P2 se abstiene, las restricciones de activación anteriores no acotan su peso a .2.

El neutro gana estrictamente cuando su masa excede a las dos direcciones. Un empate que incluya la mayor masa también produce mayoría nula. Con masa positiva, `r` mide concentración en cualquier clase, también neutra. En particular si la masa se concentra en cero, el panel puede marcar verde por encima de .8 con Γ=0 y decisión nula. Si la masa es cero, las tres fracciones y `r` quedan a cero. El mínimo incluye coincidencias con peso cero.

Los casos siguientes inyectan los votos y pesos directamente. La columna `M/N/S` da la decisión al neutralizar, respectivamente, el mínimo (`m=1`), el voto nulo (masa 0 fuera del máximo y del total) o la alineación (`s=1`). El modo ponderado solo devuelve `a_maj`. La segunda intervención cambia los componentes del cálculo que dependen de la misma masa, mientras que el resto de reglas y umbrales sigue fijo. En cada variante se mantiene la comprobación de `r≥.6`. Los pesos se listan P1/P2/P3. El signo EMA bruto es + en todos los casos.

| Caso | Votos / pesos | `a_maj` | `r` | `m` | `s` | Γ | `a_final` | M/N/S |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P1/P2 | (+,+,0) / (.82,.10,.03) | + | .9684 | .10 | .7 | .0636 | 0 | +/0/0 |
| P1/P3 | (+,0,+) / (.73,.01,.55) | + | .9922 | .55 | 1 | .5373 | + | +/+/+ |
| Opuestos | (+,0,−) / (.80,.01,.12) | + | .8602 | .80 | .7 | .3642 | + | +/+/+ |
| Empate de direcciones | (+,0,−) / (.25,.04,.25) | 0 | .4630 | 0 | .7 | 0 | 0 | 0/0/0 |
| Neutro gana | (+,0,0) / (.45,.48,.32) | 0 | .6400 | 0 | .7 | 0 | 0 | 0/+/0 |
| Neutro verde con voto direccional | (+,0,0) / (.10,.48,.32) | 0 | .8889 | 0 | .7 | 0 | 0 | 0/0/0 |
| Ausencia de dirección | (0,0,0) / (.4,.5,.3) | 0 | 1 | 0 | .7 | 0 | 0 | 0/0/0 |
| Masa cero con votos | (+,0,−) / (0,0,0) | 0 | 0 | 0 | .7 | 0 | 0 | 0/0/0 |
| Mínimo o alineación | (+,0,0) / (.40,.01,.01) | + | .9524 | .40 | .7 | .2424 | 0 | +/0/+ |
| Solo alineación | (+,0,−) / (.99,0,.54) | + | .6471 | .99 | .7 | .2214 | 0 | 0/0/+ |
| Empate con neutro | (+,0,0) / (.48,.30,.18) | 0 | .5000 | 0 | .7 | 0 | 0 | 0/+/0 |

Desde OHLC, el arnés reproduce las siguientes salidas, con todas las memorias inicializadas en .5. Los empates positivos se ejercitan por inyección de pesos. El test de masa cero desde OHLC mantiene cierre y máximo en 100 y mínimo en 99, lo que da ER=0 y ambos factores de posición nulos.

| Serie y barra | Votos | `a_maj` | `r` | `m` | `s` | Γ | `a_final` |
|---|---|---:|---:|---:|---:|---:|---:|
| Diaria, 86 | (+,+,0) | 0 | .5540 | 0 | .7 | 0 | 0 |
| Horaria, 60 | (+,−,0) | + | .9929 | .1294 | .49 | .0620 | 0 |
| Horaria, 121 | (+,−,+) | + | .999999 | .1435 | .7 | .1004 | 0 |
| Horaria, 1009 | (0,0,0) | 0 | 1 | 0 | .7 | 0 | 0 |
| Horaria, 1081 | (+,0,+) | + | 1 | .5882 | 1 | .5882 | + |
| Plana horaria, 69 | (0,0,0) | 0 | 0 | 0 | .5 | 0 | 0 |

En la serie horaria de expansión, comparar las barras 60–1081 sobre las mismas entradas y estado cambia la decisión en 936 de 1.022 barras al neutralizar el mínimo, y en 0 con cada una de las otras dos variantes. Primeros cambios por mínimo en 60, 66, 67, 68 y 69. Es una secuencia de entrenamiento artificial. Los casos de inyección sí separan efectos del neutro y de la alineación, sin atribuirles una frecuencia en OHLC real. La intervención se aplica a la decisión en esa barra, con los estados del original fijos.

## E2 · Memoria y tiempo · M3–M4

En la barra `t` elegible se puntúa `a_i[t−1]` contra el retorno `(C[t]−C[t−1])/C[t−1]` y se escribe exclusivamente `rel_i[context[t−1]]`. La entrada del suavizado es 1 si el retorno firmado menos comisión y deslizamiento es estrictamente positivo, y 0 si es cero o negativo. Se puntúa el voto individual, incluso si la decisión final anterior fue nula. Una abstención individual conserva todas sus celdas. La celda actual puede coincidir con la anterior y usar la actualización de inmediato, o ser otra celda. Ejemplo del segundo caso, tras dos escrituras de P2 en contexto lateral 2 al llegar a la barra diaria 8, se lee contexto alcista 0, aún con .5 en P2.

En el control aislado se fijan votos previos (+,0,−) y contextos previos (1,3,1). Los retornos brutos (.002,−.002,.0015) y (.10,−.07,.0015) producen las mismas tres escrituras por perspectiva activa. P1 registra éxito, fallo, cero; P3 fallo, éxito, fallo; P2 nunca se puntúa. Desde .5, P1 termina en .48875/.425 en celdas 1/3 y P3 en .36125/.575. Las demás celdas quedan en .5. En diario `S=6`, el voto bajista P2 de la barra 6 pierde en la 7, primera elegible, y el de la 7 pierde en la 8, dando .36125. ER sigue en .5 en 6 y 7, y vale 1 en 8 en esa serie. El arnés comprueba todas las ventanas y alias de la tabla, más las dos cadenas de respaldo.

- **Barra confirmada.** Las características de votos usan datos hasta el cierre anterior; los pesos y la señal confirmada pueden incorporar el cierre de la barra evaluada vía memoria. Una evaluación que use la señal como predictor debe fecharla al cierre y definir su resultado posterior por separado.
- **Barra abierta.** El indicador no exige `barstate.isconfirmed`. El cierre provisional puede cruzar el umbral de costes, cambiar la memoria efectiva, el peso, la decisión y, por dependencia, la transición y NRT. Con el mismo estado confirmado inicial, votos previos (+,0,0), contexto persistente 0 y Φ₁=.8, dos retornos provisionales .002 y .001 dan .575 y .425 en la misma celda, pesos .46 y .34, Γ .322 y .238, y decisiones +1 y 0 con el resto de pesos cero. Es un control inyectado. Según el modelo de ejecución de Pine se recalcula desde el estado confirmado mediante rollback y se confirma el último cálculo al cerrar. Las sucesivas revisiones de una barra no representan muestras adicionales de aprendizaje. El candidato no declara `varip`. La secuencia intrabar de un gráfico real queda sin observación. [Modelo de ejecución de Pine](https://www.tradingview.com/pine-script-docs/language/execution-model/)

## E3 · Alcance y vida de NRT · M3–M4

Para una transición `Q_T = r² × m × s² × exp(−β(1−r))`. Con `r,m≤1` y β positivo, si falla la alineación del EMA bruto P1 con el signo P3, `s≤.7` y por tanto `Q_T≤.49`. Alineación con penalización de P2 también deja `s=.7`. Así, la configuración por defecto exige `s=1` para crear. La cota por sí sola no excluye activación con θNRT configurado por debajo de .50.

El arnés genera 1.082 barras positivas de OHLC válido en temporalidad 60. Usa una deriva de +.17 % por barra durante 1.000 barras con expansiones de rango cada 60, un desplazamiento de −5 % con 80 barras casi planas y una expansión final tras un alza de 1.2 % sobre el ancla. La única creación se reproduce en **barra 1081**, sin ajustar los parámetros. La 1080 cierra con decisión 0. En la 1081, la barra de expansión pasa a `[1]`, ER=.928793, z=6.855540, posición P2/P3=.705882, ATR/ATR medio=1.916955. P2 se abstiene y pesa 0, P1/P3 votan + y pesan .605726/.588235. Soportes (+,−,0)=(1.193961,0,0), `r=s=1`, `m=Γ=Q_T=.588235`, decisión y transición +1. Escribe el mínimo previo 509.741069823 y queda con contador 19. Es evidencia de alcanzabilidad en el modelo OHLC local, pendiente de ejecución independiente de Pine.

El ciclo se controló también en aislamiento, con el operador de estado de un lado y referencias de soporte inyectadas. `c` es la barra de creación:

| Paso | Entrada y orden | Estado después de evaluar |
|---|---|---|
| c | Precio 100 y contador 20. El decremento se aplica inmediatamente. Soporte actual y de hace cinco barras iguales a 0. | Precio 100, contador 19, visible con `show_nrt=true`. `0 < 0×.5` es falso. |
| c+1 | Sin nueva creación. | Precio 100 y contador 18. |
| c+18, c+19 y c+20 | Mantener soportes en 0. | Contadores 1, 0 y 0, con precio 100 visible en las tres evaluaciones. |
| Frontera de caída | Soporte actual .20 y previo .40. Repetir con .199, o con 0 y previo .40. | En igualdad exacta persiste. Los dos casos inferiores borran precio y ponen contador a cero. Un lag ausente tampoco dispara comparación verdadera. |
| Reemplazo mismo lado | Nueva creación a 101 con .30/.40; repetir con .10/.40. | Primero escribe 101 y reinicia, queda en 19 en el primer caso. En el segundo, la invalidación posterior a crear lo borra en la misma barra. |
| Interruptor de dibujo | Precio retenido, con `show_nrt=false`. | Serie de dibujo ausente sin cambio de precio ni contador. El panel NRT consulta precios, con prioridad alcista si existen ambos. |

El bucle de aislamiento comprueba cada decremento hasta cero y la visibilidad de la serie en todos los pasos. Los dos lados son simétricos por inspección y pueden coexistir, pues crear uno no borra el otro. Alcanzar contador cero solo cambia el contador. La invalidación y el reemplazo siguen siendo posibles tras ese punto. La condición de caída mira una razón relativa a cinco barras, no a la creación. El estilo de línea puede unir tramos con datos ausentes; la prueba evalúa los valores de la serie y no el renderizado.

## E5 · Concordancia y transferencia · M5

**NO EVALUADA.** El intento HTTPS a `www.tradingview.com/chart/` en esta instancia recibió 403 al abrir el túnel del proxy. No se obtuvo sesión del editor, compilación del candidato ni traza Pine independiente. Por tanto no hay una primera divergencia observable, ni para señal, ni memorias ni NRT.

Se inspeccionó el antecedente de Filtrado en `cf3130f0b29531928a9a3916365a5edfb05f5218`, incluido el árbol del commit y sus arneses. El árbol no contiene el blob de `codigo`. Los blobs del comparador EMA y del comparador de estado son `281c7c5d32add4fa6ee126d3dfa0b08b481bf913` y `dd93caea8c2a6f1275aa240aa3f5986d06cc7405`. El núcleo referenciado (`7772485747be935398330902293efde87b35fa48`) se identifica como Viper Minimal Core v0.1. Su interfaz tiene fiabilidad escalar y EMA con semilla SMA, sin el contrato de 12 celdas, tres votos y dos estados NRT del candidato. La referencia EMA comparte implementación con el lado bajo prueba en Filtrado, y el arnés de estado llama al mismo núcleo para ambos lados. Se adopta el control metodológico de perturbación unilateral para un futuro comparador independiente. No se reutilizaron esos comparadores ni se trasladaron sus resultados a Quantum Viper. [Expediente Filtrado-R01](https://github.com/ksgfin8-cyber/Filtrado/blob/cf3130f0b29531928a9a3916365a5edfb05f5218/docs/research/FILTRADO_RDL_PB_001_EVALUATION.md)

Para reabrir, compilar y archivar la identidad del original. Si se requiere instrumentar campos internos, hacerlo en copia con el delta de instrumentación registrado y verificar igualdad de las salidas visibles. Fijar proveedor, símbolo, sesión, zona, temporalidad, tipo de gráfico, parámetros, eje y primera barra de historia. Exportar OHLC y por barra confirmada votos, contexto actual y previo, 12 celdas, tres soportes, `a_maj`, `r,m,s,Γ`, `a_final`, T, Q, precios y contadores NRT. Hacer una captura separada con clave de barra y orden de actualización para tiempo real. Verificar que el comparador detecte una perturbación unilateral superior a la tolerancia sobre estado cubierto. Comparar igualdad de enteros y presencia de valores, y fijar tolerancias numéricas antes de comparar flotantes. Reportar primera barra y primer campo desigual, con ambas entradas y estados previos. En ausencia de historial inicial idéntico, la comparación de memoria y NRT no tiene una condición inicial común.

## Decisión por propiedad y coste · M6–M7

| Propiedad | Evidencia y decisión |
|---|---|
| Papel de P2 y claridad | **VERIFICADA** la cota por álgebra y los efectos en casos locales. Precisar si P2 debe confirmar una dirección, frenarla o aportar un veto. La regla actual impide emisión por defecto cada vez que P2 acompaña a la mayoría, y una claridad verde puede corresponder a abstención. |
| Objetivo de memoria | **VERIFICADA** la actualización binaria condicionada al voto y contexto anteriores. **REPRODUCIDA** la invariancia a magnitud y la dependencia del cierre presente. Precisar si el objetivo es frecuencia de acierto neto por barra y contexto, valor económico u otro estimando. Definir si la señal se consume únicamente al cierre. |
| NRT | **VERIFICADA** la cota por álgebra y el desacoplamiento de contador, precio y dibujo por inspección. **REPRODUCIDAS** la creación con parámetros por defecto y las transiciones de estado locales. Precisar qué debe expirar y cuándo, cómo manejar dos lados y qué representa una caída de soporte. |
| Mecanismos | **REPRODUCIDOS** efectos aislados y casos invariantes. Son reglas con consecuencias de decisión observables en el dominio ensayado. Su utilidad de producto necesita un objetivo explícito y contraste contra él. |
| Concordancia Pine | **NO EVALUADA**. Mantener abierta la puerta de equivalencia hasta obtener una trayectoria Pine independiente alineada. |
| Capacidad predictiva, rentabilidad y ventaja en mercado | **NO EVALUADAS** en QV-R01. |

Controles reutilizables: fijación de identidad Git y puentes de versión para evitar transferencias entre contratos distintos, vectores inyectados para cotas y ablación con una sola intervención, trayectorias OHLC pequeñas y deterministas para comprobar alcance local, y pasos de máquina de estados para límites inclusivos y estrictos. La repetición del arnés completo requiere Python estándar y tomó aproximadamente 0.2 s de pared en esta instancia. El coste de la inspección y de preparar los estímulos no se instrumentó. El arnés modela OHLC positivo continuo, parámetros por defecto y trazas de cierre; simplifica bordes de datos ausentes y no replica todas las reglas de precisión, datos y recalculación del motor Pine. La inspección algebraica se aplica a valores finitos y rangos válidos. Una captura Pine suma preparación de cuenta, instrumento, historial e instrumentación; ese coste queda sin medir.

## Reproducción

Desde la raíz del repositorio, con Python 3.12.14 en la ejecución registrada. El arnés imprime trazas y un código de salida distinto de cero si falla una aserción. Los números de barra del informe son índices de las secuencias generadas, sin fechas de mercado.

```sh
git rev-parse a97f6e0d7f198d8cd2a3726a8fa598f9da476360:codigo
git log --oneline -- codigo
git rev-parse 103dd12:codigo HEAD:codigo
git rev-parse HEAD:docs/program/RDL-PB-001_v0.1_original_propuesta.md
time python3 docs/research/quantum_viper_r01.py
git diff --check a97f6e0d7f198d8cd2a3726a8fa598f9da476360 HEAD
git diff --name-status a97f6e0d7f198d8cd2a3726a8fa598f9da476360 HEAD
git ls-remote origin refs/heads/main refs/heads/research/quantum-viper-r01
```

El alta `103dd12` y la base contienen el mismo blob del candidato. El blob del Playbook es `d5987168b24d677c2f5a98f194c05b41dc869db2`. El delta autorizado comprende este expediente y el arnés.
