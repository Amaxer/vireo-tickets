# Vireo ticket categoriser and headcount evidence

Reads the helpdesk export, re-classifies each ticket from its text (customer message + agent closing note), and shows
monthly volume by bot tag, by routed team, and by the team that actually owns the issue. No API calls, no keys, no cost.

## Run (clean machine, Python 3.9+)
```
pip install -r requirements.txt
python vireo.py --data /path/to/pack --out out     # pack = folder holding tickets.csv and agents.csv
python validate.py --out out                        # self-consistency check + 120-row hand-label sheet
```
Outputs in `out/`: `summary.json` (every number in the memo), `charts/1-4*.png`, `monthly_by_*.csv`,
`load_per_agent.csv`, `tickets_classified.csv`, `handlabel_sample.csv`. Takes seconds on 11.6k tickets.

## Files
- `rules.py` - the classifier: 15 issue labels, regex rules, each label mapped to its owning team (support-policy s6).
  Edit the rules here; this is where all the judgement lives.
- `vireo.py` - cleaning, classification, tables, charts, cost arithmetic.
- `validate.py` - checks, and the hand-label sheet.

## Decisions I made (the brief left these open)
1. **Window**: kept 1 Jan 2025 - 30 Jun 2026 (the stated window). Dropped 139 legacy rows dated Jun-Dec 2024.
2. **Timestamps**: legacy `resolved_at` is UTC (policy s9), everything else IST. Added 5.5 h to legacy rows; this removes all 2,379 resolved-before-created rows. `first_response_at` needed no change.
3. **Transfers**: blank on legacy rows means unknown, not zero. Transfer-based numbers use helpdesk-era rows only (Sep 2025 on).
4. **Team**: "team" = `assigned_team` (where the bot sent it). I also report "owning team" = who should own the issue per policy s6. Unclear-channel frontline issues go to the frontline team for the ticket's channel (social -> Chat, per policy s2).
5. **Handle time** = first response to resolution, per policy s10. That is elapsed time, not effort, so I do not convert it to agent-hours.
6. **Refund units**: policy says legacy used a "native unit". Refund/order-value ratios are identical across systems (median 1.0), so I treated both as rupees. No duplicates found between source systems (checked ids, exact and normalised text, customer+order+time).
7. **Money**: only policy figures (Rs 305/transfer, Rs 350/SLA credit, Rs 9 lakh for two hires from Arjun's email). Excess cost per misrouted ticket = mean transfers x 305 + (breach-rate gap vs correctly routed Billing tickets) x 350. Repeat-contact cost was tested and dropped: no signal.

## Known weaknesses
- Regex, not a model. Frontline technical labels (audio / connectivity / app / battery) blur into each other (60-80% self-agreement). They all route to the same team, so it does not change the headcount answer, but do not trust the fine split.
- Cancellation / address-change and refund-status tickets are ambiguous on ownership (Logistics vs Returns Desk vs Billing); I followed policy s6 wording.
- 1.6% of tickets have no usable text (note is "cx ok") and stay unclassified.
- Validation has no human ground truth; see `submission-answers.md`.
