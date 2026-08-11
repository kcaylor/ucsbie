#!/usr/bin/env python3
"""Rebuild the UCSB GAP landscape dataset from the 2026-07-16 baseline.

Applies the amendment register at
  2. Areas/Service/Office of Research/I&E/Landscape Analysis/GAP Landscape - Feedback Amendments (July 2026).md
Sections applied: A1-A10, B1-B7, C1-C4, E1-E3, G2.
Not applied (still open): D1-D5.
"""
import hashlib, gzip, json, os, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASS = b'XMa5-5Bea-QgLV-aBvY'
SRC = '/mnt/user-data/uploads/ucsbie/public/gap/data.enc'
OUT = '/tmp/build'
os.makedirs(OUT, exist_ok=True)
TODAY = '2026-08-10'

# ---------------------------------------------------------------- load
blob = open(SRC, 'rb').read()
key = hashlib.pbkdf2_hmac('sha256', PASS, blob[:16], 310000, 32)
rows = json.loads(gzip.decompress(AESGCM(key).decrypt(blob[16:28], blob[28:], None)))
by = {r['name']: r for r in rows}
def find(frag):
    exact = [r for r in rows if r['name'] == frag]
    if len(exact) == 1:
        return exact[0]
    m = [r for r in rows if frag.lower() in r['name'].lower()]
    assert len(m) == 1, (frag, [x['name'] for x in m])
    return m[0]

# ------------------------------------------------- C1/C2/C4 new columns
NEW_COLS = ['resource_type', 'ucsb_contact', 'listing_consent', 'targets_spinouts', 'public_listing', 'call_status']
for r in rows:
    r['resource_type'] = 'Program'
    r['ucsb_contact'] = ''
    r['targets_spinouts'] = ''
    r['listing_consent'] = ''
    r['public_listing'] = ''
    r['call_status'] = ''

UCSB_CONTACT = {
    'CNSI Technology Incubator': 'Sherylle Mills Englander',            # A3
    'Startup 360 seminar & support suite (CNSI)': 'Sherylle Mills Englander',  # A4
    'Alliance for SoCal Innovation': 'Sherylle Mills Englander',        # A5
    'Innovation 360 (CNSI)': 'Sherylle Mills Englander',
    'Space Innovation 360 (CNSI)': 'Sherylle Mills Englander',
    'CNSI SEED-TECH Grants': 'Sherylle Mills Englander',
    'CNSI-Propel Fellowships & Awards': 'Sherylle Mills Englander (program); Alana Beal Turk (matching, on leave)',
    'Climate Innovation Postdoctoral Fellows Program (CNSI)': 'Sherylle Mills Englander',
    'NSF I-Corps Regional Short Course': 'Sherylle Mills Englander; Alana Beal Turk',
    'NSF I-Corps Regional Course': 'Sherylle Mills Englander; Alana Beal Turk',
    'I-Corps Hub West partnership': 'Kelly Caylor; Tal Margalith; Alana Beal Turk',
    'OASIS (UCSB Goleta': 'Tal Margalith',
    'ACTIVATE Proof of Concept': 'Claire Driscoll (TIA)',
    'UCSB Campus Proof-of-Concept Fund': 'Claire Driscoll (TIA); Kelly Caylor',
    'New Venture Competition': 'Dave Adornetto',
    'Wilcox New Venture Incubator': 'Dave Adornetto',
    'G2 Summer Launchpad': 'Dave Adornetto',
    'Eco-Entrepreneurship (Eco-E)': 'Emily Cotter',
    'SEED-MVP Grants': 'Emily Cotter',
    'Gaucho Ventures / Gaucho Fund I': 'Kelly Caylor',
    'Osage University Partners': 'Claire Driscoll (TIA)',
}
for frag, who in UCSB_CONTACT.items():
    find(frag)['ucsb_contact'] = who

# A9 - does the investor target university spinouts?
SPINOUT_YES = ['Osage University Partners', 'Bow Capital', 'Berkeley SkyDeck Fund',
               'California Innovation Fund', 'Mission Bay Capital', 'Gaucho Ventures / Gaucho Fund I']
for r in rows:
    if r['category'] == 'Institution-Affiliated Venture Funds':
        r['targets_spinouts'] = 'Unknown - verify before public listing (Gartner, 2026-07-17)'
for frag in SPINOUT_YES:
    find(frag)['targets_spinouts'] = 'Yes'

# ------------------------------------------------------- A: corrections
# A1 OASIS - no equity, none planned; seed stage (Margalith 2026-07-16)
o = find('OASIS (UCSB Goleta')
o['award_or_value'] = ('Space and services at the Goleta R&D facility. No equity and no SAFE '
                       'instrument; OASIS does not take equity and none is currently planned.')
o['what_it_provides'] = ('Wet/dry lab and R&D space with shared services for seed-stage ventures. '
                         'Structurally similar to the CNSI Technology Incubator, but serving '
                         'seed-stage companies where CNSI serves pre-seed.')
o['stage_served'] = 'Seed stage (CNSI Technology Incubator serves pre-seed)'
o['institutional_participation'] = 'None - no equity or SAFE participation'
o['notes'] = ('Publicly announced Sept 8, 2025 (UCSB Current): long-term lease on 105,000 sq ft at '
              'South Los Carneros Rd, Goleta. OASIS takes no equity and none is planned, per Tal '
              'Margalith (2026-07-16) and confirmed by Kelly Caylor (2026-07-22). Investment-track '
              'language carried over from earlier internal planning drafts was removed in full on '
              '2026-08-10 (amendment A1); do not reintroduce it without Tal confirming.')
o['status_detail'] = ("Publicly announced Sept 8, 2025 (UCSB Current): long-term lease secured on "
                      "105,000 sq ft at South Los Carneros Rd, Goleta. innovation.ucsb.edu lists "
                      "OASIS as operational, serving early/seed-stage companies as a 'step-up' from "
                      "campus incubators. OASIS takes no equity and no equity or SAFE track is "
                      f"planned (Tal Margalith, 2026-07-16). Corrected {TODAY}, amendment A1.")

# A2 GEM - $10K, pre-seed, no equity (Margalith 2026-07-16)
g = find('Goleta Entrepreneurial Magnet')
g['award_or_value'] = '$10,000 grants. No equity.'
g['stage_served'] = 'Early-stage pre-seed'
g['status_detail'] = ('Confirmed active by Tal Margalith, 2026-07-16: $10K grants for early-stage '
                      'pre-seed efforts, no equity, aimed at building a connection between the '
                      'funded startup and Goleta/Santa Barbara. Website was recently rebuilt, so '
                      'the URL needs re-verification.')
g['notes'] = ('Only open non-dilutive pre-seed grant money a UCSB founder can reach locally. '
              'Award size corrected from "amounts not published" 2026-08-10 (amendment A2).')
g['url_verified'] = False

# A3 CNSI incubator contact
c = find('CNSI Technology Incubator')
c['operator'] = c['operator'].replace('; director Tal Margalith',
                                      '; UCSB contact Sherylle Mills Englander (Executive Director)')

# A4 Startup 360 - remove Tal
s = find('Startup 360 seminar')
s['operator'] = ('CNSI (contact Sherylle Mills Englander). Umbrella branding covering several named '
                 'sub-programs, now listed separately: Mentor in Residence, Startup Newsletter, Pitch 360.')

# A6 SEED-TECH -> Active, no open call
st = find('CNSI SEED-TECH')
st['status'] = 'Active'
st['status_detail'] = ('Active with no open call, per Sherylle Mills Englander, 2026-07-18: the '
                       'hiatus is budget-driven only, a call will issue when the budget situation '
                       'resolves, and she would find funding for a compelling ad hoc case. '
                       'Resolved from status Unclear.')
st['cadence'] = 'No open call at present; call expected when budget conditions allow'

# A7 CNSI-Propel -> Active
pr = find('CNSI-Propel')
pr['status'] = 'Active'
pr['status_detail'] = ('Active, per Sherylle Mills Englander, 2026-07-18: funding was extended and '
                       'the program is running. New mentor matches are paused for a couple of '
                       'months during Alana Beal Turk\'s maternity leave. Resolved from status Suspended.')

# A8 TCA - reframe, pending D1
t = find('TCA Venture Group')
t['name'] = 'TCA Venture Group (Tech Coast Angels) - Pasadena/LA chapters'
t['operator'] = ('TCA Venture Group, multi-chapter angel organization. Central Coast deals are '
                 'reached through the Pasadena and LA chapters; Mark Sten is the local contact '
                 '(via Sherylle Mills Englander).')
t['status_detail'] = ('CONFLICTING SOURCES, unresolved. Jonathan Gartner (2026-07-17) believes the '
                      'Santa Barbara chapter closed roughly five years ago. Sherylle Mills '
                      'Englander (2026-07-18) says TCA is active in the area through Pasadena and '
                      'LA with Mark Sten as her contact. The standing Santa Barbara chapter claim '
                      'has been dropped pending confirmation from Mark Sten. See amendment D1.')
t['url_verified'] = False

# EDC rows - contacts from Englander (handled as a correction, not a new row)
e1 = find('EDC Small Business Development Center')
e1['operator'] = e1['operator'] + ' Contacts per Sherylle Mills Englander (2026-07-18): Eric Z. at the Ventura/SB SBDC; Brendon Keiser for Santa Barbara EDC business mentoring.'

# E1 UC systemwide POC renewed
u = find('UC Systemwide Proof of Concept Pilot')
u['name'] = 'UC Systemwide Proof of Concept Program (renewed 2026-29)'
u['status'] = 'Active'
u['award_or_value'] = ('Up to $200,000/yr to UCSB with no campus match required, for three years '
                       '(FY 2026-27 through 2028-29). Systemwide commitment up to $2M/yr, $6M total.')
u['status_detail'] = ('Renewed by President Milliken, announced 2026-07-29 by Provost Katherine '
                      'Newman and Darren Cooke (PENC Chair). UCSB sits in the no-match tier with '
                      'UCR, UC Merced and UCSC. Award period Oct 1 to Sep 30; first awards possible '
                      'as early as 2026-10-01. Resolved from status Suspended.')
u['cadence'] = 'Annual, FY 2026-27 through 2028-29'
u['notes'] = ('Pilot results across ten campuses: 47 projects, 114 students, 32 invention '
              'disclosures, 27 IP filings, 17 startups. Central funds carry an expectation that '
              'each campus builds a permanent local POC fund from 2029-30, with a local funding '
              'plan due to PENC before the final installment in 2028-29.')
u['ucsb_contact'] = 'Claire Driscoll (TIA); Kelly Caylor'

uif = find('UC Innovation Fund / State POC')
uif['status_detail'] = ('Advocacy track for a recurring systemwide POC line. Partly overtaken by '
                        'the 2026-07-29 UCOP renewal (see UC Systemwide Proof of Concept Program), '
                        'which funds three years centrally but leaves the post-2029 local '
                        'sustainability requirement unaddressed. Restated 2026-08-10.')

ac = find('ACTIVATE Proof of Concept')
ac['status_detail'] = (ac['status_detail'] + ' NOTE 2026-08-10: ACTIVATE was the UCSB delivery '
                       'vehicle for the systemwide pilot. With the 2026-07-29 renewal confirmed, '
                       'confirm with Claire Driscoll whether ACTIVATE reactivates as the local '
                       'mechanism for the $200K/yr allocation.')

# E2 Space Innovation 360 -> Active
si = find('Space Innovation 360')
si['status'] = 'Active'
si['status_detail'] = ('Applications opened 2026-08-03 with a 2026-09-17 deadline, per the CNSI '
                       'announcement (Nina Myers). First running of the workshop. Resolved from '
                       'status Planned.')
si['cadence'] = 'First cohort, applications due 2026-09-17'

# G2 Chancellor's Innovation Fund replaces both the campus POC row name and the Evergreen entry
cf = find('UCSB Campus Proof-of-Concept Fund')
cf['name'] = "Chancellor's Innovation Fund (proposed campus-wide POC fund)"
cf['status_detail'] = ("Proposed campus-wide proof-of-concept fund. Supersedes and absorbs the "
                       "earlier 'UCSB Evergreen Seed Fund' concept per Kelly Caylor's bundling "
                       "decision, 2026-07-16, and replaces the prior 'UCSB Campus Proof-of-Concept "
                       "Fund' framing. Tracked calls (deep tech, OASIS-specific, quantum) are "
                       "post-launch decisions and are deliberately not enumerated. Sizing carried "
                       "forward from the TIA spec and still needs confirmation.")
cf['notes'] = ("Merged 2026-08-10 (amendment G2): the separate 'UCSB Evergreen Seed Fund' entry was "
               "removed and this row is the single proposed campus POC vehicle. None of the earlier "
               "evergreen-vehicle or facility-instrument structure carries over. Sizing (~$2M/yr, "
               "~$100K per team) is unconfirmed and should not appear in a shared document until "
               "Kelly confirms it.")
rows = [r for r in rows if 'Evergreen Seed Fund' not in r['name']]

# ------------------------------------------------------------ B: additions
nid = max(int(r['id']) for r in rows)
def add(name, cat, rtype, layer, status, provides, award, sector, url, source, *,
        operator='', detail='', eligibility='', stage='', cadence='', contact='',
        notes='', participation='', spinouts=''):
    global nid
    nid += 1
    rows.append(dict(
        id=nid, name=name, category=cat, resource_type=rtype, layer=layer, status=status,
        status_detail=(detail or f'Recommended by {source}. Not independently link-verified as of {TODAY}.'),
        operator=operator, what_it_provides=provides, award_or_value=award, sector_focus=sector,
        eligibility=eligibility, stage_served=stage, cadence=cadence, url=url, url_verified=False,
        institutional_participation=participation, notes=notes,
        sources=[f'{source} (reviewer feedback on the 2026-07-16 beta)'] + ([url] if url else []),
        ucsb_contact=contact, listing_consent='', targets_spinouts=spinouts, public_listing='',
        call_status=''))

SME = 'Sherylle Mills Englander, 2026-07-18'
COT = 'Emily Cotter, 2026-07-16/17'
VF, POC, ACL, PRE = ('Institution-Affiliated Venture Funds', 'POC Funds',
                     'Startup Accelerators', 'Pre-POC / Pipeline')

# B1 investors and funds
add('Central Coast Ventures', VF, 'Program', 'Regional', 'Active',
    'Venture firm based in San Luis Obispo that invests in Santa Barbara companies.',
    'Not published', 'Generalist regional', 'https://centralcoast.ventures/', SME,
    operator='Central Coast Ventures. Contacts: Steve Larsen or JoAnn Miller.',
    spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')
add('Sustainable Change Alliance', VF, 'Program', 'Regional', 'Active',
    'Santa Barbara organization that has coordinated angel investments; several members have '
    'invested in Bren startups. Also runs an Impact Investing Summit (listed separately).',
    'Individual angel checks; no confirmed fund', 'Sustainability and impact',
    'https://www.sustainablechangealliance.org/', f'{SME}; {COT}',
    detail='Flagged independently by Englander and Cotter. Cotter notes Jonathan Gartner told her '
           'some years ago they were developing a fund. Whether a fund now exists is unconfirmed '
           '(amendment D4).',
    spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')
add('Propeller VC', VF, 'Program', 'Private-external', 'Active',
    'Venture fund investing in ocean and climate ventures.', 'Not published',
    'Ocean, climate', 'https://propellervc.com/', COT,
    spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')
add('Better Ventures', VF, 'Program', 'Private-external', 'Active',
    'Early-stage impact venture fund.', 'Not published', 'Impact, climate, health',
    'https://www.better.vc/', COT, spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')
add('Sea Forward Fund', VF, 'Program', 'Private-external', 'Active',
    'Fund supporting ocean-focused ventures.', 'Not published', 'Ocean / blue economy',
    'https://seaforwardfund.org/', COT, spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')
add('Schmidt Marine Technology Partners', VF, 'Program', 'Private-external', 'Active',
    'Philanthropic program funding marine technology development.', 'Not published',
    'Marine technology', 'https://schmidtmarine.org/', COT,
    spinouts='Unknown - verify before public listing (Gartner, 2026-07-17)')

# B2 POC funds
add('Rocket Fund (Caltech)', POC, 'Program', 'Private-external', 'Active',
    'Proof-of-concept and early commercialization support for climate and energy technologies.',
    'Not published', 'Climate, energy', 'https://rocketfund.caltech.edu/', SME,
    detail=f'Recommended by {SME}, who rates it highly. Confirm UCSB eligibility. Not independently link-verified as of {TODAY}.')
add('Keeling Curve Prize', POC, 'Program', 'Private-external', 'Active',
    'Annual prize for projects that reduce or remove greenhouse gases.', 'Prize award',
    'Climate', 'https://www.climatecurve.org/kcp', COT)
add('Echoing Green Fellowship', PRE, 'Program', 'Private-external', 'Active',
    'Fellowship and seed funding for early-stage social-impact leaders.',
    'Fellowship stipend + seed funding', 'Social impact', 'https://echoinggreen.org/', COT)

# B3 incubators and accelerators
add('UCLA Magnify', ACL, 'Program', 'UC system', 'Active',
    "CNSI UCLA's incubator, with access to the UCLA medical campus. CNSI UCSB and Magnify trade companies.",
    'Incubator space and services', 'Deep tech, biotech, medtech', 'https://magnify.cnsi.ucla.edu/', SME,
    operator='CNSI, UCLA', contact='Sherylle Mills Englander')
add('Silicon Catalyst', ACL, 'Program', 'Private-external', 'Active',
    'Bay Area incubator/accelerator for semiconductor and chip-based startups.',
    'In-kind design tools, foundry access, mentorship; investment through affiliated angels',
    'Semiconductors, photonics, chip-based hardware', 'https://siliconcatalyst.com/', SME,
    notes="Englander flags this as aligned to UCSB's strongest research area.")
add('JLabs San Francisco (Johnson & Johnson Innovation)', ACL, 'Program', 'Private-external', 'Active',
    'No-strings biotech incubator with lab space and corporate resources.',
    'Lab space and services; no equity taken', 'Biotech, medtech, health',
    'https://jnjinnovation.com/locations/jlabs/jlabs-san-francisco', SME)
add('UCLA Anderson Venture Accelerator', ACL, 'Program', 'UC system', 'Active',
    'Accelerator run out of the Price Center at UCLA Anderson.', 'In-kind program',
    'All sectors', 'https://www.anderson.ucla.edu/about/centers/price-center-for-entrepreneurship-and-innovation/anderson-venture-accelerator', COT)
add('UC Davis Big Bang Competition', PRE, 'Program', 'UC system', 'Active',
    'Business plan competition run by the Mike and Renee Child Institute.', 'Competition prizes',
    'All sectors', 'https://innovate.ucdavis.edu/big-bang-competition', COT,
    notes='Confirm UCSB team eligibility, as Big Ideas is now Berkeley-only.')
add('Food System 6 (FS6)', ACL, 'Program', 'Private-external', 'Active',
    'Accelerator for food and agriculture ventures.', 'In-kind accelerator program',
    'Food, agriculture', 'https://www.foodsystem6.org/', COT,
    notes='Not to be confused with F6S, a separate platform also listed.')
add('Sea Ahead', ACL, 'Program', 'Private-external', 'Active',
    'Blue-economy venture platform and accelerator.', 'In-kind program', 'Ocean / blue economy',
    'https://www.sea-ahead.com/', COT)

# B4 facilities
add('CNSI Innovation Workshop', '', 'Facility', 'UCSB campus', 'Active',
    'Prototyping and design workshop, heavily used by startups designing products and devices.',
    'Facility access', 'All', 'https://www.cnsi.ucsb.edu/innovation/innovation-workshop', SME,
    operator='CNSI, UC Santa Barbara', contact='Brian Dincau')
add('FathomWerx', '', 'Facility', 'Regional', 'Active',
    'Ventura-based prototyping and technology development facility with several routes to access.',
    'Facility access and collaboration', 'Defense, maritime, dual-use',
    'https://www.fathomwerx.com/', SME,
    detail=f'Recommended by {SME}, who notes there are several ways in. Not independently link-verified as of {TODAY}.')

# B5 events
add('Central Coast Innovation Awards', '', 'Event', 'Regional', 'Active',
    'Annual awards event run by the Pacific Coast Business Times. Startups receive tables by '
    'invitation only; others can get comped tickets because UCSB is a title sponsor.',
    'Exposure and networking; no funding', 'All', '', SME,
    detail='Invite-only. CNSI, in consultation with others, identifies and invites companies. Per '
           'Englander (2026-07-18), do not list as an open opportunity. No dedicated website; the '
           'Pacific Coast Business Times page is the reference.',
    contact='Sherylle Mills Englander',
    notes='Listed as an event with a UCSB contact rather than an opportunity (amendment C3).')
add('Born in California (UC Irvine)', '', 'Event', 'UC system', 'Active',
    'UC-wide startup showcase hosted by UC Irvine.', 'Exposure and investor access; no funding',
    'All', 'https://innovation.uci.edu/born-in-california/', f'{SME}; {COT}',
    detail='Invite-only. CNSI is responsible for identifying and inviting UCSB companies; the '
           'event does not want open calls. Per Englander (2026-07-18), list as an event with a '
           'UCSB contact.',
    contact='Sherylle Mills Englander',
    notes='Listed as an event with a UCSB contact rather than an opportunity (amendment C3).')
add('Sustainable Change Alliance Impact Investing Summit', '', 'Event', 'Regional', 'Active',
    'Impact investing summit; CNSI helps coordinate UCSB startup participation.',
    'Investor exposure; no funding', 'Sustainability and impact',
    'https://www.sustainablechangealliance.org/', SME, contact='Sherylle Mills Englander')
add('UCLA MedTech Partnering Conference', '', 'Event', 'UC system', 'Active',
    'Partnering conference connecting medtech ventures with industry and investors.',
    'Partnering meetings; no funding', 'Medtech, health',
    'https://www.universitylabpartners.org/our-events/ucla-medtech-partnering-conference', SME)

# B6 support services
add('LARTA Institute', '', 'Support Service', 'Private-external', 'Active',
    'Technical and business assistance to startups in key market areas, including federal '
    'commercialization assistance programs.', 'Advisory services', 'All',
    'https://larta.org/', SME)
add('SoCalBio', '', 'Support Service', 'Private-external', 'Active',
    'Southern California bioscience trade organization. Purchase discounts and a range of programming.',
    'Membership benefits', 'Bioscience, biotech', 'https://socalbio.org/', SME,
    detail='UCSB membership secured. Office of Research approved the $750 fee on 2026-07-27 and it '
           'was charged to an OR chartstring (amendment E3). Membership is held jointly by '
           'CNSI/OASIS.',
    contact='Sherylle Mills Englander; Tal Margalith',
    participation='UCSB holds an institutional membership (paid by Office of Research, 2026-07)')
add('Apex Accelerator', '', 'Support Service', 'Federal', 'Active',
    'Helps startups reach federal procurement, with a defense focus.', 'Advisory services',
    'Defense, dual-use, federal procurement', 'https://www.apexaccelerators.us/', SME)
add('Startup Legal Garage', '', 'Support Service', 'Private-external', 'Active',
    'Law-student-staffed legal services for early-stage startups. Used by Bren alumni entrepreneurs.',
    'Pro bono / low-cost legal work', 'All', 'https://www.startuplegalgarage.org/', COT,
    notes='Category decision: legal services, outside the four GAP categories (amendment C1).')
add('F6S', '', 'Support Service', 'Private-external', 'Active',
    'Platform connecting startups with advisors, programs and funding opportunities.',
    'Platform access', 'All', 'https://innovation.f6s.com/', COT,
    notes='Surfaced through the MESM 2026 Eco-E project MediMRF. Not to be confused with Food '
          'System 6 (FS6), a separate accelerator also listed.')

# B7 Startup 360 sub-programs
add('CNSI Mentor in Residence Program', PRE, 'Program', 'UCSB campus', 'Active',
    'Experienced entrepreneur available to advise UCSB startups and founders.',
    'In-kind mentoring', 'All research areas', 'https://www.cnsi.ucsb.edu/innovation/start-up-resources', SME,
    operator='CNSI, UC Santa Barbara', contact='Jonathan Gartner',
    detail='Broken out of the Startup 360 umbrella per Englander, 2026-07-18.')
add('CNSI Startup Newsletter', PRE, 'Program', 'UCSB campus', 'Active',
    'Newsletter carrying startup opportunities, calls and events to the campus community.',
    'In-kind information channel', 'All research areas',
    'https://www.cnsi.ucsb.edu/innovation/start-up-resources', SME,
    operator='CNSI, UC Santa Barbara', contact='Alana Beal Turk',
    detail='Broken out of the Startup 360 umbrella per Englander, 2026-07-18.')
add('CNSI Pitch 360', PRE, 'Program', 'UCSB campus', 'Active',
    'Pitch practice and feedback sessions for UCSB startups.', 'In-kind program',
    'All research areas', 'https://www.cnsi.ucsb.edu/innovation/start-up-resources', SME,
    operator='CNSI, UC Santa Barbara', contact='Sherylle Mills Englander',
    detail='Broken out of the Startup 360 umbrella per Englander, 2026-07-18.')

# --------------------------------------------- C2 consent + A10 public build
for r in rows:
    if r['layer'] in ('UCSB campus', 'UCSB-affiliated', 'UC system'):
        r['listing_consent'] = 'Not required - UC/UCSB program'
    elif r['layer'] in ('Federal', 'State'):
        r['listing_consent'] = 'Not required - public program'
    elif r['category'] == 'Institution-Affiliated Venture Funds':
        r['listing_consent'] = 'Required - not obtained'
    else:
        r['listing_consent'] = 'Not required - public program or service'

    if r['status'] == 'Defunct':
        r['public_listing'] = 'Hide - defunct (A10, Driscoll 2026-07-17)'
    elif r['listing_consent'].startswith('Required'):
        r['public_listing'] = 'Hide - listing consent not obtained (C2)'
    elif r['resource_type'] == 'Event' and 'Invite-only' in (r['status_detail'] or ''):
        r['public_listing'] = 'Show as event with UCSB contact, not as an open opportunity (C3)'
    else:
        r['public_listing'] = 'Show'

# C5 - call status, separate from program status (Englander 2026-07-18 via VuVu decision #4).
# Populated only where there is evidence; blank means not yet determined.
CALL = {
    'CNSI SEED-TECH': 'No open call (budget pause; call to reissue)',
    'CNSI-Propel': 'Open (new mentor matches paused during leave)',
    'Space Innovation 360': 'Open - applications close 2026-09-17',
    'UC Systemwide Proof of Concept Program': 'Opening - first awards possible 2026-10-01',
    'Space Vandenberg Innovation Fund': 'First call Fall 2026',
    'ACTIVATE Proof of Concept': 'No open call',
    'Born in California': 'Invite-only - CNSI selects UCSB companies',
    'Central Coast Innovation Awards': 'Invite-only - CNSI selects UCSB companies',
    'UC LAUNCH': 'Open - two cohorts per year',
    'Goleta Entrepreneurial Magnet': 'Open',
}
for frag, cs in CALL.items():
    find(frag)['call_status'] = cs
for r in rows:
    if r['status'] == 'Defunct':
        r['call_status'] = 'Closed'
    elif r['status'] == 'Suspended' and not r['call_status']:
        r['call_status'] = 'No open call'

rows.sort(key=lambda r: int(r['id']))
json.dump(rows, open(f'{OUT}/data.json', 'w'), ensure_ascii=False, indent=1)

# ------------------------------------------------------------- report
from collections import Counter
print(f'rows: {len(rows)}')
print('by status:', dict(Counter(r['status'] for r in rows)))
print('by resource_type:', dict(Counter(r['resource_type'] for r in rows)))
print('by category:', dict(Counter(r['category'] or '(none)' for r in rows)))
print('public build shows:', sum(1 for r in rows if r['public_listing'].startswith('Show')))
print('hidden:', dict(Counter(r['public_listing'] for r in rows if r['public_listing'].startswith('Hide'))))
