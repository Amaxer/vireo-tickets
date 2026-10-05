#!/usr/bin/env python3
"""Vireo ticket categoriser + headcount-evidence report.
Usage: python vireo.py --data /path/to/pack --out out/
Needs only pandas + matplotlib. No API calls, no cost."""
import argparse, json, os
import pandas as pd
from rules import classify, owner_team

SLA_H = {"chat": .25, "voice": 2, "social": 4, "email": 8}   # policy s3
CREDIT, XFER, HIRES_YR = 350, 305, 900_000                   # policy s3, s4; Arjun's email
START, END = "2025-01-01", "2026-06-30 23:59"                 # stated window; earlier rows are 139 legacy stragglers

def load(data):
    t = pd.read_csv(f"{data}/tickets.csv", parse_dates=["created_at", "first_response_at", "resolved_at"])
    a = pd.read_csv(f"{data}/agents.csv")
    n0 = len(t)
    # legacy resolved_at was rebuilt from a UTC event log; helpdesk is IST -> add 5.5h (fixes 2,379 negative durations)
    leg = t.source_system == "legacy_fd"
    t.loc[leg, "resolved_at"] += pd.Timedelta(hours=5.5)
    t = t[(t.created_at >= START) & (t.created_at <= END)].copy()
    t["month"] = t.created_at.dt.to_period("M").astype(str)
    t["frt_h"] = (t.first_response_at - t.created_at).dt.total_seconds() / 3600
    t["handle_h"] = (t.resolved_at - t.first_response_at).dt.total_seconds() / 3600
    t["breach"] = t.frt_h > t.channel.map(SLA_H)
    return t, a, n0 - len(t)

def categorise(t):
    r = [classify(m, n) for m, n in zip(t.customer_message, t.agent_notes)]
    t["issue"], t["conf"] = [x[0] for x in r], [x[2] for x in r]
    t["true_team"] = [owner_team(i, c) if i != "Unclassified" else None for i, c in zip(t.issue, t.channel)]
    t["billing_misroute"] = (t.category == "Billing & Payments") & t.true_team.notna() & (t.true_team != "Billing")
    return t

def report(t, a, dropped, out):
    os.makedirs(f"{out}/charts", exist_ok=True)
    agents = a.groupby("team").agent_id.nunique()
    # monthly tables
    t.pivot_table(index="month", columns="category", values="ticket_id", aggfunc="count", fill_value=0).to_csv(f"{out}/monthly_by_bot_category.csv")
    t.pivot_table(index="month", columns="assigned_team", values="ticket_id", aggfunc="count", fill_value=0).to_csv(f"{out}/monthly_by_routed_team.csv")
    ok = t[t.true_team.notna()]
    ok.pivot_table(index="month", columns="true_team", values="ticket_id", aggfunc="count", fill_value=0).to_csv(f"{out}/monthly_by_owning_team.csv")
    # per-agent load, last 6 months
    r = t[t.created_at >= "2026-01-01"]
    load = pd.DataFrame({"agents": agents, "routed": r.groupby("assigned_team").size(), "owning": r.dropna(subset=["true_team"]).groupby("true_team").size()}).fillna(0)
    load["routed_per_agent_month"] = (load.routed / 6 / load.agents).round(1)
    load["owning_per_agent_month"] = (load.owning / 6 / load.agents).round(1)
    load.to_csv(f"{out}/load_per_agent.csv")
    # misroute cost (transfers exist only in the current helpdesk, blank on legacy)
    h = t[(t.source_system == "helpdesk") & (t.category == "Billing & Payments") & t.true_team.notna()]
    bad, good = h[h.billing_misroute], h[~h.billing_misroute]
    per = bad.transfers.mean() * XFER + (bad.breach.mean() - good.breach.mean()) * CREDIT
    bill = r[r.category == "Billing & Payments"]
    n_q = r.billing_misroute.sum() / 2
    s = {
      "rows_in_window": len(t), "rows_dropped_outside_window": dropped, "unclassified_pct": round((t.issue == "Unclassified").mean()*100, 1),
      "billing_tag_share_of_all_tickets_pct": round((t.category == "Billing & Payments").mean()*100, 1),
      "billing_tagged_h1_2026": int(len(bill)), "billing_tag_not_billing_pct": round(r.billing_misroute.sum()/len(bill)*100, 1),
      "misrouted_per_quarter": round(n_q), "helpdesk_misrouted_n": len(bad), "helpdesk_correct_billing_n": len(good),
      "transfer_rate_misrouted_pct": round((bad.transfers > 0).mean()*100, 1), "transfer_rate_correct_pct": round((good.transfers > 0).mean()*100, 1),
      "breach_rate_misrouted_pct": round(bad.breach.mean()*100, 1), "breach_rate_correct_pct": round(good.breach.mean()*100, 1),
      "csat_misrouted": round(bad.csat_score.mean(), 2), "csat_correct": round(good.csat_score.mean(), 2),
      "median_resolution_h_misrouted": round(bad.handle_h.median(), 1), "median_resolution_h_correct": round(good.handle_h.median(), 2),
      "excess_cost_per_misrouted_ticket_inr": round(per),
      "excess_cost_per_quarter_inr": round(per * n_q), "excess_cost_per_year_inr": round(per * n_q * 4),
      "target_10pct_saving_per_quarter_inr": round(per * (n_q - 0.10 * len(bill) / 2)),
      "two_hires_per_year_inr": HIRES_YR,
    }
    json.dump(s, open(f"{out}/summary.json", "w"), indent=2)
    t.drop(columns=["month"]).to_csv(f"{out}/tickets_classified.csv", index=False)
    charts(t, ok, load, out)
    return s, load

def charts(t, ok, load, out):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    def stacked(df, col, title, fn):
        p = df.pivot_table(index="month", columns=col, values="ticket_id", aggfunc="count", fill_value=0)
        ax = p.plot(kind="bar", stacked=True, figsize=(12, 5.5), colormap="tab20", width=.85)
        ax.set_title(title); ax.set_xlabel(""); ax.set_ylabel("tickets"); ax.legend(fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.xticks(rotation=60, fontsize=8); plt.tight_layout(); plt.savefig(f"{out}/charts/{fn}", dpi=130); plt.close()
    stacked(t, "category", "Monthly tickets by bot category tag (as exported)", "1_monthly_by_category.png")
    stacked(t, "assigned_team", "Monthly tickets by team they were first routed to (as exported)", "2_monthly_by_routed_team.png")
    stacked(ok, "true_team", "Monthly tickets by the team that owns the actual issue (re-classified from text)", "3_monthly_by_owning_team.png")
    ax = load[["routed_per_agent_month", "owning_per_agent_month"]].plot(kind="bar", figsize=(9, 5), color=["#999", "#d9534f"])
    ax.set_title("Tickets per agent per month, Jan-Jun 2026"); ax.set_xlabel(""); ax.legend(["as routed (bot tag)", "by owning team (from text)"])
    plt.xticks(rotation=30, ha="right"); plt.tight_layout(); plt.savefig(f"{out}/charts/4_load_per_agent.png", dpi=130); plt.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", default="out")
    a = ap.parse_args()
    t, ag, dropped = load(a.data); t = categorise(t)
    s, load_ = report(t, ag, dropped, a.out)
    print(json.dumps(s, indent=2)); print(load_)
