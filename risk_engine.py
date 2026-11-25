from datetime import date
import re


def assess_ownership_risk(year, km_driven, owners=None, gearbox_type=None,
                          fuel=None, induction=None, e20_compatibility=None,
                          has_insurance=None):
    def norm(x):
        return str(x or '').strip().lower()
    age = date.today().year - int(year)
    km = int(km_driven)
    if age < 0 or km < 0:
        raise ValueError('Invalid year or mileage')
    rows = []
    def add(name, maximum, points, note):
        rows.append(dict(Factor=name, Maximum=maximum, Points=points, Explanation=note))
    add('Age',20, next(p for limit,p in [(3,0),(5,5),(8,10),(12,15),(999,20)] if age<=limit), f'{age} years old; inspect age-related wear.')
    add('Mileage',25,next(p for limit,p in [(30000,0),(60000,5),(90000,10),(120000,18),(float('inf'),25)] if km<limit),f'{km:,} km; inspect wear and scheduled maintenance.')
    o=norm(owners)
    match=re.fullmatch(r'(\d+)(?:st|nd|rd|th)?(?:\s+owners?)?',o)
    n=int(match.group(1)) if match else next((i for i,w in enumerate(['first','second','third','fourth','fifth'],1) if o in (w,w+' owner')),None)
    add('Owner count',10, None if not n else [0,3,6,10][min(n,4)-1], 'Verify ownership chain; count alone does not establish condition.')
    g=norm(gearbox_type)
    if 'manual' in g and 'automated' not in g: gp=0
    elif any(w in g for w in ('dct','dsg','dual clutch','dual-clutch')): gp=10 if km>=80000 else 0
    elif any(w in g for w in ('amt','cvt','torque converter','automated manual')): gp=5 if km>=80000 else 0
    else: gp=None
    add('Gearbox',10,gp,'Verify transmission subtype and inspect operation and maintenance requirements.')
    f=norm(fuel)
    fp=10 if f=='diesel' and km>=100000 else 5 if f in ('cng','lpg') and km>=100000 else 0 if f in ('petrol','diesel','cng','lpg') else None
    add('Fuel system',10,fp,'Check fuel-specific components; EV/hybrid battery risk is not assessed by these rules.')
    i=norm(induction)
    if f=='electric': pass
    else:
        ip=10 if 'turbo' in i and km>=80000 else 0 if 'turbo' in i or i in ('na','n/a','naturally aspirated','natural aspiration') else None
        add('Induction',10,ip,'For turbo engines, inspect oil leaks, boost and service records.')
    if f not in ('diesel','electric'):
        e=norm(e20_compatibility)
        ep={'yes':0,'no':10}.get(e) if f=='petrol' else None
        add('E20 compatibility',10,ep,'Reported incompatibility: consult manufacturer on approved fuel.' if ep==10 else 'Reported compatible; verify manufacturer guidance.' if ep==0 else 'Verify petrol use and manufacturer E20 approval.')
    ins=norm(has_insurance)
    add('Insurance',5,{'yes':0,'no':5,'true':0,'false':5}.get(ins),'Verify policy validity, coverage and transfer requirements.')
    applicable=sum(r['Maximum'] for r in rows)
    known=sum(r['Maximum'] for r in rows if r['Points'] is not None)
    points=sum(r['Points'] or 0 for r in rows)
    score=round(100*points/known)
    coverage=round(100*known/applicable)
    category='Low' if score<=25 else 'Moderate' if score<=50 else 'High' if score<=75 else 'Very High'
    return dict(score=score, coverage=coverage, category=category, breakdown=rows,
                unknowns=[r['Factor'] for r in rows if r['Points'] is None])
