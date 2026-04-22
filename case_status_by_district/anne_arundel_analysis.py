import csv
from collections import defaultdict

csv_path = r"c:\Users\Sebastian Grammas\Desktop\MD_County_Case_DF\case_status_by_district\DC_FD_ByCaseType (1).csv"

# {year: {disposition: count}}
dui = defaultdict(lambda: defaultdict(int))
criminal = defaultdict(lambda: defaultdict(int))

with open(csv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['County'] != 'Anne Arundel':
            continue
        if row['Count Description'] != 'Disposition':
            continue

        fy = row['FY']
        case_type = row['DC Case Type']
        disposition = row['Filing/Disposition Type'].strip()
        count = int(row['Count'])

        if case_type == 'DUI/DWI':
            dui[fy][disposition] += count
        elif case_type == 'Criminal':
            criminal[fy][disposition] += count

SUCCESSFUL = {'Guilty', 'Probation Before Judgment'}
EXCLUDE_DUI = {'Jury Trial Prayer'}
EXCLUDE_CRIMINAL = {'Forwarded to Circuit Court', 'Jury Trial Prayer'}

years = sorted(set(list(dui.keys()) + list(criminal.keys())))

SEP = "=" * 80

print(SEP)
print("ANNE ARUNDEL COUNTY — DUI/DWI CASES BY FISCAL YEAR")
print("  Excluded from total: Jury Trial Prayer")
print("  Successful = Guilty + Probation Before Judgment")
print(SEP)
print(f"{'Year':<8} {'Excl JTP':>10} {'Adj Total':>10} {'Guilty':>8} {'PBJ':>8} {'Successful':>12} {'Other':>8} {'Success%':>10}")
print("-" * 90)
for yr in years:
    if yr not in dui:
        continue
    d = dui[yr]
    jtp = d.get('Jury Trial Prayer', 0)
    total = sum(d.values())
    adj_total = total - jtp
    guilty = d.get('Guilty', 0)
    pbj = d.get('Probation Before Judgment', 0)
    successful = guilty + pbj
    other = adj_total - successful
    pct = (successful / adj_total * 100) if adj_total else 0
    print(f"{yr:<8} {jtp:>10,} {adj_total:>10,} {guilty:>8,} {pbj:>8,} {successful:>12,} {other:>8,} {pct:>9.1f}%")

print()
print("  Breakdown of 'Other' outcomes (after excluding Jury Trial Prayer):")
all_dui_dispositions = set()
for d in dui.values():
    all_dui_dispositions |= d.keys()
other_dui = sorted(all_dui_dispositions - SUCCESSFUL - EXCLUDE_DUI)
print(f"  {'Year':<8}", end="")
for outcome in other_dui:
    print(f"  {outcome[:14]:>14}", end="")
print()
for yr in years:
    if yr not in dui:
        continue
    d = dui[yr]
    print(f"  {yr:<8}", end="")
    for outcome in other_dui:
        print(f"  {d.get(outcome, 0):>14,}", end="")
    print()

print()
print(SEP)
print("ANNE ARUNDEL COUNTY — CRIMINAL CASES BY FISCAL YEAR")
print("  Excluded from total: Forwarded to Circuit Court, Jury Trial Prayer")
print("  Successful = Guilty + Probation Before Judgment")
print(SEP)
print(f"{'Year':<8} {'Filed':>8} {'Excl CC':>8} {'Excl JTP':>8} {'Adj Total':>10} {'Guilty':>8} {'PBJ':>8} {'Success':>10} {'Other':>8} {'Success%':>10}")
print("-" * 100)
for yr in years:
    if yr not in criminal:
        continue
    c = criminal[yr]
    fwd_cc = c.get('Forwarded to Circuit Court', 0)
    jtp = c.get('Jury Trial Prayer', 0)
    excluded = fwd_cc + jtp
    total_disp = sum(c.values())
    adj_total = total_disp - excluded
    guilty = c.get('Guilty', 0)
    pbj = c.get('Probation Before Judgment', 0)
    successful = guilty + pbj
    other = adj_total - successful
    pct = (successful / adj_total * 100) if adj_total else 0
    print(f"{yr:<8} {total_disp:>8,} {fwd_cc:>8,} {jtp:>8,} {adj_total:>10,} {guilty:>8,} {pbj:>8,} {successful:>10,} {other:>8,} {pct:>9.1f}%")

print()
print("  Breakdown of 'Other' outcomes (after excluding Circuit Court + Jury Trial Prayer):")
all_crim_dispositions = set()
for d in criminal.values():
    all_crim_dispositions |= d.keys()
other_crim = sorted(all_crim_dispositions - SUCCESSFUL - EXCLUDE_CRIMINAL)
print(f"  {'Year':<8}", end="")
for outcome in other_crim:
    print(f"  {outcome[:16]:>16}", end="")
print()
for yr in years:
    if yr not in criminal:
        continue
    c = criminal[yr]
    print(f"  {yr:<8}", end="")
    for outcome in other_crim:
        print(f"  {c.get(outcome, 0):>16,}", end="")
    print()

print()
print(SEP)
print("COMBINED SUMMARY — Successful outcomes (DUI/DWI + Criminal) by year")
print(SEP)
print(f"{'Year':<8} {'DUI Success':>12} {'DUI Total':>10} {'DUI%':>7} {'Crim Success':>13} {'Crim Adj':>10} {'Crim%':>7} {'Combined':>10} {'Comb Total':>12} {'Comb%':>8}")
print("-" * 105)
for yr in years:
    d = dui.get(yr, {})
    c = criminal.get(yr, {})

    dui_succ = d.get('Guilty', 0) + d.get('Probation Before Judgment', 0)
    dui_total = sum(d.values()) - d.get('Jury Trial Prayer', 0)
    dui_pct = (dui_succ / dui_total * 100) if dui_total else 0

    fwd_cc = c.get('Forwarded to Circuit Court', 0)
    jtp = c.get('Jury Trial Prayer', 0)
    crim_total_disp = sum(c.values())
    crim_adj = crim_total_disp - fwd_cc - jtp
    crim_succ = c.get('Guilty', 0) + c.get('Probation Before Judgment', 0)
    crim_pct = (crim_succ / crim_adj * 100) if crim_adj else 0

    comb_succ = dui_succ + crim_succ
    comb_total = dui_total + crim_adj
    comb_pct = (comb_succ / comb_total * 100) if comb_total else 0

    print(f"{yr:<8} {dui_succ:>12,} {dui_total:>10,} {dui_pct:>6.1f}% {crim_succ:>13,} {crim_adj:>10,} {crim_pct:>6.1f}% {comb_succ:>10,} {comb_total:>12,} {comb_pct:>7.1f}%")
