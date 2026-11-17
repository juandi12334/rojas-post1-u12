# Impacto de la computación cuántica en la seguridad de la información: análisis post-cuántico

**Autor:** Juan Diego Rojas Rey (código 1152512)
**Materia:** Arquitectura de Computadores, Ingeniería de Sistemas, UFPS
**Unidad 12 — Parte 2**

---

## Introducción

La criptografía que protege hoy la web, las VPN, las firmas digitales y la mayor parte de los registros electrónicos descansa sobre dos problemas matemáticos, la factorización de enteros y el logaritmo discreto, que un computador clásico no resuelve en tiempo razonable. El algoritmo de Shor resuelve ambos en tiempo polinomial sobre un computador cuántico suficientemente grande, y el algoritmo de Grover reduce la búsqueda exhaustiva a su raíz cuadrada. Ninguno de los dos se puede ejecutar hoy sobre claves reales. Las estimaciones de recursos, sin embargo, bajan con cada trabajo nuevo: en 2019 se calculaba que factorizar un RSA de 2048 bits requería unos 20 millones de qubits ruidosos durante 8 horas, y una estimación de 2025 lo reduce a menos de un millón de qubits ruidosos y menos de una semana (Gidney, 2025). Ese ritmo explica que las agencias de seguridad pidan empezar a migrar antes de que exista la máquina, y no después (CISA, NSA y NIST, 2023).

En la Parte 1 de este laboratorio se simularon circuitos de 2 qubits con ruido y se vio que el error acumulado destruye la señal al alargar el circuito (con 162 puertas CZ y 1 % de error por puerta, Grover cayó a 40 % de éxito). Esa misma limitación es la que mantiene a los computadores cuánticos actuales lejos de romper RSA: factorizar una clave de 2048 bits exige corrección de errores a gran escala. Aun así, la migración no se puede dejar para el día en que esa máquina exista, por la amenaza de *harvest now, decrypt later* (HNDL), en la que un adversario guarda hoy tráfico cifrado para descifrarlo en el futuro.

Este documento sigue la estructura pedida. La sección 1 clasifica los algoritmos actuales según su vulnerabilidad. La sección 2 compara los tres estándares post-cuánticos publicados por el NIST en agosto de 2024 (FIPS 203, 204 y 205). La sección 3 plantea un plan de migración para tres perfiles organizacionales, y la sección 4 cuantifica el crecimiento de claves y firmas y su efecto en un handshake TLS 1.3 híbrido. Después se justifican las dos decisiones técnicas de esta parte y se cierra con conclusiones y referencias. Las cifras de tamaño provienen de los documentos FIPS y de las especificaciones de implementación citadas; donde un dato no es oficial o se calculó, se indica.

## 1. Inventario de algoritmos criptográficos vulnerables

La Tabla 1 clasifica los algoritmos en uso. La clave está en distinguir dos niveles de daño. Los algoritmos "rotos completamente" caen ante Shor con una máquina suficientemente grande y esa ruptura es retroactiva: quien guardó el tráfico puede descifrarlo después. Los "debilitados" pierden margen de seguridad frente a Grover, pero siguen siendo seguros si se usa un tamaño adecuado.

**Tabla 1. Inventario y vulnerabilidad cuántica**

| Algoritmo | Tipo | Vulnerabilidad cuántica | Algoritmo atacante | Acción recomendada |
|---|---|---|---|---|
| RSA-2048 / 3072 / 4096 | Cifrado y firma asimétricos | Roto completamente | Shor (factorización, polinomial en el tamaño de la clave) | Reemplazar: ML-KEM (establecimiento de claves) y ML-DSA/SLH-DSA (firmas) |
| ECDSA (P-256, P-384) | Firma digital | Roto completamente | Shor (logaritmo discreto en curvas elípticas) | Reemplazar con ML-DSA (o SLH-DSA como respaldo) |
| ECDH / X25519 | Intercambio de claves | Roto completamente | Shor | Reemplazar con ML-KEM; en transición, usar híbrido X25519 + ML-KEM-768 |
| Ed25519 | Firma digital | Roto completamente | Shor | Reemplazar con ML-DSA |
| Diffie-Hellman finito (DH-2048) | Intercambio de claves | Roto completamente | Shor | Reemplazar con ML-KEM |
| AES-128 | Cifrado simétrico | Debilitado: 128 bits clásicos, unos 64 bits en el modelo ideal de Grover | Grover, O(√N) | Preferir AES-256 en datos de larga vida |
| AES-256 | Cifrado simétrico | Aceptable: unos 128 bits efectivos | Grover | Mantener |
| SHA-256 | Función hash | Preimagen 2²⁵⁶ → 2¹²⁸ con Grover; la resistencia a colisiones baja en teoría de 2¹²⁸ a 2⁸⁵ | Grover y variantes | Usar SHA-384 o SHA-512 en sistemas nuevos de larga vida |
| SHA-3-256 | Función hash | Equivalente a SHA-256 | Grover | Usar SHA-3-384 o mayor cuando se necesite margen |

**Análisis.** Los cinco primeros algoritmos son asimétricos y caen todos por la misma razón: su seguridad se apoya en factorizar o en calcular logaritmos discretos, problemas que Shor resuelve en tiempo polinomial. No hay "aumentar el tamaño de la clave" como defensa, porque con Shor basta crecer algo la máquina. Por eso la única solución es cambiar de familia de algoritmos. Los simétricos y los hash, en cambio, solo sufren la raíz cuadrada de Grover, y la regla práctica es duplicar el tamaño de la clave o de la salida: AES-256 y SHA-384/512 cubren el caso.

Hay dos matices que conviene dejar claros. El primero es que el "64 bits efectivos" de AES-128 es el valor del modelo ideal. Grover no se puede paralelizar bien: dividir la búsqueda en máquinas independientes reduce la ventaja cuadrática. Jaques et al. (2020) estimaron el costo en puertas de un oráculo de Grover para AES, y el NIST define sus categorías de seguridad post-cuánticas a partir de ese costo, no del valor teórico de 2⁶⁴; por eso el NIST mantiene AES-128, 192 y 256 como válidos para sus categorías de seguridad. En este documento se recomienda AES-256 para datos de larga vida por prudencia, no porque AES-128 esté roto. El segundo matiz es que la cifra de 2⁸⁵ para colisiones en SHA-256 es teórica, y no hay un ataque cuántico práctico a colisiones que justifique cambiar de hash de inmediato; el cambio a SHA-384/512 es una medida de margen.

La diferencia con consecuencias para la migración es la siguiente. Que un asimétrico esté "roto" compromete retroactivamente la confidencialidad de todo lo que se cifró con él y se guardó, y por eso el intercambio de claves es lo más urgente. Un algoritmo "debilitado" reduce el margen pero no expone datos pasados.

## 2. Estándares NIST PQC (2024)

El NIST publicó el 13 de agosto de 2024 los tres primeros estándares de criptografía post-cuántica: FIPS 203 (ML-KEM), FIPS 204 (ML-DSA) y FIPS 205 (SLH-DSA) (NIST, 2024a, 2024b, 2024c). Dos de ellos nacen de las propuestas CRYSTALS-Kyber y CRYSTALS-Dilithium, y el tercero de SPHINCS+.

### ML-KEM (FIPS 203)

Es un mecanismo de encapsulamiento de claves (KEM) basado en el problema Module Learning With Errors (MLWE) sobre retículos. No cifra mensajes ni firma: permite que dos partes establezcan un secreto compartido de 32 bytes. Reemplaza a ECDH, X25519 y DH finito, y al uso de RSA para transportar claves.

**Tabla 2. Parámetros de ML-KEM (bytes)**

| Conjunto | Nivel NIST | Clave de encapsulación (pública) | Clave de desencapsulación (privada) | Ciphertext |
|---|---|---|---|---|
| ML-KEM-512 | 1 (≈ AES-128) | 800 | 1632 | 768 |
| ML-KEM-768 | 3 (≈ AES-192) | 1184 | 2400 | 1088 |
| ML-KEM-1024 | 5 (≈ AES-256) | 1568 | 3168 | 1568 |

Fuente: NIST (2024a); valores verificados contra las tablas de parámetros de liboqs (Open Quantum Safe, s. f.).

### ML-DSA (FIPS 204)

Es un esquema de firma digital basado en MLWE (retículos). Reemplaza a ECDSA, Ed25519 y a las firmas RSA.

**Tabla 3. Parámetros de ML-DSA (bytes)**

| Conjunto | Nivel NIST | Clave pública | Clave privada | Firma |
|---|---|---|---|---|
| ML-DSA-44 | 2 | 1312 | 2560 | 2420 |
| ML-DSA-65 | 3 | 1952 | 4032 | 3309 |
| ML-DSA-87 | 5 | 2592 | 4896 | 4627 |

Fuente: NIST (2024b), valores reproducidos por la implementación de Go (The Go Authors, s. f.) y por la documentación de Encryption Consulting (2024). Frente a ECDSA P-256, cuya firma ocupa unos 64 a 72 bytes, la firma de ML-DSA-65 es unas 46 veces mayor (3309 / 72 ≈ 46). La publicación del equipo de Chrome habla de claves y firmas de unas 40 veces el tamaño de las de ECDSA (Google, 2024), que es consistente con ese orden de magnitud. En velocidad, el costo de CPU de ML-KEM y ML-DSA es manejable; el problema son los bytes, no los ciclos (Ristic, 2026). No se encontró en las fuentes consultadas una tabla de ciclos por operación publicada por el NIST, por lo que no se reporta una cifra de velocidad propia para ML-DSA.

### SLH-DSA (FIPS 205)

Es un esquema de firma sin estado basado únicamente en funciones hash (derivado de SPHINCS+). Reemplaza a ECDSA y RSA en firmas, igual que ML-DSA, pero con otra asunción de seguridad. FIPS 205 define 12 conjuntos de parámetros, con SHA-2 o SHAKE, tres niveles de seguridad y variantes pequeñas (*s*) o rápidas (*f*) (DigiCert, s. f.).

**Tabla 4. Parámetros de SLH-DSA (bytes; iguales para SHA2 y SHAKE)**

| Conjunto | Nivel NIST | Clave pública | Clave privada | Firma |
|---|---|---|---|---|
| SLH-DSA-128s | 1 | 32 | 64 | 7856 |
| SLH-DSA-128f | 1 | 32 | 64 | 17 088 |
| SLH-DSA-192s | 3 | 48 | 96 | 16 224 |
| SLH-DSA-192f | 3 | 48 | 96 | 35 664 |
| SLH-DSA-256s | 5 | 64 | 128 | 29 792 |
| SLH-DSA-256f | 5 | 64 | 128 | 49 856 |

Fuente: NIST (2024c); valores confirmados con DigiCert (s. f.) y el registro de PQ Crypto (Project Eleven, s. f.). En velocidad, el propio NIST indica que el conjunto más pequeño, SLH-DSA-SHA2-128s, firma con unas 2,2 millones de llamadas hash, cerca de 0,2 segundos en un Xeon de 3,1 GHz, y que es "demasiado grande para muchas aplicaciones" (Dang, 2025). La firma es lenta, pero la verificación es rápida.

**Por qué SLH-DSA es más conservador.** Su seguridad depende solo de que la función hash resista colisiones y segundas preimágenes, una asunción que se conoce desde hace décadas y que no depende de la dificultad de un problema algebraico estructurado. ML-DSA y ML-KEM descansan en MLWE, que tiene muchos menos años de criptoanálisis. Por eso SLH-DSA se recomienda como respaldo (diversidad criptográfica) cuando un avance contra los retículos dejara a ML-DSA comprometido, y para casos donde el tamaño de la firma sea tolerable, como certificados raíz.

**Qué reemplaza a qué.** ML-KEM reemplaza el intercambio de claves (ECDH, X25519, DH, transporte RSA). ML-DSA y SLH-DSA reemplazan las firmas (ECDSA, Ed25519, RSA). ML-KEM no sirve para firmar, y los dos esquemas de firma no sirven para intercambiar claves.

## 3. Plan de migración para tres perfiles

### Marco de referencia

Tres referencias fijan los plazos. La primera es la hoja informativa conjunta de CISA, NSA y NIST (2023), que recomienda crear una hoja de ruta de preparación cuántica, un inventario criptográfico, evaluar el riesgo y consultar a los proveedores. La segunda es el informe NIST IR 8547, en su versión final del 27 de octubre de 2026, que deprecia los algoritmos asimétricos vulnerables después de 2030 y los prohíbe después de 2035 (según el resumen de PostQuantum.com, 2026; el documento primario no se pudo consultar directamente). La tercera es CNSA 2.0 de la NSA, obligatoria para sistemas de seguridad nacional, que exige ML-KEM-1024, ML-DSA-87, AES-256 y SHA-384/512, con LMS o XMSS para firma de software y firmware, y que fija el uso exclusivo de estos algoritmos entre 2030 y 2033 según la categoría de tecnología (Encryption Consulting, 2026).

El método es común a los tres perfiles: (1) inventario de sistemas con criptografía asimétrica activa, (2) clasificación de los datos por horizonte de sensibilidad, (3) criptografía híbrida (clásica y post-cuántica en paralelo) durante la transición, (4) cronograma por fases con hitos verificables, y (5) riesgos y mitigaciones. La prioridad la dicta el horizonte de los datos: cuanto más larga es la vida de un dato confidencial, antes hay que proteger su intercambio de claves.

### Perfil A: hospital universitario (datos de 50 a 75 años)

**Inventario.** Portal de pacientes con TLS, VPN de las sedes, firma de prescripciones con ECDSA, PKI interna, copias de seguridad y bases de datos (cifradas con AES, pero con claves envueltas o transportadas con RSA/ECC), y dispositivos médicos con firmware firmado.

**Clasificación.** La historia clínica es confidencial durante toda la vida del paciente, por lo que el tráfico del portal y de las VPN es el caso típico de HNDL: lo que se capture hoy puede seguir siendo sensible dentro de 15 años o más. Las prescripciones son un problema de autenticidad, no de confidencialidad.

**Estrategia híbrida.** Intercambio de claves híbrido X25519 + ML-KEM-768 en el portal y en las VPN lo antes posible; firmas duales (ECDSA más ML-DSA-65) en las prescripciones durante la transición; AES-256 en todo dato en reposo de larga vida.

**Cronograma.**

| Fase | Plazo | Hito verificable |
|---|---|---|
| 1. Inventario | Primer semestre de 2027 | Inventario criptográfico completo, con cada sistema clasificado por horizonte de datos |
| 2. Confidencialidad | 2027 | Portal y VPN negociando X25519MLKEM768; se verifica con captura de handshake |
| 3. PKI y HSM | 2028 | PKI interna de prueba con ML-DSA-65; HSM o proveedor con soporte confirmado |
| 4. Firmas | 2029 | Prescripciones con firma dual ECDSA + ML-DSA-65 en producción |
| 5. Retiro de lo clásico | Antes de 2030 y completo antes de 2035 | Sin ECDSA/RSA en uso, cumpliendo la depreciación de NIST IR 8547 |

**Riesgos y mitigaciones.** Los HSM y los lectores de tarjetas pueden no soportar claves de 4 KB (mitigación: exigir soporte a los proveedores y probar antes de comprar). Los dispositivos médicos con firmware antiguo no se actualizan (mitigación: segmentar la red y priorizar su reemplazo). Los middleboxes pueden romper un ClientHello más grande (mitigación: pruebas en el piloto antes del despliegue general).

### Perfil B: startup de comercio electrónico (datos de 5 a 7 años)

**Inventario.** TLS 1.3 (X25519 y ECDSA) en la tienda y las API, cifrado AES-256, datos de tarjeta bajo PCI-DSS, firmas de webhooks y de JWT, y dependencia de un CDN o proveedor de nube.

**Clasificación.** Los datos tienen una vida corta, de 5 a 7 años. La amenaza HNDL existe, pero la urgencia es menor que en salud. La ventaja competitiva es ofrecer compatibilidad con clientes post-cuánticos.

**Estrategia híbrida.** Activar X25519MLKEM768 en el CDN y los balanceadores (los navegadores principales ya lo negocian), dejar los certificados clásicos hasta que la PKI web ofrezca firmas post-cuánticas y evaluar PQC puro más adelante.

**Cronograma.**

| Fase | Plazo | Hito verificable |
|---|---|---|
| 1. Inventario | 2027 | Lista de dependencias criptográficas, incluidas librerías y proveedores |
| 2. Híbrido en el borde | 2027 | X25519MLKEM768 activo en CDN y balanceadores; porcentaje de conexiones híbridas medido |
| 3. Firmas internas | 2029 a 2030 | JWT y webhooks migrados a ML-DSA o doble firma, según soporte de las librerías |
| 4. Revisión | 2030 | Decisión documentada sobre mantener el híbrido o pasar a PQC puro |

**Riesgos y mitigaciones.** El handshake más grande puede aumentar la latencia en redes móviles con pérdida (mitigación: medir antes y después, como se detalla en la sección 4). Una dependencia de un solo proveedor limita el control (mitigación: exigir al proveedor un cronograma PQC por contrato).

### Perfil C: entidad gubernamental de defensa (datos de 25 a 50 años)

**Inventario.** Comunicaciones clasificadas, PKI nacional, VPN entre agencias, firma de documentos oficiales, firmware y software firmados, y sistemas heredados.

**Clasificación.** Datos de muy larga vida. La migración no es opcional: CNSA 2.0 es mandatoria para sistemas de seguridad nacional.

**Estrategia.** Usar directamente los conjuntos de máximo nivel que fija CNSA 2.0: ML-KEM-1024 y ML-DSA-87, AES-256 y SHA-384/512, con LMS o XMSS para firma de software y firmware. SLH-DSA queda excluido de los sistemas de seguridad nacional (PostQuantum.com, 2025). Se pueden mantener híbridos clásicos cuando una interoperabilidad lo exija, pero el objetivo final es solo CNSA 2.0.

**Cronograma (según las categorías de CNSA 2.0).**

| Categoría | Soportar y preferir | Uso exclusivo |
|---|---|---|
| Firma de software y firmware | 2025 | 2030 |
| Navegadores, servidores y servicios en la nube | 2025 | 2033 |
| Redes tradicionales (VPN, routers) | 2026 | 2030 |
| Sistemas operativos | 2027 | 2033 |

La meta general para sistemas de seguridad nacional es 2035, alineada con NSM-10 (Encryption Consulting, 2026).

**Riesgos y mitigaciones.** El equipo heredado sin actualización (mitigación: reemplazo planificado hasta 2033). Los certificados y la PKI son difíciles de reemplazar en bloque (mitigación: dobles jerarquías en paralelo). La dependencia de proveedores que no cumplen CNSA 2.0 (mitigación: exigir validación de cumplimiento en las compras).

### Justificación de la priorización

El orden Perfil C, Perfil A, Perfil B responde al horizonte de los datos y a si hay una obligación externa. C tiene obligación regulatoria y datos de hasta 50 años. A no tiene una norma que lo obligue de inmediato, pero sus datos duran más que cualquier otro perfil y están expuestos a HNDL en el portal. B tiene el horizonte más corto y puede apoyarse en su CDN para la parte de confidencialidad con poco esfuerzo propio.

## 4. Tamaños de claves y firmas: PQC frente a criptografía clásica y su efecto en TLS 1.3 híbrido

**Tabla 5. Comparación de tamaños (bytes)**

| Algoritmo | Tipo | Clave pública | Clave privada | Firma / ciphertext | Nivel de seguridad NIST |
|---|---|---|---|---|---|
| RSA-3072 | Cifrado/firma clásico | ~400 | ~1600 | 384 (firma) | ~128 bits clásicos (no post-cuántico) |
| ECDSA P-256 | Firma clásica | 64 | 32 | ~70 a 72 (DER) | ~128 bits clásicos (no post-cuántico) |
| X25519 | Intercambio de claves clásico | 32 | 32 | N/A (no es firma) | ~128 bits clásicos (no post-cuántico) |
| ML-KEM-768 (FIPS 203) | KEM post-cuántico | 1184 | 2400 | 1088 (ciphertext) | Nivel 3 (≈ AES-192) |
| ML-DSA-65 (FIPS 204) | Firma post-cuántica | 1952 | 4032 | 3309 | Nivel 3 (≈ AES-192) |
| SLH-DSA-128s (FIPS 205) | Firma post-cuántica (hash) | 32 | 64 | 7856 | Nivel 1 (≈ AES-128) |

Los tamaños de los tres algoritmos post-cuánticos salen de los documentos FIPS 203, 204 y 205 (NIST, 2024a, 2024b, 2024c), ya contrastados en la sección 2. Los tamaños de RSA-3072, ECDSA P-256 y X25519 no vienen de esos documentos: son los tamaños estándar de cada esquema (el módulo para RSA, el punto sin comprimir para la curva y la clave de 32 bytes de X25519), y los de RSA son aproximados porque el formato de la clave privada varía.

**Crecimiento.** La clave pública de ML-KEM-768 es unas 37 veces mayor que la de X25519 (1184 / 32 = 37). La firma de ML-DSA-65 es unas 46 veces mayor que una firma ECDSA P-256 (3309 / 72 ≈ 46) y su clave pública unas 30 veces mayor (1952 / 64 ≈ 30). SLH-DSA-128s tiene claves diminutas (32 bytes) pero una firma de 7856 bytes, unas 2,4 veces la de ML-DSA-65 (7856 / 3309 ≈ 2,4).

### Impacto en un handshake TLS 1.3 híbrido

**Intercambio de claves.** En el grupo híbrido X25519MLKEM768, el `key_share` del cliente es la concatenación de la clave de encapsulación de ML-KEM-768 y la de X25519: 1216 bytes (1184 + 32), y la respuesta del servidor son 1120 bytes (1088 + 32). Estos tamaños aparecen en la especificación de IETF (Kwiatkowski et al., 2026). Frente a los 32 bytes de X25519 solo, el cliente envía 1184 bytes más y el servidor 1088 bytes más. Con los demás campos, el ClientHello pasa a ocupar cerca de 1300 a 1500 bytes (Encryption Consulting, 2026), un valor del orden de un segmento TCP típico (unos 1460 bytes de carga útil). El equipo de Chrome reportó un aumento de alrededor de 4 % en la latencia del handshake al desplegar ML-KEM, por los bytes adicionales y la fragmentación (según Ristic, 2026). El crecimiento del intercambio de claves casi nunca agrega una ida y vuelta completa, pero no es gratis.

**Autenticación.** El cambio grande es el de las firmas. Un handshake TLS típico lleva dos claves públicas y cinco firmas (Google, 2024). Con los tamaños de la Tabla 5, el cálculo propio es:

| Cadena de autenticación | Cálculo | Total aproximado |
|---|---|---|
| ECDSA P-256 | 2 × 64 + 5 × 72 | ≈ 0,5 KB (488 bytes) |
| ML-DSA-65 | 2 × 1952 + 5 × 3309 | ≈ 20,4 KB (20 449 bytes) |

Es unas 42 veces más (20 449 / 488), muy cerca del "unas 40 veces" que reporta el equipo de Chrome. Con una ventana de congestión inicial de 10 segmentos (Chu et al., 2013; unos 14 600 bytes), la respuesta del servidor con la cadena ML-DSA ya no cabe en el primer vuelo y exige al menos una ronda de red adicional, mientras que una cadena ECDSA sí cabe con holgura. Cuando se suman los certificados de transparencia, el overhead de una cadena de profundidad 2 con ML-DSA-65 llega a unas 32 veces el de Ed25519 (Encryption Consulting, 2026).

**Conclusión.** El intercambio híbrido de claves tiene un costo pequeño que, en redes con buena conectividad, normalmente cabe en el primer vuelo. La autenticación con ML-DSA es la que puede añadir rondas y fragmentación, sobre todo en redes con alta latencia o pérdida de paquetes. Esto justifica el orden de la migración: primero el intercambio de claves (que además es lo que protege contra HNDL) y después las firmas y certificados.
