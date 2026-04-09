# Normativa Eléctrica para Datacenters IngeNova (División Francia)

## 1. Marco Aplicable y Reglamentación (Francia)
Todes las instalaciones y sistemas eléctricos dentro de los datacenters situados en territorio francés se rigen por la normativa NF C 15-100 para instalaciones de baja tensión. Los equipos de conmutación y protección deben contar con la certificación oficial del comité electrotécnico de Francia (UTE). Además, el suministro de alta tensión se regirá por los protocolos requeridos por Enedis y RTE.

## 2. Niveles de Redundancia de Suministro
A diferencia de otros territorios, el suministro de la red del estado francés suele considerarse de muy alta disponibilidad por su carga nuclear base. Sin embargo, IngeNova Francia exige para edificios A y B una redundancia mixta: N+2 para generadores diésel (Grupos Electrógenos) y 2N para las líneas de distribución interna del edificio.
La sectorización contra incendios entre los equipos de la ruta A y la ruta B debe aguantar un fuego clasificado como REI 120 (Resistencia, Estanqueidad y Aislamiento durante 120 minutos).

## 3. Baterías y Sistemas de Alimentación Ininterrumpida (SAI)
En los datacenters franceses se prohíbe el uso en nuevas construcciones de tecnologías VRLA (Plomo) por normativas ecológicas estrictas, implantándose de forma obligatoria baterías de iones de litio u otros medios libres de plomo (ej. volantes de inercia o "flywheels").
La autonomía exigida mínima desde que se produce el corte de red hasta que los grupos electrógenos estabilizan su tensión y asumen la carga es de tan solo 10 minutos al 100% de la carga de potencia crítica (Cooling e IT). La revisión del BMS se realizará obligatoriamente cada 6 meses.

## 4. Diseño del Sistema de Tomas de Tierra
Las normativas NF limitan drásticamente las corrientes parasitarias toleradas. Por ello, la resistencia de las tomas de tierra del edificio principal debe estar por debajo de los 3 ohmios (más estricto que en otras divisiones). Todo chasis, estructura metálica de contención térmica (pasillos) y las propias bandejas de techo tipo "Cablofil" deben estar unidas al bus de tierra principal del centro de datos usando un cable amarillo/verde de sección mínima 25 mm2.

## 5. Cuadros de Distribución (PDUs y RPL)
Todos los Racks requieren alimentación dual. En las PDUs francesas es obligatorio que se disponga de protección diferencial por agrupamiento y dispositivos de supervisión del aislamiento (CPI) en caso de configuración de red en Esquema IT. 
Los cables y regletas deben cumplir colores: Blanco para la línea A, Preto para la línea B. Las alarmas de consumo excedido en SNMP v3 saltarán automáticamente si la PDU detecta un balanceo que supera el 80% en cualquier fase.
