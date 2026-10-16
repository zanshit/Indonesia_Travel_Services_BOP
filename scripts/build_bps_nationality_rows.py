"""Build 03_extract/bps_nationality_rows.csv: every row label of BPS vars 272, 331, 356, 1470 and of the 2025 publication
tables (Pengeluaran Tabel 14/15/27, Kunjungan Lampiran 3), side by side, with ISO3 where the row is a single country.

Run:  python -I scripts/build_bps_nationality_rows.py   (needs the CSVs written by fetch_bps_api.py / extract_bps_pdfs.py)
The ISO3 mapping below is a hand-built dictionary (variant -> ISO3). Anything not in it is flagged UNMAPPED, never guessed.
Entities that are cities, sub-national parts, historical names or ambiguous are flagged in `note` and given a blank ISO3
unless the identity is unambiguous.
"""
import os, sys, re, csv, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bps_common import EXTRACT, write_csv

# iso3 | English name | variants (lower-case, ';'-separated)   -- single countries / territories
C = """
MYS|Malaysia|malaysia
SGP|Singapore|singapore;singapura
TLS|Timor-Leste|timor leste;east timor;timor-leste
IDN|Indonesia|indonesia
PHL|Philippines|philippines;filipina;phillippiness
THA|Thailand|thailand;tailan
VNM|Vietnam|vietnam
MMR|Myanmar|myanmar;myanmar/burma;burma
BRN|Brunei Darussalam|brunei darussalam
KHM|Cambodia|kamboja;cambodia
LAO|Laos|laos
HKG|Hong Kong|hong kong;hongkong, rrt
CHN|China|republik rakyat tiongkok;tiongkok;china;cina;people's republic of china
IND|India|india
KOR|South Korea|south korea;korea selatan;korea rep.;korea
JPN|Japan|japan;jepang
TUR|Turkey|turki;turkey
MNG|Mongolia|mongolia
KAZ|Kazakhstan|kazakhstan
PAK|Pakistan|pakistan
UZB|Uzbekistan|uzbekistan
BGD|Bangladesh|bangladesh
NPL|Nepal|nepal
TWN|Taiwan|taiwan
LKA|Sri Lanka|srilanka;sri lanka
MDV|Maldives|maladewa
KGZ|Kyrgyzstan|kirgistan
TJK|Tajikistan|tajikhistan
BTN|Bhutan|bhutan
AFG|Afghanistan|afganistan
TKM|Turkmenistan|turkmenistan
PRK|North Korea|korea utara
MAC|Macao|macao, rrt
IOT|British Indian Ocean Territory|british indian ocean teritory
SAU|Saudi Arabia|saudi arabia;arab saudi
OMN|Oman|oman
EGY|Egypt|egypt;mesir
JOR|Jordan|jordan
ARE|United Arab Emirates|uni emirat arab;u. arab emirates;united arab emirates
YEM|Yemen|yaman;yemen
IRN|Iran|iran
KWT|Kuwait|kuwait
IRQ|Iraq|irak
SYR|Syria|syiria
PSE|Palestine|palestina
LBN|Lebanon|libanon
BHR|Bahrain|bahrain
QAT|Qatar|qatar
ISR|Israel|israel
GBR|United Kingdom|united kingdom;inggris;inggris raya;great britain
RUS|Russia|rusia;russia;federasi rusia
FRA|France|france;perancis
DEU|Germany|germany;jerman;gemany
NLD|Netherlands|netherlands;belanda
ITA|Italy|italy;italia
ESP|Spain|spain;spanyol
POL|Poland|polandia
UKR|Ukraine|ukraine
SWE|Sweden|sweden;swedia
DNK|Denmark|denmark
CHE|Switzerland|switzerland;swiss
PRT|Portugal|portugal
CZE|Czechia|ceko
IRL|Ireland|irlandia;ireland
BEL|Belgium|belgium;belgia
NOR|Norway|norway;norwegia
ROU|Romania|romania
HUN|Hungary|hongaria
FIN|Finland|finland;finlandia
BLR|Belarus|belarus
LTU|Lithuania|lithuania
SVK|Slovakia|slovakia
EST|Estonia|estonia
BGR|Bulgaria|bulgaria
GRC|Greece|yunani;greece;hellenic
LVA|Latvia|latvia
HRV|Croatia|croasia
ISL|Iceland|iceland;islandia
MLT|Malta|malta
LUX|Luxembourg|luxemburg
LIE|Liechtenstein|liechtenstein
MCO|Monaco|monako
AND|Andorra|andorra
SMR|San Marino|san marino
ABW|Aruba|aruba
VAT|Vatican City|vatikan
BFA|Burkina Faso|burkina faso;burkinabe;volta atas
SRB|Serbia|serbia
SVN|Slovenia|slovenia
ARM|Armenia|armenia
AZE|Azerbaijan|azerbaijan
CYP|Cyprus|cyprus
MKD|North Macedonia|macedonia
BIH|Bosnia and Herzegovina|bosnia herzegovina
GEO|Georgia|georgia
ALB|Albania|albania
MDA|Moldova|moldova
MNE|Montenegro|montenegro
XKX|Kosovo|republik cosovo
AUT|Austria|austria
USA|United States|united states of america;amerika serikat;u s a;usa
CAN|Canada|canada;kanada
BRA|Brazil|brazilia;brazil
COL|Colombia|kolombia
ARG|Argentina|argentina
MEX|Mexico|mexiko;meksiko;mexico
CHL|Chile|chili
CRI|Costa Rica|costarika
GTM|Guatemala|guatemala
PAN|Panama|panama
HND|Honduras|honduras
SLV|El Salvador|el salvador
NIC|Nicaragua|nicaragua
BLZ|Belize|belize
PER|Peru|peru
VEN|Venezuela|venezuela
ECU|Ecuador|ekuador
URY|Uruguay|uruguay
PRY|Paraguay|paraguay
BOL|Bolivia|bolivia
SUR|Suriname|suriname
GUY|Guyana|guyana
FLK|Falkland Islands|falkland islands
CUB|Cuba|kuba
DMA|Dominica|dominika
TTO|Trinidad and Tobago|trinidad & tobago
KNA|Saint Kitts and Nevis|st. kitts & nevis;st. christopher
JAM|Jamaica|jamaika
BRB|Barbados|barbados
GRD|Grenada|grenadines (grenada)
LCA|Saint Lucia|st. lucia
ATG|Antigua and Barbuda|antigua & barbuda
BHS|Bahamas|bahama islands
HTI|Haiti|haiti
DOM|Dominican Republic|dominika rep.
VCT|Saint Vincent and the Grenadines|st. vincent
BMU|Bermuda|bermuda
MTQ|Martinique|martinique
PRI|Puerto Rico|puertorico
GLP|Guadeloupe|guadelope
AUS|Australia|australia
PNG|Papua New Guinea|papua new guinea;papua nugini
NZL|New Zealand|new zealand;selandia baru
FJI|Fiji|fiji islands
VUT|Vanuatu|vanuatu
TON|Tonga|tonga
SLB|Solomon Islands|solomon islands
WSM|Samoa|samoa;samoa barat
NRU|Nauru|nauru
PLW|Palau|palau rep.
COK|Cook Islands|cooks islands
GUM|Guam|guam
NCL|New Caledonia|kaledonia
KIR|Kiribati|karibati (kiribati)
MHL|Marshall Islands|marshall islands
FSM|Micronesia (Federated States)|micronesia rep.
NIU|Niue|niue
TUV|Tuvalu|tuvalu
WLF|Wallis and Futuna|walis & futuna
ZAF|South Africa|south africa;afrika selatan
MAR|Morocco|maroko
KEN|Kenya|kenya
TUN|Tunisia|tunisia
DZA|Algeria|aljazair / algeria;algeria
MUS|Mauritius|mauritius
TZA|Tanzania|tanzania
LBY|Libya|libya
NGA|Nigeria|nigeria
MOZ|Mozambique|mozambik
ZWE|Zimbabwe|zimbabwe
SDN|Sudan|sudan
SOM|Somalia|somalia
GHA|Ghana|ghana
CMR|Cameroon|kamerun
UGA|Uganda|uganda
MDG|Madagascar|malagasy (madagascar)
ETH|Ethiopia|ethiopia
COD|DR Congo|congo rep. dem.;zaire
SYC|Seychelles|seychelles
RWA|Rwanda|rwanda
ZMB|Zambia|zambia
MWI|Malawi|malawi
SEN|Senegal|senegal
COM|Comoros|comoros
MLI|Mali|mali
ERI|Eritrea|eritrea
TCD|Chad|chad
SLE|Sierra Leone|sierra leona
NAM|Namibia|namibia
GMB|Gambia|gambia
BWA|Botswana|bostwana
LBR|Liberia|liberia
SWZ|Eswatini|swaziland
GIN|Guinea|guinea
CPV|Cabo Verde|cape verde
CIV|Cote d'Ivoire|ivory coast (pantai gading);ivory coast;pantai gading
COG|Congo (Republic)|congo
BDI|Burundi|burundi
MRT|Mauritania|mauritania
TGO|Togo|togo
GAB|Gabon|gabon
LSO|Lesotho|lesotho
SSD|South Sudan|south sudan
NER|Niger|niger
DJI|Djibouti|djibouti
GNQ|Equatorial Guinea|guinea equator
CAF|Central African Republic|afrika tengah rep.
AGO|Angola|angola
BEN|Benin|benin
STP|Sao Tome and Principe|sao tome & principe
GNB|Guinea-Bissau|guinea bissau
ESH|Western Sahara|sahara
"""

# non-country / group / ambiguous rows: variant -> (canonical key, English name, row_type, note)
G = {
 "asean": ("GROUP:ASEAN_SUBTOTAL", "ASEAN (subtotal)", "region_subtotal", ""),
 "1. asean": ("GROUP:ASEAN_SUBTOTAL", "ASEAN (subtotal)", "region_subtotal", "publication group heading"),
 "total asean": ("GROUP:ASEAN_SUBTOTAL", "ASEAN (subtotal)", "region_subtotal", ""),
 "asean lainnya": ("GROUP:OTHER_ASEAN", "Other ASEAN", "residual_group", ""),
 "asean lainnya/other asean": ("GROUP:OTHER_ASEAN", "Other ASEAN", "residual_group", ""),
 "other asia": ("GROUP:OTHER_ASIA", "Other Asia (excl. ASEAN, Middle East)", "residual_group", ""),
 "asia lainnya": ("GROUP:OTHER_ASIA", "Other Asia (excl. ASEAN, Middle East)", "residual_group", ""),
 "lain-lain": ("GROUP:OTHER_ASIA_LAINLAIN", "Lain-lain (listed in the Asia block of var 1470)", "residual_group", "unclear residual; sits in the Asia block just before TOTAL ASIA"),
 "total asia (excl.asean)": ("GROUP:ASIA_EXCL_ASEAN_SUBTOTAL", "Asia excl. ASEAN (subtotal)", "region_subtotal", ""),
 "2. asia (excl. asean & middle east)": ("GROUP:ASIA_EXCL_ASEAN_SUBTOTAL", "Asia excl. ASEAN (subtotal)", "region_subtotal", "publication group heading; also excludes Middle East"),
 "total asia (excl. asean & middle east)": ("GROUP:ASIA_EXCL_ASEAN_SUBTOTAL", "Asia excl. ASEAN (subtotal)", "region_subtotal", ""),
 "other middle east": ("GROUP:OTHER_MIDDLE_EAST", "Other Middle East", "residual_group", ""),
 "timur tengah lainnya": ("GROUP:OTHER_MIDDLE_EAST", "Other Middle East", "residual_group", ""),
 "total middle east": ("GROUP:MIDDLE_EAST_SUBTOTAL", "Middle East (subtotal)", "region_subtotal", ""),
 "3. timur tengah/middle east": ("GROUP:MIDDLE_EAST_SUBTOTAL", "Middle East (subtotal)", "region_subtotal", "publication group heading"),
 "total timur tengah": ("GROUP:MIDDLE_EAST_SUBTOTAL", "Middle East (subtotal)", "region_subtotal", ""),
 "other west europe": ("GROUP:OTHER_WEST_EUROPE", "Other West Europe", "residual_group", ""),
 "eropa barat lainnya": ("GROUP:OTHER_WEST_EUROPE", "Other West Europe", "residual_group", ""),
 "other east europe": ("GROUP:OTHER_EAST_EUROPE", "Other East Europe", "residual_group", ""),
 "eropa timur lainnya": ("GROUP:OTHER_EAST_EUROPE", "Other East Europe", "residual_group", ""),
 "total europe": ("GROUP:EUROPE_SUBTOTAL", "Europe (subtotal)", "region_subtotal", ""),
 "4. eropa/europe": ("GROUP:EUROPE_SUBTOTAL", "Europe (subtotal)", "region_subtotal", "publication group heading"),
 "total eropa": ("GROUP:EUROPE_SUBTOTAL", "Europe (subtotal)", "region_subtotal", ""),
 "central america": ("GROUP:CENTRAL_AMERICA", "Central America (group)", "regional_group", "BPS group; in var 1470 Costa Rica, Guatemala, Panama, Honduras, El Salvador, Nicaragua, Belize are also listed separately"),
 "amerika tengah": ("GROUP:CENTRAL_AMERICA", "Central America (group)", "regional_group", "BPS group row in var 272/356"),
 "south america": ("GROUP:SOUTH_AMERICA", "South America (group)", "regional_group", "BPS group; Peru, Venezuela, Ecuador etc. are also listed separately in var 1470"),
 "amerika selatan": ("GROUP:SOUTH_AMERICA", "South America (group)", "regional_group", "BPS group row in var 272/356; Brazil, Argentina, Colombia, Chile are listed separately in var 1470"),
 "other america": ("GROUP:OTHER_AMERICA", "Other America", "residual_group", ""),
 "amerika lainnya": ("GROUP:OTHER_AMERICA", "Other America", "residual_group", ""),
 "total america": ("GROUP:AMERICA_SUBTOTAL", "America (subtotal)", "region_subtotal", ""),
 "5. amerika/america": ("GROUP:AMERICA_SUBTOTAL", "America (subtotal)", "region_subtotal", "publication group heading"),
 "total amerika": ("GROUP:AMERICA_SUBTOTAL", "America (subtotal)", "region_subtotal", ""),
 "other oceania": ("GROUP:OTHER_OCEANIA", "Other Oceania", "residual_group", ""),
 "oceania lainnya": ("GROUP:OTHER_OCEANIA", "Other Oceania", "residual_group", ""),
 "total oceania": ("GROUP:OCEANIA_SUBTOTAL", "Oceania (subtotal)", "region_subtotal", ""),
 "6. oseania/oceania": ("GROUP:OCEANIA_SUBTOTAL", "Oceania (subtotal)", "region_subtotal", "publication group heading"),
 "total oseania": ("GROUP:OCEANIA_SUBTOTAL", "Oceania (subtotal)", "region_subtotal", ""),
 "other africa": ("GROUP:OTHER_AFRICA", "Other Africa", "residual_group", ""),
 "afrika lainnya": ("GROUP:OTHER_AFRICA", "Other Africa", "residual_group", ""),
 "total africa": ("GROUP:AFRICA_SUBTOTAL", "Africa (subtotal)", "region_subtotal", ""),
 "7. afrika/africa": ("GROUP:AFRICA_SUBTOTAL", "Africa (subtotal)", "region_subtotal", "publication group heading"),
 "total afrika": ("GROUP:AFRICA_SUBTOTAL", "Africa (subtotal)", "region_subtotal", ""),
 "negara lainnya": ("GROUP:ALL_OTHER_COUNTRIES", "All other countries (residual, var 272/356/331)", "residual_group", "residual of the 36 named rows; composition not stated in the API"),
 "rata- rata": ("TOTAL:AVERAGE_OR_TOTAL", "All nationalities (average / total)", "total", "var 272/356: weighted average per visit; var 331: Jumlah = total USD million"),
 "jumlah": ("TOTAL:AVERAGE_OR_TOTAL", "All nationalities (average / total)", "total", ""),
 "jumlah/grand total": ("TOTAL:AVERAGE_OR_TOTAL", "All nationalities (average / total)", "total", ""),
 "grand total": ("TOTAL:AVERAGE_OR_TOTAL", "All nationalities (average / total)", "total", ""),
 "stateless": ("NONCOUNTRY:STATELESS", "Stateless", "non_country", "no country"),
 "uno": ("NONCOUNTRY:UNO", "UN laissez-passer (UNO)", "non_country", "no country"),
 "scotlandia": ("SUBNATIONAL:SCOTLAND", "Scotland", "sub_national", "part of GBR; may duplicate United Kingdom"),
 "wales": ("SUBNATIONAL:WALES", "Wales", "sub_national", "part of GBR; may duplicate United Kingdom"),
 "alaska": ("SUBNATIONAL:ALASKA", "Alaska", "sub_national", "part of USA; may duplicate United States"),
 "siberia": ("SUBNATIONAL:SIBERIA", "Siberia", "sub_national", "part of RUS; may duplicate Russia"),
 "yugoslavia": ("HISTORIC:YUGOSLAVIA", "Yugoslavia", "historic", "historic entity; no ISO3 in use"),
 "guiana": ("AMBIGUOUS:GUIANA", "Guiana (French Guiana?)", "ambiguous", "label ambiguous (French Guiana GUF?); not mapped"),
 "polynesia": ("AMBIGUOUS:POLYNESIA", "Polynesia (French Polynesia?)", "ambiguous", "label ambiguous (French Polynesia PYF?); not mapped"),
 "cabinda": ("SUBNATIONAL:CABINDA", "Cabinda", "sub_national", "exclave of Angola"),
 "maseru": ("NONCOUNTRY:MASERU", "Maseru", "non_country", "capital city of Lesotho used as a passport label"),
 "zomba": ("NONCOUNTRY:ZOMBA", "Zomba", "non_country", "city in Malawi used as a passport label"),
}

CMAP = {}
for line in C.strip().split("\n"):
    iso, name, vs = line.split("|")
    for v in vs.split(";"):
        CMAP[v.strip().lower()] = (iso, name)
NOTES = {"hellenic": "'Hellenic' read as Greece", "volta atas": "historic name of Burkina Faso (listed in the Europe block of var 1470)",
         "samoa barat": "historic name of Samoa", "samoa": "BPS 'Samoa'; could also be American Samoa - read as Samoa",
         "zaire": "historic name of DR Congo", "korea": "var 331 label 'Korea' read as South Korea (Korea Utara is a separate row in var 1470)",
         "kaledonia": "read as New Caledonia", "grenadines (grenada)": "read as Grenada", "sahara": "read as Western Sahara",
         "st. christopher": "same entity as St. Kitts & Nevis", "burkinabe": "same entity as Burkina Faso",
         "congo": "read as Republic of the Congo", "hongkong, rrt": "Hong Kong (RRT = special region of PRC)",
         "macao, rrt": "Macao (RRT = special region of PRC)"}


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", html.unescape(s))).strip()
    if re.fullmatch(r"(?:\S ){2,}\S", s):
        s = s.replace(" ", "")
    s = s.replace("�", "'").replace("’", "'")
    return re.sub(r"\s+", " ", s)


def classify(label):
    n = norm(label); low = n.lower().rstrip(". ").strip()
    cands = [low, n.lower()]
    # tokens: split on '/' and parentheses
    toks = [t.strip() for t in re.split(r"[/()]", low) if t.strip()]
    for c in cands:
        if c in G: return G[c]
    for c in cands:
        if c in CMAP: return (CMAP[c][0], CMAP[c][1], "country", NOTES.get(c, ""))
    for t in toks:
        if t in G: return G[t]
    # first token (Indonesian) first, then the rest
    for t in toks:
        if t in CMAP: return (CMAP[t][0], CMAP[t][1], "country", NOTES.get(t, ""))
    return ("UNMAPPED:" + n, n, "unmapped", "no rule; resolve manually")


def main():
    srcs = {}   # source -> list of (label, extra)
    V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_vervar_labels.json"), encoding="utf-8"))
    for var in ("272", "356", "331", "1470"):
        srcs["var" + var] = [(norm(x["label"]), "row_id=%s" % x["id"]) for x in V[var]]
    def pub_labels(path, edition, extra_filter=None):
        out, seen = [], set()
        for r in csv.DictReader(open(path, encoding="utf-8-sig")):
            if r["edition"] != str(edition): continue
            if extra_filter and not extra_filter(r): continue
            lab = norm(r["nationality"])
            if lab not in seen:
                seen.add(lab); out.append((lab, "p%s" % r["source_page_pdf"]))
        return out
    srcs["pub_spend_2025"] = pub_labels(os.path.join(EXTRACT, "bps_spend_per_visit_detail.csv"), 2025,
                                         lambda r: r["table_family"] == "spend_per_visit_quarterly_by_nationality")
    srcs["pub_arrivals_2025"] = pub_labels(os.path.join(EXTRACT, "bps_arrivals_by_nationality_pub.csv"), 2025)
    keyinfo, cells = {}, {}
    for s, items in srcs.items():
        for lab, extra in items:
            key, name, rtype, note = classify(lab)
            keyinfo.setdefault(key, [name, rtype, set()])
            if note: keyinfo[key][2].add(note)
            cells.setdefault(key, {}).setdefault(s, []).append(lab)
    order = ["var272", "var356", "var331", "var1470", "pub_spend_2025", "pub_arrivals_2025"]
    rows = []
    for key, (name, rtype, notes) in sorted(keyinfo.items(), key=lambda kv: (kv[1][1] != "country", kv[0])):
        iso = key if (rtype == "country") else ""
        r = [key, iso, name, rtype] + [" | ".join(cells[key].get(s, [])) for s in order]
        r.append("; ".join(sorted(notes)))
        # multiple distinct labels within one source -> flag
        dup = [s for s in order if len(cells[key].get(s, [])) > 1]
        if dup:
            r[-1] = (r[-1] + "; " if r[-1] else "") + "several labels map here in: " + ",".join(dup)
        rows.append(r)
    write_csv(os.path.join(EXTRACT, "bps_nationality_rows.csv"),
              ["canonical_key", "iso3", "canonical_name_en", "row_type", "var272_label", "var356_label", "var331_label",
               "var1470_label", "pub_spend_2025_label", "pub_arrivals_2025_label", "note"], rows)
    un = [r for r in rows if r[3] == "unmapped"]
    print("rows", len(rows), "unmapped", len(un))
    for r in un: print("  UNMAPPED:", r[0])
    print({s: len(v) for s, v in srcs.items()})


if __name__ == "__main__":
    main()
