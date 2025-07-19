import json, os, urllib.request, urllib.error, traceback
from http.server import BaseHTTPRequestHandler

ETHERSCAN_KEY = os.getenv("ETHERSCAN_KEY")  # optional (free tier allows 5/sec)

CHAIN_RPC = {
    "eth": "https://api.etherscan.io/api",
    "polygon": "https://api.polygonscan.com/api",
    "bsc": "https://api.bscscan.com/api",
    "arbitrum": "https://api.arbiscan.io/api",
    "optimism": "https://api-optimistic.etherscan.io/api",
    "base": "https://api.basescan.org/api",
    "avalanche": "https://api.snowtrace.io/api",
    "fantom": "https://api.ftmscan.com/api",
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            addr = body["address"]
            date = body["date"]
            chain = body["chain"]
            api_url = CHAIN_RPC[chain]

            # get block number closest to that date
            ts = int(__import__("datetime").datetime.strptime(date, "%Y-%m-%d").timestamp())
            blk_url = f"{api_url}?module=block&action=getblocknobytime&timestamp={ts}&closest=before&apikey={ETHERSCAN_KEY or ''}"
            blk_res = json.loads(urllib.request.urlopen(blk_url).read())
            block = blk_res["result"]

            # get balance at that block
            bal_url = f"{api_url}?module=account&action=balance&address={addr}&tag={block}&apikey={ETHERSCAN_KEY or ''}"
            bal_res = json.loads(urllib.request.urlopen(bal_url).read())
            balance = int(bal_res["result"]) / 1e18

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"{balance:.6f} ETH\n".encode())

        except Exception:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(traceback.format_exc().encode())