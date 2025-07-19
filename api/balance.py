import json
import os
import urllib.request
import urllib.error
import traceback
from http.server import BaseHTTPRequestHandler

# 1. read the key from Vercel’s env
BITQUERY_KEY = os.getenv("BITQUERY_KEY")

# 2. map from user-friendly name to Bitquery network enum
CHAIN_MAP = {
    "eth": "ethereum",
    "polygon": "polygon",
    "bsc": "bsc",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
    "base": "base",
    "avalanche": "avalanche",
    "fantom": "fantom",
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # read JSON body
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            addr  = body["address"]
            date  = body["date"] + "T00:00:00Z"
            chain = CHAIN_MAP[body["chain"]]

            # GraphQL query with variables
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
                "variables": {
                    "a": addr,
                    "d": date,
                    "net": chain,
                },
            }

            # send request
            req = urllib.request.Request(
                "https://streaming.bitquery.io/graphql",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": BITQUERY_KEY,
                },
            )
            res = json.loads(urllib.request.urlopen(req).read())

            # extract balances
            balances = res["data"]["ethereum"]["address"][0]["balances"]
            out = [
                f"{float(b['value']):>15.6f} {b['currency']['symbol']}"
                for b in balances
            ]

            # return success
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write("\n".join(out).encode())

        except Exception:
            # return full traceback so we always see the error
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())