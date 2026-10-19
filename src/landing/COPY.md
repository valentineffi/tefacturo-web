# Landing de performance `/empezar/`: documento de copy

**Estado:** borrador 1 (2026-10-14), para revisar con el cliente antes de mandar tráfico pago. Las opciones A están implementadas en `src/landing/empezar.html`; las B quedan para test A/B.

**Para qué es esta página:** destino de anuncios (Meta Ads y Google Ads). Una sola conversión: abrir una conversación de WhatsApp con el equipo de TeFacturo. Va con `noindex` y fuera del sitemap para no competir con la home ni con las guías en buscadores.

**A quién le habla (un lector):** dueño o dueña de un comercio chico de mostrador (kiosco, almacén, ferretería, local de ropa) que llega desde un anuncio en el celular. Hoy factura desde Comprobantes en línea en la web de ARCA, con una ticketeadora vieja, o todavía no factura y tiene que empezar. Su dolor, en sus palabras: *"Facturar en la página de ARCA me lleva un montón y con gente esperando no puedo"* y *"No sé ni cómo dar de alta el punto de venta"*.

Fuera de alcance: profesionales que emiten pocas facturas por mes (les alcanza Comprobantes en línea, y la guía comparativa ya lo dice) y empresas medianas con ERP.

**Cómo leerlo:** cada sección tiene "Para qué" (nota interna, no va en la página) y el texto final.

## Antes de leer: lo que cambió el mensaje

- **"80 % mayor eficiencia" y "100 % clientes satisfechos"** (están en el Wix) no tienen fuente ni método: se sacaron. Un comerciante escéptico los descarta en un segundo y arrastran la credibilidad del resto.
- **"Ahorro de más del 60 % frente a una ticketeadora fiscal"** (tefacturo.com.ar, 2019): dato viejo y sin base actual. Fuera.
- **No hay precio público.** La skill pide sección de precio; acá se reemplaza por lo que sí se puede afirmar del FAQ del sitio: plan mensual o anual, sin costo por factura, sin permanencia. El precio se da por WhatsApp.
- **"Te damos de alta en ARCA"** es falso: el trámite lo hace el titular del CUIT con su Clave Fiscal. Se dice "te guiamos en ARCA".
- **La pantalla del equipo en el fold son capturas reales de la app** (desde 2026-10-19, pendiente 1 resuelto): una venta de homologación en el alpha con productos ficticios sin marca (Yerba mate 1 kg, Leche entera 1 l, Galletitas surtidas 400 g), cobrada en efectivo y autorizada como Factura B 0001-00000244. Las imágenes están en `src/landing/app/`; si la pantalla de venta cambia, hay que volver a sacarlas. El ticket que sale es HTML con el formato y los datos del ticket térmico real de esa venta, sin los datos del emisor (nombre, CUIT, domicilio). Sin marcas de terceros ni el botón QR: Mercado Pago no se anuncia hasta validarlo con un comercio real.

## 0. Header

Para qué: marca y una salida a WhatsApp. Sin menú: cada link que no es la conversión es una fuga de tráfico pago.

- Logo (sin link a la home).
- Botón chico: **Hablar por WhatsApp**

## 1. Fold

Para qué: en 5 segundos, en el celular, entender qué es (sistema + equipo para facturar), ver que funciona, y tener un solo botón.

### Opción A (implementada)
- **Kicker:** Sistema de facturación electrónica
- **H1:** Facturá en segundos, con el cliente adelante.
- **Bajada:** App y equipo POS para facturar en el mostrador. Te guiamos en ARCA y te lo entregamos listo para emitir tu primera factura. (En celular la primera oración reemplaza al kicker, arriba del H1, y no hay bajada: el equipo va entre el título y el botón para que la venta se vea entera sin scrollear.)
- **CTA:** Quiero mi TeFacturo
- **Debajo del CTA:** Te respondemos por WhatsApp.
- **Línea de confianza:** Facturas A, B y C con CAE · Sin costo por factura · Sin permanencia
- **Visual:** un equipo POS con la app real que hace una venta en ~10 s (6 capturas): venta vacía, carrito, cobro, resumen, emitiendo, «Factura autorizada por ARCA», y sale el ticket impreso.

Riesgo: "en segundos" es una promesa de velocidad. Está en el sitio actual ("facturar en segundos") pero no está medida. Variante a testear si el cliente no la puede sostener: "Facturá con el cliente adelante."

### Opción B (para test A/B)
- **H1:** Dejá de facturar desde la página de ARCA.
- **Bajada:** igual que A.
- Por qué no es la A: le habla solo a quien ya usa Comprobantes en línea y deja afuera al que recién empieza. Sirve para un conjunto de anuncios segmentado a ese dolor.

## 2. El dolor

Para qué: que el lector se reconozca. Se muestra con los pasos de verdad en vez de adjetivos.

### Opción A (implementada)
- **H2:** En la web de ARCA, cada venta es un trámite.
- **Columna ARCA, "Comprobantes en línea":** Entrar con CUIT y Clave Fiscal · Abrir el servicio y elegir a quién representás · Elegir punto de venta y tipo de comprobante · Cargar fecha y concepto · Cargar los datos del cliente · Escribir el detalle de lo que vendiste · Confirmar · Descargar el PDF e imprimirlo
- **Columna TeFacturo, "3 pasos por venta":** Tocar los productos o escanear el código de barras · Elegir cómo paga · Emitir. El CAE se pide solo a ARCA y el ticket sale impreso en el momento.
- (Era "2 pasos"; Juan r1: la demo del fold muestra elegir el medio de pago, un lector escéptico cuenta 3. Se pasó a 3.)
- **Nota al pie:** Comprobantes en línea es gratis y válido. Si vendés todos los días en mostrador, se queda corto.

### Opción B
- **H2:** Hay gente esperando y la página de ARCA no carga.
- Por qué no es la A: afirma que la página falla, algo que no podemos medir ni probar. La A muestra pasos verificables.

## 3. Lo que tenés con TeFacturo

Para qué: responder "¿qué hace además de facturar?" con funciones concretas del PDF, sin adjetivos.

- **Kicker:** Además de facturar
- **H2:** Todo lo que pasa en el mostrador, en un solo lugar.
- **Productos cargados una vez.** Alta masiva desde Excel o CSV, código de barras, variantes y categorías. También imprimís las etiquetas de góndola.
- **Caja y reportes.** Apertura y cierre de caja. Ventas por día, por vendedor y por cliente. Usuarios con permisos por punto de venta.
- **En el equipo que tengas.** Android, Windows, Linux o web. O un equipo POS con impresora térmica, listo para usar.
- (Eran 6 tarjetas; Juan r1: genérico y repetía el fold. Se dejan las 3 cosas que la demo no muestra.)

## 4. Cómo empezás

Para qué: bajar el miedo al trámite. Es la objeción más fuerte del que nunca facturó.

- **H2:** Vos nos contás tu negocio. Del resto nos ocupamos con vos.
- **01. Nos escribís por WhatsApp.** Con tus datos fiscales y lo que vendés.
- **02. Te guiamos en ARCA.** El alta del punto de venta la hacés con tu Clave Fiscal, paso a paso con nosotros.
- **03. Configuramos el sistema.** Con tus productos, tu rubro y tu forma de trabajar.
- **04. Emitís tu primera factura.** En la app o en el equipo, que llega vinculado a tu cuenta.

## 5. Prueba (va en la misma sección que "Cómo empezás", a la derecha de los pasos)

Para qué: que hay un negocio real atrás. Solo datos que el cliente ya publica.

- **140+ comercios activos** facturando con TeFacturo (`ACTIVE_COMMERCES` en `tools/build_site.py`).
- **8+ años** en el mercado (se cuentan desde 2018 al año en curso: `SINCE_YEAR`).
- **Equipo propio en Coronel Suárez.** Mitre 1058. Soporte por WhatsApp, por mail y por chat dentro del sistema.
- Foto: comerciante emitiendo en un equipo POS (de la home actual).
- Sin testimonios hasta tenerlos con permiso escrito (pendiente 3).

## 6. Dudas antes de escribir

Para qué: matar las cuatro o cinco objeciones que frenan el clic. Respuestas cortas, todas salen del FAQ del sitio.

- **¿Las facturas son válidas?** Sí. Las autoriza ARCA con CAE, como cualquier factura electrónica.
- **¿Cuánto cuesta?** Plan mensual o anual según tu comercio, con actualizaciones, soporte y respaldo incluidos. Sin costo por factura. Te pasamos el precio por WhatsApp.
- **¿Tengo que firmar permanencia?** No. Cancelás cuando quieras. Si compraste un equipo, es tuyo.
- **¿Necesito una computadora?** No. Funciona en un celular o tablet Android, en una PC o en un equipo POS con impresora.
- **¿Y si nunca facturé?** Te guiamos en ARCA desde el alta del punto de venta. Si sabés usar WhatsApp, sabés usar TeFacturo.

## 7. El pedido

Para qué: cerrar con el mismo botón y, opcionalmente, calificar el lead en dos toques sin formulario.

- **H2:** Contanos de tu comercio y te armamos tu TeFacturo.
- **Bajada:** Si querés, contanos esto y seguimos por WhatsApp.
- **Pregunta 1 (opcional):** ¿Qué tenés? Kiosco o almacén · Ferretería · Ropa o calzado · Servicios · Otro rubro
- **Pregunta 2 (opcional):** ¿Cómo facturás hoy? En la web de ARCA · Con otro sistema · Todavía no facturo
- **CTA:** Seguir por WhatsApp
- **Mensaje que se abre:** "Hola, quiero mi TeFacturo. Tengo [rubro] y hoy [cómo factura]." (+ referencia de campaña si viene con `utm_campaign`, ver pendiente 4).
- **Debajo:** +54 9 2926 508200 · contacto@tefacturo.com.ar

## 8. Barra fija en celular

Para qué: el botón siempre a mano. En celular y tablet (<1000 px) aparece cuando el CTA del fold no está en pantalla; se oculta sobre el pedido final. En desktop, el header se vuelve fijo y su botón pasa a naranja.

- **Texto:** Quiero mi TeFacturo

## SEO y meta

La página es `noindex` (destino de anuncios), así que el título se escribe para la pestaña y para compartir, no para ranking.

- `<title>`: **Facturación electrónica para tu comercio | TeFacturo** (52 caracteres)
- Description: **App y equipo POS para facturar en el mostrador. Te guiamos en ARCA y te lo entregamos listo. Facturas A, B y C, sin costo por factura.** (134)

Volumen de búsqueda: **no medido** (no hay acceso a Keyword Planner desde acá). Las palabras salen de las guías ya publicadas ("facturación electrónica", "sistema de facturación", "ARCA"). Si la página se indexa más adelante, medir antes de elegir H1.

## Pasada adversarial (comerciante que usa Comprobantes en línea gratis y desconfía)

| Antes | Problema | Después |
|---|---|---|
| "80 % mayor eficiencia" | Sin fuente. "¿80 % de qué?" | Fuera. Se muestran los pasos de un lado y del otro. |
| "100 % clientes satisfechos" | Nadie se lo cree. | Fuera. 140+ comercios, 8+ años, dirección real. |
| "Te damos de alta en ARCA" | Falso: lo hace el titular. | "Te guiamos en ARCA… lo hacés con tu Clave Fiscal, paso a paso con nosotros." |
| "La página de ARCA se cae" | No lo podemos probar. | Se compara cantidad de pasos, que es verificable. |
| "Más barato" | No hay precio público. | "Sin costo por factura. Te pasamos el precio por WhatsApp." |
| "Reemplaza tu ticketeadora fiscal" | Depende del caso y del régimen. | No se dice. |

## Checklist anti-slop

| Regla | Resultado |
|---|---|
| Sin rayas (—) | OK |
| Sin emoji | OK |
| Sin "no es X, es Y" | OK (la opción B del H1 se descartó como A en parte por esto) |
| Sin listas de tres por reflejo | Funciones: 6. Pasos: 4. FAQ: 5. Línea de confianza: 3 (son los tres datos duros que hay; se deja). |
| Sin preguntas retóricas fuera del FAQ | OK |
| Palabras prohibidas (fácil, simple, rápido…) | "Simple" aparece en el sitio y en el manual de marca como atributo; acá no se usa. "En segundos" se mantiene (pendiente 2). |
| Frases de más de 20 palabras | Bajada del fold (24): la nuance (app + equipo + ARCA + listo) lo necesita. |
| Cada número con fuente | Ver tabla |

## Claims y fuentes

| Claim | Fuente |
|---|---|
| 140+ comercios activos | El cliente: 141 comercios activos al 2026-10-19 (el Wix decía 60+). Reconfirmar antes de pautar. |
| 8+ años de experiencia | El cliente: en el mercado desde 2018. El número se calcula al año en curso. |
| Facturas A, B y C con CAE automático y notas de crédito (las de débito no están implementadas: se sacaron del sitio el 2026-10-19) | PDF "Funcionalidades principales" |
| Alta masiva CSV/Excel, variantes, categorías | PDF |
| Código de barras, varios medios de pago por venta | PDF ("Punto de venta (POS)") |
| Impresión térmica, PDF, etiquetas de góndola | PDF |
| Cajas, reportes por fecha/vendedor/cliente | PDF |
| Android, Web, Windows, Linux | PDF ("Multiplataforma") |
| Roles admin, gerente, operador, visualizador | PDF |
| Plan mensual o anual, sin costo por factura | FAQ del sitio ("¿Cómo funciona el pago?", "¿Hay costos ocultos?") |
| Sin permanencia, el equipo es tuyo | FAQ ("¿Puedo cancelar cuando quiera?") |
| El alta en ARCA la hace el titular, con guía | FAQ ("¿Ustedes me dan de alta en ARCA…?") |
| Pasos de Comprobantes en línea | Flujo del servicio de ARCA (punto de venta y tipo → datos de emisión → receptor → operación → confirmar). Revisar contra una cuenta real antes de pautar. |
| Soporte por WhatsApp, mail y chat | FAQ ("¿Qué pasa si tengo un problema técnico?") |
| Dirección y teléfono | Sección Contacto del sitio |

## Pendientes para el cliente

1. ~~**Capturas reales de la app**~~ Hecho el 2026-10-19 (ver «Antes de leer»).
2. ¿Pueden sostener **"en segundos"**? Si tienen un tiempo medido de emisión (de tocar "Emitir" al ticket), mejor ponerlo con su base.
3. **Testimonios**: pedir a 3 comercios, con esta pregunta: "¿Cómo facturabas antes de TeFacturo y qué cambió en el mostrador?", y permiso escrito para nombre, rubro y foto.
4. ¿Agregamos la **referencia de campaña** (`utm_campaign`) al final del mensaje de WhatsApp para atribuir conversaciones? Está implementado; se apaga con `WA_REF = False` en `tools/landing.py`.
5. **IDs de medición**: Meta Pixel y Google Tag (GA4/Ads). Sin eso, la página no reporta conversiones. Se configuran en `tools/landing.py` (`META_PIXEL_ID`, `GTAG_ID`).
6. Reconfirmar **140+ comercios** el día que arranca la pauta (los años se actualizan solos).
