# Primer Parcial - Seguridad de Redes

**Autor:** Junior Javier Santos Perez  
**Matrícula:** 2024-1599

**Repositorio GitHub:**

**Video demostrativo:**
https://www.youtube.com/watch?v=dcpJeWhHLSY 
---

## Tabla de Contenidos
1. Descripción General
2. Topología de Red
3. Direccionamiento IP
4. Configuración de VLANs
5. Router-on-a-Stick
6. DHCP
7. Configuración de Switches
8. OSPF con Autenticación
9. NAT
10. SSH y Acceso Remoto
11. Banner de Advertencia
12. Port-Security
13. Listas de Control de Acceso (ACL)
14. Controles de Seguridad Adicionales
15. Ataques Realizados
    - DNS Spoofing / DNS Poisoning
    - DHCP Starvation
16. Contramedidas Implementadas

---

## Descripción General
Esta práctica implementa una infraestructura de red segmentada y segura compuesta por dos routers (R1 e ISP/R2), un switch central (SW-CENTRAL) y dos switches de acceso (SW-1, SW-2). Se implementan dos VLANs, enrutamiento dinámico OSPF con autenticación MD5, traducción de direcciones NAT, acceso remoto SSH y múltiples controles de seguridad. Adicionalmente, se realizan y documentan dos ataques de red con sus respectivas contramedidas.

---

## Topología de Red

---

## Direccionamiento IP

| Dispositivo | Interfaz | Dirección IP | Descripción |
|-------------|----------|--------------|-------------|
| R1 | g0/0.10 | 10.15.99.1/26 | Gateway VLAN ADMIN |
| R1 | g0/0.20 | 10.15.99.65/26 | Gateway VLAN USUARIOS |
| R1 | fa0/1 | 200.1.1.1/30 | Enlace WAN hacia ISP |
| R2 (ISP) | fa0/1 | 200.1.1.2/30 | Enlace WAN hacia R1 |
| SW-CENTRAL | VLAN 10 | 10.15.99.2/26 | Gestión del switch |
| SW-1 | VLAN 10 | 10.15.99.3/26 | Gestión del switch |
| SW-2 | VLAN 10 | 10.15.99.4/26 | Gestión del switch |


----------------------------------------
Swichs/Router

User: admin
Password: cisco
-----------------------------------------

### Subredes Utilizadas

| VLAN | Nombre | Red | Máscara | Gateway | Rango Usable |
|------|--------|-----|---------|---------|--------------|
| 10 | ADMIN | 10.15.99.0/26 | 255.255.255.192 | 10.15.99.1 | 10.15.99.2 – 10.15.99.62 |
| 20 | USUARIOS | 10.15.99.64/26 | 255.255.255.192 | 10.15.99.65 | 10.15.99.66 – 10.15.99.126 |
| 999 | NATIVE | N/A | N/A | N/A | VLAN nativa (sin usuarios) |

---

## Configuración de VLANs
Las VLANs se configuran de forma idéntica en los tres switches (SW-CENTRAL, SW-1, SW-2):

```
configure terminal
vlan 10
 name ADMIN
vlan 20
 name USUARIOS
vlan 999
 name NATIVE
end
```

La VLAN 999 se utiliza como VLAN nativa en todos los enlaces trunk, en sustitución de la VLAN 1 por defecto, cumpliendo con la buena práctica de seguridad que exige el enunciado (cambiar la VLAN por defecto por una VLAN no utilizada para usuarios).

### Puertos de Acceso

SW-1 — Equipos de usuarios:
```
configure terminal
interface g0/0
 switchport mode access
 switchport access vlan 20
end
write
```

SW-2 — Equipos de usuarios:
```
configure terminal
interface range g0/1-2
 switchport mode access
 switchport access vlan 20
end
write
```

### Puertos Trunk

SW-CENTRAL → Router (g0/0):
```
configure terminal
interface g0/0
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,999
end
write
```

SW-CENTRAL → SW-1 (g0/1):
```
configure terminal
interface g0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,999
end
write
```

SW-CENTRAL → SW-2 (g0/2):
```
configure terminal
interface g0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,999
end
write
```

SW-1 → SW-CENTRAL (g0/1):
```
configure terminal
interface g0/1
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,999
end
write
```

SW-2 → SW-CENTRAL (g0/0):
```
configure terminal
interface g0/0
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,999
end
write
```

---

## Router-on-a-Stick
Configurado en R1 para enrutar el tráfico entre las VLANs 10 y 20 a través de subinterfaces sobre la interfaz g0/0:

```
interface g0/0.10
 encapsulation dot1Q 10
 ip address 10.15.99.1 255.255.255.192

interface g0/0.20
 encapsulation dot1Q 20
 ip address 10.15.99.65 255.255.255.192
```

Cada subinterfaz actúa como gateway predeterminado para su VLAN correspondiente.

---

## DHCP
El servidor DHCP se configura en R1, con exclusiones para las IPs de los gateways y dispositivos de gestión:

```
configure terminal

! Exclusiones de IPs estáticas
ip dhcp excluded-address 10.15.99.1
ip dhcp excluded-address 10.15.99.65

! Pool VLAN ADMIN
ip dhcp pool ADMIN
 network 10.15.99.0 255.255.255.192
 default-router 10.15.99.1
 dns-server 8.8.8.8

! Pool VLAN USUARIOS
ip dhcp pool USUARIOS
 network 10.15.99.64 255.255.255.192
 default-router 10.15.99.65
 dns-server 8.8.8.8

end
```

---

## Configuración de Switches
La siguiente configuración base aplica a SW-CENTRAL, SW-1 y SW-2 (ajustando hostname e IP de gestión según corresponda):

### SW-CENTRAL
```
enable
configure terminal
hostname SW-CENTRAL
no ip domain-lookup
interface vlan 10
 ip address 10.15.99.2 255.255.255.192
 no shutdown
ip default-gateway 10.15.99.1
end
write
```

### SW-1
```
enable
configure terminal
hostname SW-1
no ip domain-lookup
interface vlan 10
 ip address 10.15.99.3 255.255.255.192
 no shutdown
ip default-gateway 10.15.99.1
end
write
```

### SW-2
```
enable
configure terminal
hostname SW-2
no ip domain-lookup
interface vlan 10
 ip address 10.15.99.4 255.255.255.192
 no shutdown
ip default-gateway 10.15.99.1
end
write
```

La interfaz VLAN 10 permite la administración remota de cada switch vía SSH desde la red de gestión.

---

## OSPF con Autenticación
Se utiliza OSPF área 0 con autenticación MD5 en el enlace WAN entre R1 y R2 (ISP).

### R1
```
configure terminal
interface fa0/1
 ip address 200.1.1.1 255.255.255.252
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 cisco123
 no shutdown

router ospf 1
 network 10.15.99.0 0.0.0.255 area 0
 network 200.1.1.0 0.0.0.3 area 0
end
```

### R2 (ISP)
```
configure terminal
interface fa0/1
 ip address 200.1.1.2 255.255.255.252
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 cisco123
 no shutdown

router ospf 1
 network 200.1.1.0 0.0.0.3 area 0
end
```

La autenticación MD5 garantiza que solo routers legítimos con la clave correcta pueden formar adyacencias OSPF, previniendo ataques de inyección de rutas.

---

## NAT
Se configura NAT con sobrecarga (PAT) en R1 para permitir que los hosts internos accedan a Internet usando la IP pública del enlace WAN.

```
configure terminal

! ACL que define el tráfico interno
access-list 1 permit 10.15.99.0 0.0.0.255

! Interfaces NAT
interface fa0/0
 ip nat inside
interface fa0/1
 ip nat outside

! NAT overload (PAT)
ip nat inside source list 1 interface fa0/1 overload

! Ruta por defecto hacia ISP
ip route 0.0.0.0 0.0.0.0 200.1.1.2

end
write
```

### Ruta de retorno en R2 (ISP)
```
configure terminal
ip route 10.15.99.0 255.255.255.0 200.1.1.1
end
write
```

---

## SSH y Acceso Remoto
Se configura SSH v2 en todos los dispositivos. El acceso remoto queda restringido exclusivamente a las líneas VTY 0 4 mediante autenticación local.

```
configure terminal
username admin secret cisco
ip domain-name instituto.local
crypto key generate rsa
! Seleccionar: 1024 bits
ip ssh version 2
line vty 0 4
 login local
 transport input ssh
end
write
```

Se configuran únicamente las líneas VTY 0 4 tal como lo exige el enunciado. El protocolo Telnet queda deshabilitado al especificar transport input ssh.

---

## Banner de Advertencia
```
enable
configure terminal
banner motd #
ACCESO RESTRINGIDO
SOLO PERSONAL AUTORIZADO
#
end
```

---

## Port-Security
Se configura Port-Security en los puertos de acceso para prevenir ataques de MAC flooding y DHCP Starvation. Máximo 2 direcciones MAC por puerto; acción shutdown ante violación.

```
configure terminal
interface g0/0
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
end
write
```

El modo sticky aprende dinámicamente las MACs legítimas y las almacena en la configuración, evitando configuración manual.

---

## Listas de Control de Acceso (ACL)
Se implementan un mínimo de 5 ACLs para restringir el acceso entre las diferentes áreas de la institución.

### ACL 110 — Bloqueo de tráfico HTTP a hosts específicos
Impide que dos hosts de la VLAN USUARIOS accedan a servicios web (puerto 80):

```
access-list 110 deny tcp host 10.15.99.30 any eq 80
access-list 110 deny tcp host 10.15.99.31 any eq 80
access-list 110 permit ip any any

interface g0/0.20
 ip access-group 110 in
exit
```

### ACL 111 — Bloqueo de acceso de un host a la red ADMIN
Impide que el host 10.15.99.31 acceda a la red de administración 10.15.99.0/26:

```
access-list 111 deny ip host 10.15.99.31 10.15.99.0 0.0.0.63
access-list 111 permit ip any any

interface g0/0.20
 ip access-group 111 in
exit
```

### ACL 1 — Definición del tráfico NAT
Permite el tráfico de toda la red interna para ser traducido por NAT:

```
access-list 1 permit 10.15.99.0 0.0.0.255
ip nat inside source list 1 interface fa0/1 overload
```

Total de reglas de control: Las ACLs 110 y 111 contienen 5 entradas de denegación/permiso aplicadas en la VLAN de usuarios, más la ACL 1 para NAT. En conjunto, superan los 5 controles de acceso requeridos.

---

## Controles de Seguridad Adicionales

### 1. Cifrado de contraseñas en texto plano
```
service password-encryption
```
Cifra todas las contraseñas almacenadas en la configuración con algoritmo tipo 7.

### 2. Contraseña de enable con MD5
```
enable secret cisco
```
La directiva enable secret utiliza MD5, más seguro que enable password.

### 3. Bloqueo por intentos fallidos de login
```
login block-for 60 attempts 3 within 60
```
Bloquea el acceso por 60 segundos si se detectan 3 intentos de login fallidos en 60 segundos. Mitiga ataques de fuerza bruta.

### 4. Deshabilitación de búsqueda DNS
```
no ip domain-lookup
```
Evita que el router intente resolver comandos mal escritos como nombres de host, previniendo retrasos y posibles filtraciones de información.

### 5. DHCP Snooping y Dynamic ARP Inspection (DAI)

---

## Ataques Realizados

### DNS Spoofing / DNS Poisoning
Objetivo: Alterar el registro DNS del dominio itla.edu.do para redirigir a los usuarios hacia un servidor web fraudulento controlado por el atacante.

**Requisitos demostrados:**

| Etapa | Descripción |
|-------|-------------|
| ✅ Resolución DNS legítima | El dominio resuelve correctamente antes del ataque |
| ✅ Ejecución del ataque | El atacante envenena la caché DNS mediante ARP Poisoning para posicionarse como MITM |
| ✅ Resolución DNS alterada | El dominio itla.edu.do ahora apunta a la IP del servidor fraudulento |
| ✅ Acceso al sitio fraudulento | La víctima accede al servidor web del atacante creyendo que es el legítimo |
| ✅ Evidencia del impacto | Se observa el tráfico redirigido y la página falsa cargada en el navegador de la víctima |

**Flujo del ataque:**
```
1. Atacante ejecuta ARP Poisoning → se posiciona entre víctima y gateway
2. Intercepta consultas DNS de la víctima
3. Responde con IP del servidor fraudulento en lugar de la IP real
4. Víctima accede a itla.edu.do → carga el sitio controlado por el atacante
```

---

### DHCP Starvation
Objetivo: Agotar el pool de direcciones IP del servidor DHCP mediante solicitudes con MACs falsas, impidiendo que nuevos clientes legítimos obtengan configuración de red.

**Requisitos demostrados:**

| Etapa | Descripción |
|-------|-------------|
| ✅ Funcionamiento normal | El servidor DHCP asigna IPs correctamente antes del ataque |
| ✅ Ejecución del ataque | Script envía masivamente paquetes DHCP Discover con MACs aleatorias |
| ✅ Agotamiento del pool | El pool de VLAN USUARIOS (10.15.99.64/26 → 62 hosts) queda completamente ocupado |
| ✅ Impacto en clientes legítimos | Nuevos clientes reciben DHCP: No lease — sin conectividad de red |

**Flujo del ataque:**
```
1. Script genera MACs aleatorias en cada iteración
2. Envía DHCP Discover por broadcast en la red objetivo
3. El servidor DHCP responde con DHCP Offer para cada MAC única
4. El pool se agota progresivamente
5. Clientes legítimos no reciben respuesta DHCP → sin IP → sin conectividad
```

---

## Contramedidas Implementadas

### Contramedida 1 — DNS Spoofing: Dynamic ARP Inspection (DAI)
Mecanismo: El switch valida cada paquete ARP contra la tabla de DHCP Snooping. Los paquetes ARP del atacante no coinciden con la tabla y son descartados automáticamente, bloqueando el ARP Poisoning desde la raíz y eliminando la posición MITM que hace posible el DNS Spoofing.

```
configure terminal

! Habilitar DHCP Snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20

! Marcar interfaz hacia el router como trusted
interface GigabitEthernet0/0
 ip dhcp snooping trust

! Habilitar Dynamic ARP Inspection
ip arp inspection vlan 10,20

! Marcar interfaz hacia el router como trusted para ARP
interface GigabitEthernet0/0
 ip arp inspection trust

end
```

Los puertos de acceso (hacia PCs) quedan en modo untrusted por defecto — cualquier ARP no validado por la tabla de snooping es descartado.

---

### Contramedida 2 — DHCP Starvation: Port-Security
Mecanismo: Limitar el número de direcciones MAC aprendidas por puerto a un máximo de 2. Un atacante que genere cientos de MACs aleatorias desde un mismo puerto activa inmediatamente el modo shutdown, bloqueando el puerto y deteniendo el ataque.

```
configure terminal
interface g0/0
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation shutdown
 switchport port-security mac-address sticky
end
write
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| maximum | 2 | Máximo de MACs permitidas por puerto |
| violation | shutdown | El puerto se deshabilita ante una violación |
| mac-address sticky | — | Aprende y guarda MACs legítimas automáticamente |
