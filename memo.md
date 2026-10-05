# Memo: where the two hires should go

**To:** Priya Raman  **Re:** Headcount chart, Jan 2025 - Jun 2026 (11,641 tickets)

**Short answer: don't put the two hires in Billing yet. The data points to Logistics, and about Rs 2.4 lakh a year of the problem is a fixable intake rule.**

**Why Billing looks biggest.** Billing is 21% of all tickets and, by the bot's tag, the busiest team per person (about 37 tickets per agent per month in Jan-Jun 2026, against 24 for Logistics). But the bot tags a ticket "Billing" when the customer says they've *paid*. Reading what customers wrote and what agents closed, **42% of Billing-tagged tickets in 2026 are not billing issues**. Most are "I paid and my order never arrived". I read 50 at random and 49 were classified correctly (see notes below).

**What that does to the picture.** Re-assigning each ticket to the team that owns the problem (your own policy, section 6):

| Tickets per agent per month, Jan-Jun 2026 | As routed | By real owner |
|---|---|---|
| Billing (4 agents) | 37 | 26 |
| Logistics (5 agents) | 25 | **47** |
| Returns Desk (3 agents) | 21 | 24 |
| Frontline teams | 14-18 | 11-14 |

Neha is right that Logistics is the stretched team. Logistics agents already resolve most of these tickets after a hand-off. Their load is hidden because the work arrives through Billing's queue.

**What the mis-tag costs.** Compared with correctly-routed Billing tickets, the mis-tagged ones are transferred 61% of the time (8%), miss the first-response target 32% of the time (9%), score CSAT 2.5 (3.6), and take about 2 days to resolve (20 minutes). At about 190 a quarter, using your policy costs (Rs 305 per transfer, Rs 350 per missed-SLA credit), that is **about Rs 61,000 a quarter, Rs 2.4 lakh a year**.

**The number to aim for.** Cut non-billing tickets in the Billing queue from 42% to under 10%: about **Rs 46,000 a quarter** saved directly. The bigger prize is Arjun's: Rs 9 lakh a year not spent on the wrong team.

**Recommendation.**
1. Hold the Billing hires. Ask Sameer to change the intake bot so "paid / not received / tracking" goes to Logistics. A rule list is in `rules.py`.
2. If one of the two hires is still wanted now, Logistics is where the evidence points. Revisit after two months of corrected routing.
3. One more fix: SLA breaches are reported against the *resolving* agent. Logistics is charged with 423 breaches but only 184 happened in its queue; Billing is the reverse (477 happened, 241 charged). Eighteen months of credits total about Rs 4.5 lakh.

**What I'm not claiming.** Tickets per agent is a rough proxy; the export has no effort-time data, and elapsed hours are not workload. Escalations & Warranty is certified Tier 2 work and isn't comparable on volume. The classifier is rules-based and was checked on a small sample by one reviewer, not a full audit. Cancellations and refund-status tickets could reasonably belong to more than one team.
