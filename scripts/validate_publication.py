"""Validate the curated public notebook without accessing hardware or a network."""
import ipaddress
import json
from pathlib import Path
import re
import statistics
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
ALLOWED_SUFFIXES = {'.md', '.json', '.py', '.c', '.h', '.inc', ''}
ALLOWED_TEXT_FILES = {
    'prototypes/cmp-window/ce132/LICENSE.NVIDIA',
    'prototypes/cmp-window/ce132/nv-gpu-ops-window-hook.patch',
}
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
    app = load('cuda-application-transport.json')
    app_path = ROOT / 'data/cuda-application-transport.json'
    if app['native_CUDA_peer_capabilities'] != [False, False] or app['extra_usable_GiB'] or app['extra_SM']:
        error(app_path, 'explicit CE transport does not establish native peer capability or extra capacity')
    cuda = app['CUDA_buffers']
    if len(cuda['cases']) != 6 or sum(r['bytes'] for r in cuda['cases']) != cuda['payload_bytes']:
        error(app_path, 'expected six bounded CUDA data cases with consistent payload bytes')
    for row in cuda['cases']:
        if row['CPU_wrong_bytes'] or row['GPU_wrong_words'] or row['source_GPU_wrong_words'] or not row['source_unchanged'] or not row['peer_completed'] or row['cleanup_status'] or row['retained'] or row['expected_sha256'] != row['destination_sha256']:
            error(app_path, 'CUDA data, completion or cleanup verdict disagrees')
    if len(cuda['negative_GPU_controls']) != 2 or any(r['wrong_words'] != 1 or r['first_wrong_word'] != 17 for r in cuda['negative_GPU_controls']):
        error(app_path, 'both GPU verifiers must detect the deliberately changed word')
    pool = app['PyTorch_processes']
    if len(pool['cases']) != 4 or pool['process_exitcodes'] != [0, 0] or sum(r['bytes'] for r in pool['cases']) != pool['payload_bytes'] or any(not r['GPU_expected_equal'] or not r['guards_unchanged'] for r in pool['cases']):
        error(app_path, 'cross-process pool/view proof is incomplete')
    request_sets = []
    for row in app['application']['variants']:
        if row['status'] != 'completed' or len(row['sequential']) != 3 or len(row['parallel']) != 4:
            error(app_path, 'missing measured application requests')
        request_sets.append(tuple(r['request_sha256'] for r in row['sequential'] + row['parallel']))
        if abs(statistics.median(r['stream_decode_tps_estimate'] for r in row['sequential']) - row['median_sequential_decode_tps_estimate']) > 1e-8 or abs(sum(r['output_tokens'] for r in row['parallel']) / row['parallel_wall_s'] - row['parallel_four_response_tps']) > 1e-8:
            error(app_path, 'application speed summary is inconsistent')
        if row['CE'] and (not row['CE']['all_source_destination_hashes_match'] or row['native_CUDA_peer_support'] or row['CPU_payload_fallback']):
            error(app_path, 'direct activation proof and effective route disagree')
    if len(request_sets) != 3 or len(set(request_sets)) != 1:
        error(app_path, 'expected three matched application variants')
    if {r['name'] for r in app['application']['variants']} != {'pp2-ce-validated', 'pp2-shm-matched', 'pp2-ce-payload-only'}:
        error(app_path, 'unexpected explicit activation comparison variants')
    persistent = load('persistent-collective-transport.json')
    persistent_path = ROOT / 'data/persistent-collective-transport.json'
    if persistent['native_CUDA_peer_capabilities'] != [False, False] or any(persistent[k] for k in ['extra_usable_GiB', 'extra_SM', 'native_NCCL_backend', 'TP_model_run']):
        error(persistent_path, 'explicit collectives do not qualify native support, a TP model or extra capacity')
    backend = persistent['persistent_backend']
    run = backend['model']
    if run['native_contexts'] != 1 or run['context_uses'] != run['native_requests'] or run['one_time_context_creations'] != 1 or not run['all_activation_hashes_match'] or run['CPU_payload_fallback']:
        error(persistent_path, 'persistent application proof and actual context reuse disagree')
    if len(run['sequential']) != 3 or len(run['parallel']) != 4 or run['measured_requests'] != 7:
        error(persistent_path, 'missing persistent application requests')
    if abs(statistics.median(r['stream_decode_tps_estimate'] for r in run['sequential']) - run['median_sequential_decode_tps_estimate']) > 1e-8 or abs(sum(r['output_tokens'] for r in run['parallel']) / run['parallel_wall_s'] - run['parallel_total_tps']) > 1e-8 or abs(statistics.median(r['ttft_s'] for r in run['sequential']) - run['median_sequential_ttft_s']) > 1e-8:
        error(persistent_path, 'persistent speed arithmetic differs from request records')
    shm = next(r for r in app['application']['variants'] if r['name'] == 'pp2-shm-matched')
    if [r['request_sha256'] for r in run['sequential'] + run['parallel']] != [r['request_sha256'] for r in shm['sequential'] + shm['parallel']]:
        error(persistent_path, 'persistent comparison inputs differ from the matched SHM reference')
    coll = persistent['small_collectives']
    cases = coll['cases']
    if len(cases) != 20 or [r['sequence'] for r in cases] != list(range(1, 21)) or {r['dtype'] for r in cases} != {'int32', 'float32', 'bfloat16'}:
        error(persistent_path, 'incomplete independent two-rank collective coverage')
    if sum(r['operation'] == 'all-reduce-sum' for r in cases) != coll['all_reduce_sum'] or sum(r['operation'] == 'all-gather' for r in cases) != coll['all_gather'] or 2 * sum(r['input_bytes'] for r in cases) != coll['total_peer_payload_bytes']:
        error(persistent_path, 'collective operation or payload totals disagree')
    for row in cases:
        if row['rank0_output_sha256'] != row['rank1_output_sha256'] or any(not row[k] for k in ['full_GPU_expected_equal', 'input_unchanged', 'guards_unchanged']):
            error(persistent_path, 'collective result hashes or independent GPU/guard verdicts disagree')
    if not cases[0]['negative_checker_detected'] or coll['negative_result_checker_verdicts'] != 2 or coll['native_requests'] != coll['counter_delta']['payload_requests'] or coll['model_started'] or coll['native_transport_changed']:
        error(persistent_path, 'checker, real request counts or bounded collective scope disagree')
    final = persistent['final_state']
    if final['native_sessions_created'] != final['native_session_destroy_ok'] or final['native_channels_created'] != final['native_channel_destroy_calls'] or final['contexts_live'] or final['module_reference_count'] or not final['actual_idle_both_cards'] or final['selected_GPU_kernel_errors']:
        error(persistent_path, 'native close/idle claims are inconsistent')
    tp = load('tp-application-transport.json')
    tp_path = ROOT / 'data/tp-application-transport.json'
    if not tp['actual_direct_TP_model'] or tp['native_NCCL_backend'] or tp['native_CUDA_peer_capabilities'] != [False, False] or tp['extra_usable_GiB'] or tp['extra_SM']:
        error(tp_path, 'actual experimental TP data does not establish native support or extra capacity')
    if {k: tp['settings'][k] for k in ['TP', 'PP', 'max_num_batched_tokens', 'max_output_tokens']} != {'TP': 2, 'PP': 1, 'max_num_batched_tokens': 128, 'max_output_tokens': 32}:
        error(tp_path, 'short TP comparison configuration is inconsistent')
    proof = tp['model_proof']
    if sum(proof['operations'].values()) != proof['collective_pairs'] or 2 * proof['collective_pairs'] != proof['directed_input_tensors'] or proof['shared_result_hash_pairs'] != proof['collective_pairs'] or sum(tp['model_context_uses']) != proof['native_requests'] or proof['native_completions'] != proof['native_requests'] + proof['native_contexts']:
        error(tp_path, 'actual TP collective, transfer or native-completion totals disagree')
    if any(not proof[k] for k in ['passed', 'full_sender_receiver_hashes_match', 'all_shared_result_hashes_match', 'all_real_completions_and_lifecycle_checks_pass']) or proof['CPU_activation_payload_fallback'] or proof['root_gather_contracts'] or tp['actual_model_uses_root_gather']:
        error(tp_path, 'actual TP proof and precisely exercised operations disagree')
    extension = tp['prerequisite_extension']
    if len(extension['cases']) != 12 or sum(c['full_GPU_expected_result_verdicts'] for c in extension['cases']) != 18:
        error(tp_path, 'missing independent extended GPU qualification')
    for case in extension['cases']:
        if not case['inputs_and_guards_unchanged']:
            error(tp_path, 'extended input or guard verdict failed')
        if case['operation'] == 'gather-root':
            root = case['root']
            if case[f'rank{root}_result_is_none'] or not case[f'rank{root}_output_sha256'] or not case[f'rank{1-root}_result_is_none'] or case[f'rank{1-root}_output_sha256'] is not None:
                error(tp_path, 'root gather returned data/None to the wrong rank')
        elif case['rank0_output_sha256'] != case['rank1_output_sha256']:
            error(tp_path, 'shared extended-result hashes disagree')
    if proof['maximum_input_bytes_per_rank'] > extension['maximum_input_bytes_per_rank'] or not extension['cases'][0]['negative_result_checker_detected_on_both']:
        error(tp_path, 'actual TP range or result-checker scope exceeds qualification')
    tp_sets = []
    for run in tp['variants']:
        if len(run['sequential']) != 3 or len(run['parallel']) != 4 or any(not 0 < row['output_tokens'] <= 32 for row in run['sequential'] + run['parallel']):
            error(tp_path, 'missing or out-of-scope short TP requests')
        tp_sets.append([r['request_sha256'] for r in run['sequential'] + run['parallel']])
        if abs(statistics.median(r['stream_decode_tps_estimate'] for r in run['sequential']) - run['median_sequential_decode_tps_estimate']) > 1e-8 or abs(sum(r['output_tokens'] for r in run['parallel']) / run['parallel_wall_s'] - run['parallel_total_tps']) > 1e-8:
            error(tp_path, 'short TP speed arithmetic differs from request records')
    if len(tp_sets) != 2 or tp_sets[0] != tp_sets[1] or {r['route'] for r in tp['variants']} != {'explicit_application_CE_TP', 'native_NCCL_SHM'}:
        error(tp_path, 'matching short TP comparison inputs/routes disagree')
    final_tp = tp['final_state']
    if final_tp['native_sessions_created'] != final_tp['native_session_destroy_ok'] or final_tp['native_channels_created'] != final_tp['native_channel_destroy_calls'] or final_tp['contexts_live'] or final_tp['module_reference_count'] or not final_tp['actual_idle_both_cards'] or final_tp['selected_GPU_kernel_errors']:
        error(tp_path, 'actual TP native cleanup and idle claims disagree')
    model_runs = load('model-parallel-trials.json')
    model_path = ROOT / 'data/model-parallel-trials.json'
    variants = model_runs['variants']
    if {r['name'] for r in variants} != {'tp2-auto', 'tp2-no-p2p', 'pp2-auto', 'pp2-no-p2p', 'single64'} or len(variants) != 5:
        error(model_path, 'expected five distinct model variants')
    if model_runs['actual_P2P_model_speed_measured'] or model_runs['native_window_CE_hook_used_by_models']:
        error(model_path, 'SHM runs do not demonstrate the direct CE-window application route')
    request_sets = []
    count = 0
    for row in variants:
        if row['model_status'] != 'completed' or row['actual_P2P'] or row['actual_transport'] != ('single_gpu' if row['name'] == 'single64' else 'NCCL_SHM'):
            error(model_path, 'model success and effective transport disagree')
        if len(row['sequential']) != 3 or len(row['parallel']) != 4:
            error(model_path, 'missing measured requests')
        request_sets.append(tuple(r['request_sha256'] for r in row['sequential']))
        count += len(row['sequential']) + len(row['parallel'])
        median = statistics.median(r['stream_decode_tps_estimate'] for r in row['sequential'])
        aggregate = sum(r['output_tokens'] for r in row['parallel']) / row['parallel_wall_s']
        if abs(median - row['median_sequential_decode_tps_estimate']) > 1e-8 or abs(aggregate - row['parallel_four_total_response_tps']) > 1e-8:
            error(model_path, 'published speed arithmetic differs from request records')
    if count != model_runs['responses_generated'] or len(set(request_sets)) != 1:
        error(model_path, 'request count or identical-input comparison disagrees')

    windows = load('window-ce-trials.json')
    window_path = ROOT / 'data/window-ce-trials.json'
    if {(r['owner'], r['accessor']) for r in windows['directions']} != {('CMP40', 'CMP64'), ('CMP64', 'CMP40')}:
        error(window_path, 'expected the two actual directed CE trials')
    for row in windows['directions']:
        if row['peer_copy_bytes'] != 1048576 or row['local_control_bytes'] != 65536:
            error(window_path, 'trial size differs from qualified bounded scope')
        if len(row['completions']) != 2 or any(not c['GPU_completion_observed'] or not c['fresh_payload_matches'] or c['channel_error'] for c in row['completions']):
            error(window_path, 'missing independent GPU completion')
        checks = {c['label']: c for c in row['checks']}
        for label in ['owner_before', 'peer_destination', 'owner_after']:
            if checks[label]['words'] != 262144 or checks[label]['wrong_words']:
                error(window_path, 'incomplete or failed full peer-data comparison')
        if row['lease_release']['status'] or row['lease_release']['retained'] or row['session_destroy_status'] or row['test_module_unload_status']:
            error(window_path, 'recorded cleanup is not complete')
    if windows['extra_usable_GiB'] or windows['extra_SM'] or not all(windows['unresolved'].values()):
        error(window_path, 'small CE copies do not qualify broader results')
    import hashlib
    for source in windows['published_sources']:
        content = (ROOT / source['path']).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(content).hexdigest() != source['sha256']:
            error(window_path, 'published source hash differs: ' + source['path'])

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
        if path.suffix not in ALLOWED_SUFFIXES and path.name != '.gitignore' and path.relative_to(ROOT).as_posix() not in ALLOWED_TEXT_FILES:
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
