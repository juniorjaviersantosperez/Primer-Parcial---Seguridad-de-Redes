#!/usr/bin/env python3
"""
=============================================================
  Servidor Web Falso — Complemento del laboratorio DNS Spoofing
=============================================================
  Ejecutar en 10.15.99.150 (el servidor del laboratorio).
  Simula el sitio itla.edu.do para demostrar la redirección.

  Uso:
    python3 fake_server.py

  Luego visitar desde la víctima:
    curl http://itla.edu.do
    o abrir en el navegador (con DNS ya envenenado)
=============================================================
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import datetime

PUERTO = 80
IP     = "10.15.99.150"

PAGE_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>ITLA - Instituto Tecnológico de Las Américas</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f0f4f8; margin: 0; }}
    .banner {{ background: #003087; color: white; padding: 20px 40px; }}
    .banner h1 {{ margin: 0; font-size: 1.6em; }}
    .container {{ max-width: 800px; margin: 40px auto; background: white;
                  padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    .alert {{ background: #fff3cd; border: 1px solid #ffc107;
              padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
    .info  {{ color: #555; font-size: .9em; }}
  </style>
</head>
<body>
  <div class="banner">
    <h1>🎓 ITLA — Instituto Tecnológico de Las Américas</h1>
    <p style="margin:4px 0 0;opacity:.8">itla.edu.do</p>
  </div>
  <div class="container">
    <div class="alert">
      ⚠️ <strong>DEMO DE LABORATORIO</strong> — Esta página es un servidor FALSO
      usado en una demostración de DNS Spoofing con fines educativos.
    </div>
    <h2>Bienvenido a ITLA</h2>
    <p>Si estás viendo esta página desde la máquina víctima, el ataque
       <strong>DNS Spoofing</strong> fue exitoso. Tu consulta DNS para
       <code>itla.edu.do</code> fue redirigida a este servidor.</p>
    <hr>
    <p class="info">
      Servidor: {ip} &nbsp;|&nbsp; Puerto: {puerto} &nbsp;|&nbsp;
      Hora: {hora}
    </p>
  </div>
</body>
</html>"""

class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = PAGE_HTML.format(
            ip=IP,
            puerto=PUERTO,
            hora=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
        print(f"  [req] {self.client_address[0]} → {self.path}")

    def log_message(self, fmt, *args):
        pass  # Silenciar log por defecto de HTTPServer

if __name__ == "__main__":
    print(f"[*] Servidor web falso escuchando en {IP}:{PUERTO}")
    print("[*] Presiona Ctrl+C para detener.\n")
    server = HTTPServer((IP, PUERTO), FakeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor detenido.")
