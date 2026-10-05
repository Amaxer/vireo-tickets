"""Rule-based issue classifier. Free, deterministic, no API. Reads customer message + agent closing note.
Each label maps to the team that OWNS that issue under support-policy.pdf s6."""
import re

ISSUES = {  # label: (owning team, [regex...]); dict order = tie-break priority
 "Payment: duplicate charge":      ("Billing", [r"duplic", r"double (pay|charg)", r"charged twice", r"(deducted|debited) twice", r"same amount (twice|got deducted again)"]),
 "Payment: debited, no order":     ("Billing", [r"without ord", r"no order", r"failed (order|payment|txn)", r"page failed", r"order not showing", r"nothing shows in my account", r"upi shows success", r"no order id", r"money (debit|gone)\w* .{0,30}no order"]),
 "Invoice / GST":                  ("Billing", [r"gst", r"invoice", r"\bbill\b", r"\bblil\b"]),
 "Coupon / price adjustment":      ("Billing", [r"coupon", r"promo", r"discount", r"20% off", r"full price", r"price drop"]),
 "Account / login":                ("Frontline", [r"\botp\b", r"login", r"log in", r"password", r"locked out", r"sign ?in", r"account (locked|access)"]),
 "Cancellation / address change":  ("Logistics", [r"cancel", r"stop the shipment", r"(update|change|correct)\w* (my |the )?(shipping |delivery )?ad+res", r"ad+ress (update|change)", r"wrong pincode", r"old flat", r"typo in the flat", r"moved house", r"change of mind", r"by mistake", r"redirect"]),
 "Delivery: damaged / wrong item": ("Logistics", [r"damag", r"wrong (item|variant)", r"incorrect product", r"completely different", r"something else", r"not what i paid for", r"\bdent\b", r"kicked", r"cracked? (before|straight)"]),
 "Delivery: not received / late":  ("Logistics", [r"not (been )?deliver", r"order not rec", r"(shipment|parcel|package|order) not rec", r"not rcvd", r"shipment not", r"dlvry", r"deliver\w* delay", r"(chk|checked) awb", r"raised ticket (with|w/) (crr|courier)", r"courier (confirmed|marked)", r"marked it delivered", r"lost in transit", r"\brto\b", r"re-?shipped", r"order status", r"tracking", r"nothing (at my door|in hand)", r"waiting for something", r"haven.t (got|received)", r"nobody in my house got", r"parcel stuck", r"no update, nothing"]),
 "Return / refund status":         ("Returns Desk", [r"pick-?up (not|missed|pending|has not|today)", r"pickup", r"nobody came", r"reverse pick?up pending", r"reverse pkp pending", r"re-raised pickup", r"refund (not|pending|delay|reprocess|status|was promised)", r"rfnd (pending|delay)", r"amount is nowh", r"where is the mo", r"packed the box", r"still waiting for my refund", r"return (was )?accepted", r"waiting for (my|the) refund", r"refund .{0,10}not credited"]),
 "Warranty / repair / RMA":        ("Escalations & Warranty", [r"warranty", r"\brma\b", r"repair", r"service cent", r"strap", r"touch ?screen", r"display", r"swipe", r"tap ten", r"watch not respon"]),
 "Product enquiry":                ("Frontline", [r"enquir", r"pre-?sales", r"compatib", r"spec sheet", r"iphone", r"survive a shower", r"connect two", r"work with", r"waterproof"]),
 "App / firmware":                 ("Frontline", [r"firmware", r"\bapp\b", r"update (failed|stuck|hang)", r"\bfw\b", r"update hang", r"spinning circle", r"app (crash|clos)"]),
 "Connectivity / pairing":         ("Frontline", [r"pair", r"bluetooth", r"connect", r"discover", r"disconnect", r"drop", r"stutter"]),
 "Charging / battery":             ("Frontline", [r"\bcharging\b", r"not charg", r"stopped charg", r"never charges", r"\bcharges\b", r"\bcharge\b", r"batter", r"drain", r"lights up", r"dies by lunch", r"0%", r"percent"]),
 "Audio quality":                  ("Frontline", [r"audio", r"sound", r"crackl", r"static", r"\bmic", r"bass", r"one ear", r"one direction", r"left side", r"right side", r"volume", r"muffled", r"silent", r"mute"]),
}
FRONTLINE_BY_CHANNEL = {"chat":"Chat Frontline","social":"Chat Frontline","email":"Email Frontline","voice":"Voice Frontline"}
_C = {k:[re.compile(p) for p in v[1]] for k,v in ISSUES.items()}

def classify(message, note):
    """-> (label, owning_team_or_None, score). 'Unclassified' when no pattern fires (e.g. note is just 'cx ok')."""
    m, n = str(message or "").lower(), str(note or "").lower()
    best, bs = None, 0.0
    for i, lab in enumerate(ISSUES):
        s = 2*sum(bool(p.search(n)) for p in _C[lab]) + sum(bool(p.search(m)) for p in _C[lab]) - i*1e-3
        if s > bs: best, bs = lab, s
    return (best, ISSUES[best][0], bs) if best else ("Unclassified", None, 0.0)

def owner_team(label, channel):
    team = ISSUES[label][0] if label in ISSUES else None
    return FRONTLINE_BY_CHANNEL[channel] if team == "Frontline" else team
