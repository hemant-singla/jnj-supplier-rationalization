"""J&J supplier rationalization business case model (top-down, assumption-driven)."""
SPEND = 35_000  # $M addressable spend
SUPPLIERS = 29_000

# Segmentation (assumed Pareto shape)
seg = {
    "A Strategic": {"sup_share": 0.02, "spend_share": 0.70, "cut": 0.00},
    "B Core":      {"sup_share": 0.13, "spend_share": 0.22, "cut": 0.25},
    "C Tail":      {"sup_share": 0.85, "spend_share": 0.08, "cut": 0.60},
}
# savings rate on spend moved/addressed
price_rate = {"A Strategic": 0.005, "B Core": 0.05, "C Tail": 0.08}
COST_PER_SUPPLIER = 0.002  # $M/yr to maintain an active supplier ($2,000)
transition = {"A Strategic": 0, "B Core": 0.025, "C Tail": 0.0005}  # $M per exited supplier
PROGRAM = 15.0   # $M team, analytics, tech
LEGAL = 5.0      # $M contracting
CONT = 0.15
RAMP = [0.3, 0.7, 1.0]
DISC = 0.08

rows, run_price, exits, trans = [], 0, 0, 0
for k, s in seg.items():
    n = SUPPLIERS * s["sup_share"]; sp = SPEND * s["spend_share"]
    ex = n * s["cut"]
    addressed = sp if k == "A Strategic" else sp * s["cut"]
    sav = addressed * price_rate[k]
    run_price += sav; exits += ex; trans += ex * transition[k]
    rows.append((k, n, sp, ex, n - ex, addressed, sav))
proc = exits * COST_PER_SUPPLIER
run = run_price + proc
one_time = (PROGRAM + LEGAL + trans) * (1 + CONT)

def npv(scale_sav=1.0, scale_cost=1.0):
    cf = [-one_time * scale_cost] + [run * scale_sav * r for r in RAMP]
    return sum(c / (1 + DISC) ** i for i, c in enumerate(cf)), cf

print(f"{'Segment':12} {'Suppliers':>9} {'Spend$M':>8} {'Exit':>7} {'Remain':>7} {'Addr$M':>8} {'Sav$M':>7}")
for r in rows:
    print(f"{r[0]:12} {r[1]:9.0f} {r[2]:8.0f} {r[3]:7.0f} {r[4]:7.0f} {r[5]:8.0f} {r[6]:7.1f}")
print(f"Exits {exits:.0f}  Remaining {SUPPLIERS-exits:.0f}  ({exits/SUPPLIERS:.0%} reduction)")
print(f"Price savings {run_price:.1f}  Process savings {proc:.1f}  Run-rate {run:.1f} ({run/SPEND:.2%} of spend)")
print(f"Transition {trans:.1f}  One-time total {one_time:.1f}")
for name, a, b in [("Low", 0.5, 1.25), ("Base", 1, 1), ("High", 1.3, 0.9)]:
    v, cf = npv(a, b)
    cum = sum(cf[1:]); payback_months = one_time*b / (run*a*RAMP[0]) * 12
    print(f"{name}: run-rate {run*a:.0f}  3yr savings {cum:.0f}  NPV {v:.0f}  ROI {(cum-one_time*b)/(one_time*b):.1f}x  payback ~{payback_months:.1f} mo")
