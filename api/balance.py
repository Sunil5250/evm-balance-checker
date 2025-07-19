import json, os, urllib.request, urllib.error, traceback
from http.server import BaseHTTPRequestHandler

BITQUERY_KEY = os.getenv("BITQUERY_KEY")

CHAIN_MAP = {  # exact camel-case names Bitquery expects
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
            network = CHAIN_MAP[body["chain"]]

            payload = {
                "query": """
query($a:String!,$d:ISO8601DateTime,$net:EthereumNetwork!){
  ethereum(network:$net){
    address(address:{is:$a}){
      balances(time:{before:$d},currency:{}){
        currency{symbol}
        value
      }
    }
  }
}""",
                "variables": {"a": addr, "d": date, "net": network}
            }

            req = urllib.request.Request(
                "https://streaming.bitquery.io/graphql",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json", "X-API-KEY": BITQUERY_KEY}
            )
            res = json.loads(urllib.request.urlopen(req).read())

            # safe traversal
            data_root = res.get("data", {})
            ethereum = data_root.get("ethereum", {})
            address  = ethereum.get("address")
            balances = address[0]["balances"] if address else []

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