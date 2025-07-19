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
            addr, date, chain = body["address"], body["date"] + "T00:00:00Z", CHAIN_MAP[body["chain"]]

            url = "https://streaming.bitquery.io/graphql"
            headers = {"Content-Type": "application/json", "X-API-KEY": BITQUERY_KEY}
            payload = {
                "query": """
query($a:String!,$d:ISO8601DateTime){
  ethereum(network:%s){
    address(address:{is:$a}){
      balances(time:{before:$d},currency:{}){
        currency{symbol}
        value
      }
    }
  }
}""" % chain,
                "variables": {"a": addr, "d": date}
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
            res = json.loads(urllib.request.urlopen(req).read())
            data = res["data"]["ethereum"]["address"][0]["balances"]

            out = [f"{float(b['value']):>15.6f} {b['currency']['symbol']}" for b in data]
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write("\n".join(out).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())