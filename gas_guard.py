#!/usr/bin/env python3
"""
base-gas-guard
==============

Warn before a Base wallet runs dry.

Why this needs to exist
-----------------------
Running out of gas rarely announces itself.

Services that depend on a Base wallet degrade in ways that look like something
else entirely: a node stops announcing, a transaction silently never lands, a
listing quietly disappears. By the time you notice, you are debugging the wrong
thing.

By then the cause - an empty wallet - is the last place you look.

Usage
-----
    python gas_guard.py --address 0xYourWallet --floor 0.0002
    python gas_guard.py --address 0xYourWallet --floor 0.0002 \\
                        --rpc https://mainnet.base.org

Wire it into cron and it pages you before the failure, not after:

    */15 * * * * python /path/gas_guard.py --address 0x... --floor 0.0002

Exit codes
----------
    0  balance is above the floor
    1  balance is below the floor
    2  could not check (RPC / network error)
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_RPC = "https://mainnet.base.org"
WEI_PER_ETH = 10 ** 18


def get_balance_wei(rpc_url, address):
    """eth_getBalance against a JSON-RPC endpoint. Raises on failure."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBalance",
        "params": [address, "latest"],
    }
    req = urllib.request.Request(
        rpc_url, data=json.dumps(payload).encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "base-gas-guard")

    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read().decode())

    if "result" not in body:
        raise RuntimeError("RPC error: %s" % (body.get("error") or body))

    return int(body["result"], 16)


def get_block_number(rpc_url):
    """Best-effort chain liveness check. Returns None if unavailable."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
    req = urllib.request.Request(
        rpc_url, data=json.dumps(payload).encode(), method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "base-gas-guard")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode())
        return int(body["result"], 16)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="Warn when a Base wallet runs low on ETH.")
    ap.add_argument("--address", required=True, help="wallet address (0x...)")
    ap.add_argument("--floor", type=float, default=0.0002,
                    help="warn below this many ETH (default 0.0002)")
    ap.add_argument("--rpc", default=DEFAULT_RPC, help="JSON-RPC endpoint")
    ap.add_argument("--quiet", action="store_true",
                    help="print nothing when the balance is fine")
    args = ap.parse_args()

    try:
        wei = get_balance_wei(args.rpc, args.address)
    except Exception as e:
        print("could not check balance: %s" % e, file=sys.stderr)
        return 2

    eth = wei / WEI_PER_ETH
    block = get_block_number(args.rpc)

    if eth < args.floor:
        print("LOW  %s has %.8f ETH, below the floor of %.8f ETH"
              % (args.address, eth, args.floor))
        print("     top up now - services may already be degrading.")
        if block is not None:
            print("     (chain head: block %d)" % block)
        return 1

    if not args.quiet:
        head = " (block %d)" % block if block is not None else ""
        print("OK   %s has %.8f ETH, floor %.8f ETH%s"
              % (args.address, eth, args.floor, head))
    return 0


if __name__ == "__main__":
    sys.exit(main())
