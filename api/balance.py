import json, os, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler

BITQUERY_KEY = os.getenv("BITQUERY_KEY", "free-demo-key")

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

        query = {"query": f"""
        query($a:String!,$d:ISO8601DateTime){{
          ethereum(network:{chain}){{
            address(address:{{is:$a}}){{
              balances(time:{{before:$d}},currency:{{}}){{
                currency{{symbol}}
                value
              }}
            }}
          }}
        }}""", "variables": {"a": addr, "d": date}}

        req = urllib.request.Request(
            "https://streaming.bitquery.io/graphql",
            data=json.dumps(query).encode(),
            headers={"Content-Type": "application/json", "X-API-KEY": BITQUERY_KEY}
        )
        res = json.loads(urllib.request.urlopen(req).read())
        data = res["data"]["ethereum"]["address"][0]["balances"]

        out = [f"{float(b['value']):>15.6f} {b['currency']['symbol']}" for b in data]
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("\n".join(out).encode())