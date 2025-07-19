import json, os, urllib.request, urllib.error, traceback
from http.server import BaseHTTPRequestHandler

BITQUERY_KEY = os.getenv("BITQUERY_KEY")

CHAIN_MAP = {
    "eth": "ethereum", "polygon": "polygon", "bsc": "bsc",
    "arbitrum": "arbitrum", "optimism": "optimism", "base": "base",
    "avalanche": "avalanche", "fantom": "fantom"
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            addr  = body["address"]
            date  = body["date"] + "T00:00:00Z"
            chain = CHAIN_MAP[body["chain"]]

            payload = {
                "query": """
query($a:String!,$d:ISO8601DateTime,$net:EthereumNetwork){
  ethereum(network:$net){
    address(address:{is:$a}){
      balances(time:{before:$d},currency:{}){
        currency{symbol}
        value
      }
    }
  }
}""",
                "variables": {"a": addr, "d": date, "net": chain.upper()}
            }

            req = urllib.request.Request(
                "https://streaming.bitquery.io/graphql",
                data=json.dumps(payload).encode(),
                headers={"Content-Type":"application/json","X-API-KEY":BITQUERY_KEY}
            )
            res = json.loads(urllib.request.urlopen(req).read())
            addr_data = res["data"]["ethereum"]
            balances  = (addr_data or {}).get("address", [{}])[0].get("balances", [])

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