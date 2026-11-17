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
