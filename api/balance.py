import json, os, urllib.request, urllib.error, traceback
from http.server import BaseHTTPRequestHandler

BITQUERY_KEY = os.getenv("BITQUERY_KEY")

CHAIN_MAP = {
    "eth": "Ethereum",
    "polygon": "Polygon",
    "bsc": "BSC",
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "base": "Base",
    "avalanche": "Avalanche",
    "fantom": "Fantom"
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            addr  = body["address"]
            date  = body["date"] + "T00:00:00Z"
            net   = CHAIN_MAP[body["chain"]]

            query = f"""
{{
  ethereum(network: {net}) {{
    address(address: "{addr}") {{
      balances(time: {{before: "{date}"}}, currency: {{}}) {{
        currency {{symbol}}
        value
      }}
    }}
  }}
}}"""

            req = urllib.request.Request(
                "https://streaming.bitquery.io/graphql",
                data=query.encode(),
                headers={"Content-Type": "application/json", "X-API-KEY": BITQUERY_KEY}
            )
            res = json.loads(urllib.request.urlopen(req).read())

            balances = res.get("data", {}).get("ethereum", {}).get("address", [{}])[0].get("balances", [])
            if not balances:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"No balances found\n")
                return

            out = [f"{float(b['value']):>15.6f} {b['currency']['symbol']}" for b in balances]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("\n".join(out).encode())

        except Exception:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())