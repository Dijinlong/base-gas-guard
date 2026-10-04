# base-gas-guard

A minimal ETH balance guard for wallets on [Base](https://base.org).

## Why

Running out of gas rarely announces itself. Services that depend on a Base wallet
tend to degrade in ways that look like something else entirely — a node stops
announcing, a transaction silently never lands, a listing disappears.

By the time you notice, you are debugging the wrong thing.

## What it does

- Reads the ETH balance of one or more addresses
- Compares against a configurable floor
- Exits non-zero (so cron / CI / a monitoring hook can pick it up) when below

## Usage

    python gas_guard.py --address 0xYourAddress --floor 0.0002

    # exits 0 if fine, 1 if below floor, 2 on RPC error

## Why not just a dashboard?

Because dashboards require someone to look at them. This is meant to be wired
into whatever already pages you.

## Status

Early but usable.
