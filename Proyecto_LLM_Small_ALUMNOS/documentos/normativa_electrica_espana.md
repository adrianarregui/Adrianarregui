# Normativa Eléctrica para Datacenters IngeNova (División España)

## 1. Marco Aplicable y Reglamentación (España)
Todo diseño e instalación eléctrica en los edificios de tipo Datacenter operados en el territorio español debe cumplir con el Reglamento Electrotécnico para Baja Tensión (REBT) y sus Instrucciones Técnicas Complementarias (ITC), prestando especial atención a la ITC-BT-28 relativa a locales de pública concurrencia y centros de proceso de datos. Las instalaciones de Alta Tensión deben ajustarse al RAT (Reglamento sobre Condiciones Técnicas y Garantías de Seguridad en Instalaciones Eléctricas de Alta Tensión).

## 2. Niveles de Redundancia de Suministro
En España, dadas las fluctuaciones reportadas en la red eléctrica durante la fase estival, todo datacenter de clase A y B de IngeNova debe contar con una redundancia nivel 2N (Dos sistemas de suministro eléctrico independientes, con dos generadores de respaldo), separados físicamente mediante pasillos cortafuegos (sectorización). 
El uso de configuración N+1 solo se permite para instalaciones de tipo Edge (Microdatacenters perimetrales menores a 100 kW de consumo).

## 3. Baterías y Sistemas de Alimentación Ininterrumpida (SAI)
Según la norma corporativa española, los SAIs deben garantizar la continuidad absoluta del suministro con una autonomía mínima de carga del 100% durante:
- 15 minutos (para baterías clásicas tipo VRLA o Plomo-Ácido).
- 25 minutos (para sistemas basados en litio con gestión inteligente de BMS - Battery Management System).
Las baterías de plomo deben someterse a revisiones y descargas completas controladas de forma trimestral. Las baterías de iones de litio podrán revisarse anualmente.

## 4. Diseño del Sistema de Tomas de Tierra
La resistividad del terreno en gran parte de las sedes españolas requiere mallas de cobre de alta densidad. La resistencia óhmica final de las tomas de tierra del edificio no debe superar bajo ningún concepto los 5 ohmios. 
Cualquier rack, pasillo frío, estructura metálica del falso suelo y canaleta debe estar equipotencialmente conectada.

## 5. Cuadros de Distribución (PDUs y RPL)
Los Racks se alimentarán a través de dos líneas (A y B) desde diferentes Unidades de Distribución de Energía (PDU). El color de las regletas, cables y bases debe ser Rojo para la línea A y Azul para la línea B. Las PDUs tienen que incluir monitoreo por toma de corriente (outlet-level) e integrarse vía SNMP v3 en el DCIM de la compañía española. Las alarmas de sobrecarga se dispararán al 75% del límite nominal (16A o 32A).
