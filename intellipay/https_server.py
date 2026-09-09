#!/usr/bin/env python3
"""HTTPS front for the join MVP (self-signed, local testing only). Same handler as server.py."""
import ssl, os
from http.server import ThreadingHTTPServer
from server import H
PORT=int(os.environ.get("HTTPS_PORT","4443"))
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain("/tmp/lb-cert.pem","/tmp/lb-key.pem")
httpd=ThreadingHTTPServer(("127.0.0.1",PORT),H)
httpd.scheme="https"   # lets the handler hand the Lightbox an https logo URL it can fetch
httpd.socket=ctx.wrap_socket(httpd.socket,server_side=True)
print(f"HTTPS join MVP → https://localhost:{PORT}")
httpd.serve_forever()
