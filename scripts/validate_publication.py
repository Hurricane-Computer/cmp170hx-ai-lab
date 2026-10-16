"""Validate the curated public notebook without accessing hardware or a network."""
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
ALLOWED_SUFFIXES = {'.md', '.json', '.py', ''}
BLOCKED = {
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'credential token': r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|sk-[A-Za-z0-9_-]{25,})\b',
    'authorization header': r'(?i)authorization\s*[:=]\s*["\x27]?(?:bearer|basic)\s+\S+',
    'private Windows path': r'(?i)[A-Z]:[\\/](?:Users|Documents and Settings)[\\/][^\s"\x27]+',
    'private home path': r'/(?:home|Users)/[A-Za-z0-9_.-]+/',
    'GPU UUID': r'\bGPU-[0-9a-fA-F]{8}-[0-9a-fA-F-]{20,}\b',
    'internal machine identity': r'\bHC-(?:PM|KI|HV|AS|HC)[0-9]{2}\b',
}


def error(path, reason):
    ERRORS.append(f'{path.relative_to(ROOT)}: {reason}')


def load(name):
    path = ROOT / 'data' / name
    value = json.loads(path.read_text(encoding='utf8'))
    if value.get('schema_version') != 1:
        error(path, 'unsupported or missing schema_version')
    return value


def check_text(path, text):
    for label, pattern in BLOCKED.items():
        if re.search(pattern, text):
            error(path, label)
    for token in re.findall(r'(?<![\w])(?:\d{1,3}\.){3}\d{1,3}(?![\w])', text):
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue  # For example, a dotted VBIOS version with leading zeroes.
        if address.is_private or address.is_loopback or address.is_link_local:
            error(path, 'private or local network address')
    if path.suffix != '.md':
        return
    for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)', text):
        target = target.strip().split(' ', 1)[0].strip('<>')
        if target.startswith(('https://', 'http://', '#', 'mailto:')):
            continue
        target = unquote(target.split('#', 1)[0])
        if not target:
            continue
        dest = (path.parent / target).resolve()
        if not dest.is_relative_to(ROOT):
            error(path, 'local link escapes the public repository')
        elif not dest.exists():
            error(path, 'broken local documentation link: ' + target)


def check_data():
    cards = load('cards.json')['cards']
    variants = {v['variant'] for v in cards}
    if variants != {'cmp40', 'cmp64'}:
        error(ROOT / 'data/cards.json', 'expected the two documented variants')
    for card in cards:
        if card['full_capacity_qualified_in_this_campaign'] is not None:
            error(ROOT / 'data/cards.json', 'full-capacity status needs its own published qualification record')
        if card['established_sm_baseline']['evidence_level'] != 'owner-established':
            error(ROOT / 'data/cards.json', 'baseline provenance must stay explicit')
        if not card['memory_clock'].get('evidence_utc') or not card['memory_clock'].get('kind'):
            error(ROOT / 'data/cards.json', 'clock observation needs time and kind')

    clocks = load('clock-trials.json')
    for record in clocks['records']:
        coefficient = int(record['scratch13_coefficient'], 16)
        clock = record['operating_memory_clock_mhz']
        if coefficient & ~0xff00 != 0x10001 or ((coefficient >> 8) & 0xff) * 27 != clock:
            error(ROOT / 'data/clock-trials.json', 'coefficient and observed clock disagree')
        check = record['short_check']
        if (not re.fullmatch(r'[0-9a-f]{64}', check['source_sha256'])
                or check['source_sha256'] != check['returned_sha256']
                or not check['full_returned_data_hash_matches']):
            error(ROOT / 'data/clock-trials.json', 'copy verification and published hashes disagree')
        if any(record[field] for field in ['full_vram_integrity_qualified', 'long_term_stability_proven',
                                           'bandwidth_gain_measured', 'llm_throughput_gain_measured',
                                           'maximum_clock_determined']):
            error(ROOT / 'data/clock-trials.json', 'a short copy does not support broader qualification')
    latest_clock = max(clocks['records'], key=lambda row: row['evidence_utc'])
    cmp40 = next(card for card in cards if card['variant'] == 'cmp40')
    if (cmp40['memory_clock']['mhz'] != latest_clock['operating_memory_clock_mhz']
            or cmp40['memory_clock']['evidence_utc'] != latest_clock['evidence_utc']):
        error(ROOT / 'data/cards.json', 'latest clock and curated trial record disagree')

    tpc = load('tpc-sources.json')
    for card in tpc['cards']:
        for name, rows in card['vectors'].items():
            if [v['gpc'] for v in rows] != list(range(8)):
                error(ROOT / 'data/tpc-sources.json', 'incomplete or duplicate vector: ' + name)
            for row in rows:
                int(row['address'], 16)
                int(row['value'], 16)
    if tpc['register_writes'] != 0 or tpc['register_reads'] != 2 * (4 * 8 + 1):
        error(ROOT / 'data/tpc-sources.json', 'read-only snapshot operation counts disagree')

    catalog = load('firmware-catalog.json')
    for image in catalog['images']:
        if not re.fullmatch(r'[0-9a-f]{64}', image['rom_sha256']):
            error(ROOT / 'data/firmware-catalog.json', 'invalid input hash')
        table = image['partition_table']
        raw = bytes.fromhex(table['table_hex'])
        length = table['header_size'] + table['record_size'] * table['record_count']
        if len(raw) != length:
            error(ROOT / 'data/firmware-catalog.json', 'partition table includes missing or neighbouring bytes')
        if len(image['geometry_profiles']) != 16:
            error(ROOT / 'data/firmware-catalog.json', 'incomplete original profile catalog')

    witness = load('cp-witness.json')
    for card in witness['cards']:
        if card['effective_topology_changed']:
            error(ROOT / 'data/cp-witness.json', 'record contradicts the documented negative result')
        for address, requested in card['requested_nonzero_witness'].items():
            if int(requested, 16) == 0 or int(card['after'][address], 16) != 0:
                error(ROOT / 'data/cp-witness.json', 'nonzero rejected-witness description disagrees with readback')

    ledger = load('experiment-ledger.json')
    ids = [v['id'] for v in ledger['records']]
    if len(ids) != len(set(ids)):
        error(ROOT / 'data/experiment-ledger.json', 'duplicate experiment ID')
    for record in ledger['records']:
        if record['evidence_level'] not in {'observed', 'static-analysis', 'owner-established', 'theoretical', 'third-party', 'hypothesis'}:
            error(ROOT / 'data/experiment-ledger.json', 'unknown evidence level')
        if not (ROOT / record['interpretation']).is_file():
            error(ROOT / 'data/experiment-ledger.json', 'missing interpretation')


def main():
    files = []
    for path in sorted(ROOT.rglob('*')):
        if '.git' in path.parts or '__pycache__' in path.parts:
            continue
        if path.is_symlink():
            error(path, 'symlinks are not part of the curated publication')
        if not path.is_file():
            continue
        files.append(path)
        if path.suffix not in ALLOWED_SUFFIXES and path.name != '.gitignore':
            error(path, 'unexpected publication file type')
            continue
        if path.stat().st_size > 1_000_000:
            error(path, 'unexpectedly large publication file')
        try:
            text = path.read_text(encoding='utf8')
            check_text(path, text)
            if path.suffix == '.json':
                json.loads(text)
        except (UnicodeError, ValueError) as exc:
            error(path, 'not valid UTF-8 text/JSON: ' + str(exc))
    try:
        check_data()
    except (ValueError, KeyError, TypeError) as exc:
        ERRORS.append('data contract: ' + str(exc))
    if ERRORS:
        print('\n'.join(ERRORS))
        return 1
    print(f'Publication check passed: {len(files)} text files; data contracts and local links consistent; no flagged disclosures.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
