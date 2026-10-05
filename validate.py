#!/usr/bin/env python3
"""Validation without ground truth. Usage: python validate.py --out out/
(1) Self-consistency: classify the customer's message and the agent's note SEPARATELY; they are independent views of one ticket.
(2) Writes handlabel_sample.csv (120 stratified rows, blank 'your_label') so a human can measure real accuracy."""
import argparse, pandas as pd
from rules import classify, owner_team
ap = argparse.ArgumentParser(); ap.add_argument("--out", default="out"); a = ap.parse_args()
t = pd.read_csv(f"{a.out}/tickets_classified.csv")
t["m"] = [classify(x, "")[0] for x in t.customer_message]; t["n"] = [classify("", x)[0] for x in t.agent_notes]
b = t[(t.m != "Unclassified") & (t.n != "Unclassified")]
om = pd.Series([owner_team(x, c) for x, c in zip(b.m, b.channel)], index=b.index)
on = pd.Series([owner_team(x, c) for x, c in zip(b.n, b.channel)], index=b.index)
print(f"tickets where both message and note are classifiable: {len(b)} of {len(t)}")
print(f"label agreement (fine, 16 labels): {(b.m == b.n).mean():.1%}")
print(f"owning-team agreement (what the headcount call depends on): {(om == on).mean():.1%}")
print(f"unclassified overall: {(t.issue == 'Unclassified').mean():.1%}")
print("\nAgreement by label (message-based label vs note-based label):")
print(b.assign(ok=b.m == b.n).groupby("m").ok.mean().round(2).sort_values().to_string())
s = pd.concat([g.sample(min(len(g), 8), random_state=1) for _, g in t.groupby("issue")]).sample(frac=1, random_state=2).head(120)
s[["ticket_id", "category", "customer_message", "agent_notes", "issue", "true_team"]].assign(your_label="").to_csv(f"{a.out}/handlabel_sample.csv", index=False)
print(f"\nwrote {a.out}/handlabel_sample.csv ({len(s)} rows)")
