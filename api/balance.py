# Vercel Serverless Function (Python)
from http.server import BaseHTTPRequestHandler
import json, requests, datetime, os

API_KEY = os.getenv("COVALENT_KEY", "ckey_xxxxxxxxxxxxxxxxxx")   # fallback free key

CHAIN_MAP = {
    "eth": 1,
    "polygon": 137,
    "bsc": 56,
    "arbitrum": 42161,
    "optimism": 10,
    "base": 8453,
    "avalanche": 43114,
    "fantom": 250,
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        addr  = body["address"]
        date  = body["date"]
        chain = body["chain"]
        chain_id = CHAIN_MAP[chain]

        ts = int(datetime.datetime.strptime(date, "%Y-%m-%d").timestamp())

        # 1) Covalent GoldRush
        url = (
            f"https://api.covalenthq.com/v1/{chain_id}/address/{addr}/balances_v2/"
            f"?quote-currency=USD&format=JSON&block-signed-at-utc={date}T00:00:00Z&key={API_KEY}"
        )
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        items = r.json()["data"]["items"]

        lines = [
            f"Snapshot  {addr}",
            f"Chain     {chain} ({chain_id})",
            f"Date      {date} UTC midnight\n"
        ]
        for item in items:
            sym = item["contract_ticker_symbol"] or "ETH"
            bal = int(item["balance"]) / 10 ** int(item["contract_decimals"])
            lines.append(f"{bal:>15.6f} {sym}")

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write("\n".join(lines).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()