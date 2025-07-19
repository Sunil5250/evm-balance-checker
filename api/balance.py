import json, requests, datetime, os
from http.server import BaseHTTPRequestHandler

BITQUERY_KEY = os.getenv("BITQUERY_KEY", "free-demo-key")  # fallback for quick test

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
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        addr  = body["address"]
        date  = body["date"] + "T00:00:00Z"
        chain = CHAIN_MAP[body["chain"]]

        query = """
        query($addr:String!,$date:ISO8601DateTime){
          ethereum(network:%s){
            address(address:{is:$addr}){
              balances(time:{before:$date},currency:{}){
                currency{symbol}
                value
              }
            }
          }
        }""" % chain

        res = requests.post(
            "https://streaming.bitquery.io/graphql",
            headers={"X-API-KEY": BITQUERY_KEY},
            json={"query": query, "variables": {"addr": addr, "date": date}}
        )
        data = res.json()["data"]["ethereum"]["address"][0]["balances"]

        out = [f"{float(b['value']):>15.6f} {b['currency']['symbol']}" for b in data]
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("\n".join(out).encode())