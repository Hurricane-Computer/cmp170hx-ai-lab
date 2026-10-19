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
    poll = load('completion-poll-transport.json')
    poll_path = ROOT / 'data/completion-poll-transport.json'
    if poll['native_NCCL_backend'] or poll['native_CUDA_peer_capabilities'] != [False, False] or poll['extra_usable_GiB'] or poll['extra_SM']:
        error(poll_path, 'bounded waiting does not establish native peer capability or added hardware')
    policy = poll['wait_policy']
    if policy['maximum_busy_delays_per_copy'] != 50 or policy['busy_delay_us'] != 1 or policy['fallback_sleep_us'] != [500, 1000] or policy['timeout_ms'] != 3000 or policy['hard_50us_wall_bound_claimed']:
        error(poll_path, 'iteration, fallback, timeout or elapsed-time claim disagrees with scope')
    for field in ['actual_fresh_semaphore_and_FIFO_retirement_required', 'native_errors_and_backing_lifetime_preserved', 'need_resched_enters_sleep_fallback', 'full_CPU_validation_preserved']:
        if not policy[field]:
            error(poll_path, 'required completion/lifetime/validation contract is missing: ' + field)
    qual = poll['tensor_qualification']
    if not qual['passed'] or len(qual['cases']) != qual['directed_tensors'] or sum(c['bytes'] for c in qual['cases']) != qual['payload_bytes'] or qual['independent_GPU_data_verdicts'] != 2 * qual['directed_tensors'] or qual['outside_view_guard_verdicts'] != 2 * qual['directed_tensors']:
        error(poll_path, 'independent data/guard proof totals disagree')
    if any(not c['full_GPU_expected_equal_both'] or not c['outside_view_guards_unchanged_both'] or c['source_view_offset'] == c['destination_view_offset'] for c in qual['cases']) or {c['source'] for c in qual['cases']} != {'CMP40', 'CMP64'}:
        error(poll_path, 'both-direction random data/offset qualification is incomplete')
    proof = poll['model_proof']
    if any(not proof[k] for k in ['passed', 'full_sender_receiver_hashes_match', 'all_shared_result_hashes_match', 'all_real_completions_and_lifecycle_checks_pass']) or proof['CPU_activation_payload_fallback']:
        error(poll_path, 'bounded-poll model lacks full input/result/lifetime proof')
    if sum(proof['operations'].values()) != proof['collective_pairs'] or proof['shared_result_hash_pairs'] != proof['collective_pairs'] or proof['directed_input_tensors'] != 2 * proof['collective_pairs'] or sum(poll['model_context_uses']) != proof['native_requests'] or proof['native_completions'] != proof['native_requests'] + proof['native_contexts']:
        error(poll_path, 'bounded-poll model operation/context/completion totals disagree')
    if poll['model_counter_delta']['payload_requests'] != proof['native_requests']:
        error(poll_path, 'model trace and real native request counter disagree')
    for counters, completions in [(qual['poll_counter_delta'], qual['real_completions']), (poll['model_counter_delta'], proof['native_completions'])]:
        if counters['retire_early'] + counters['retire_after_sleep'] != completions or not 0 <= counters['busy_delay_calls'] <= 50 * completions or not 0 <= counters['early_poll_checks'] <= 51 * completions or counters['sleep_calls'] < counters['retire_after_sleep']:
            error(poll_path, 'real-retirement classification or bounded polling arithmetic disagrees')
    if abs(poll['model_counter_delta']['retire_early'] / proof['native_completions'] - poll['early_retirement_fraction']) > 1e-12:
        error(poll_path, 'early-retirement fraction differs from actual observations')
    reuse = poll['reference_reuse']
    if reuse['unchanged_SHM_replayed'] or any(not reuse[k] for k in ['actual_commands_equal_ignoring_only_loopback_port', 'matching_runtime_sources_model_core_boot_and_memory_clocks', 'matching_measured_request_hashes']):
        error(poll_path, 'matching earlier-reference qualification is incomplete')
    poll_sets = []
    for run in poll['variants']:
        if run['status'] != 'completed' or len(run['sequential']) != 3 or len(run['parallel']) != 4 or any(not 0 < row['output_tokens'] <= 32 for row in run['sequential'] + run['parallel']):
            error(poll_path, 'missing bounded TP speed requests')
        poll_sets.append([row['request_sha256'] for row in run['sequential'] + run['parallel']])
        if abs(statistics.median(row['stream_decode_tps_estimate'] for row in run['sequential']) - run['median_sequential_decode_tps_estimate']) > 1e-8 or abs(sum(row['output_tokens'] for row in run['parallel']) / run['parallel_wall_s'] - run['parallel_total_tps']) > 1e-8:
            error(poll_path, 'bounded-poll speed arithmetic differs from selected request data')
    if len(poll_sets) != 3 or any(rows != poll_sets[0] for rows in poll_sets) or sum(r['new_measurement_in_this_package'] for r in poll['variants']) != 1:
        error(poll_path, 'expected exactly one new variant and two matching retained references')
    final_poll = poll['final_state']
    if final_poll['native_sessions_created'] != final_poll['native_session_destroy_ok'] or final_poll['native_channels_created'] != final_poll['native_channel_destroy_calls'] or final_poll['contexts_live'] or final_poll['module_reference_count'] or not final_poll['actual_idle_both_cards'] or final_poll['selected_GPU_kernel_errors']:
        error(poll_path, 'bounded-poll close/idle claims disagree')
    profile = load('transport-cost-profile.json')
    profile_path = ROOT / 'data/transport-cost-profile.json'
    if profile['native_changes'] or profile['native_NCCL_backend'] or profile['native_CUDA_peer_capabilities'] != [False, False] or profile['extra_usable_GiB'] or profile['extra_SM']:
        error(profile_path, 'host profiling does not change native capability or hardware')
    if profile['source_pins']['unchanged_consumer_sha256'] != poll['source_pins']['consumer_module_sha256'] or profile['source_pins']['unchanged_core_sha256'] != poll['source_pins']['unchanged_core_sha256']:
        error(profile_path, 'unchanged native backend claim differs from preserved data')
    offline = profile['offline_verifier']
    if not offline['passed'] or not offline['local_only'] or offline['GPU_access'] or offline['negative_corrupt_trees_detected'] != 3:
        error(profile_path, 'offline timing-tree verifier qualification is incomplete')
    pilot = profile['pilot']
    if pilot['TP'] != 2 or pilot['PP'] != 1 or pilot['output_token_cap'] != 8 or not 0 < pilot['actual_output_tokens'] <= 8 or pilot['measured_speed_benchmark_requests'] or pilot['formal_quality_equivalence']:
        error(profile_path, 'diagnostic pilot scope became a speed/quality claim')
    proof = profile['model_proof']
    phases = profile['profile_verdict']
    if not proof['passed'] or proof['CPU_activation_payload_fallback'] or any(not proof[k] for k in ['full_sender_receiver_hashes_match', 'all_shared_result_hashes_match', 'all_real_completions_and_lifecycle_checks_pass']):
        error(profile_path, 'actual diagnostic model data proof is incomplete')
    if sum(proof['operations'].values()) != proof['collective_pairs'] or proof['shared_result_hash_pairs'] != proof['collective_pairs'] or proof['directed_input_tensors'] != 2 * proof['collective_pairs'] or phases['profile_roots'] != proof['rank_operation_verdicts'] or phases['profile_roots'] != 2 * proof['collective_pairs']:
        error(profile_path, 'profile roots and full model data operations disagree')
    if phases['maximum_nodes_per_root'] > phases['configured_maximum_nodes_per_root'] or phases['full_hash_calls_per_rank_operation'] != 8 or any(not phases[k] for k in ['passed', 'all_roots_match_actual_data_events', 'all_intervals_nested_and_nonoverlapping', 'all_exclusive_sums_equal_local_roots', 'native_calls_match_real_requests']):
        error(profile_path, 'bounded profile coverage or exclusive-span verdict is incomplete')
    for group in profile['small_sum_groups']:
        total = group['inclusive_total_ns']
        if sum(p['exclusive_total_ns'] for p in group['exclusive_phases']) != total or group['full_hash_calls'] != 8 * group['root_count']:
            error(profile_path, 'exclusive phase sum or preserved full hash count disagrees')
        if any(abs(p['share'] - p['exclusive_total_ns'] / total) > 1e-12 for p in group['exclusive_phases']):
            error(profile_path, 'phase share differs from actual aggregate exclusive data')
        receives = [p for p in profile['IPC_receive_paths'] if p['rank'] == group['rank']]
        recv_phase = next(p for p in group['exclusive_phases'] if p['phase'] == 'ipc.recv')
        if sum(p['calls'] for p in receives) != 7 * group['root_count'] or sum(p['exclusive_total_ns'] for p in receives) != recv_phase['exclusive_total_ns']:
            error(profile_path, 'receive-path decomposition differs from local phase totals')
    if not profile['instrumentation_cost']['no_inference_speed_comparison'] or not profile['instrumentation_cost']['final_row_per_process_excluded'] or profile['clock']['nanosecond_accuracy_claimed']:
        error(profile_path, 'instrumentation/clock precision limits must remain explicit')
    final_profile = profile['final_state']
    if final_profile['cumulative_consumer_sessions_created'] != final_profile['cumulative_consumer_session_destroy_ok'] or final_profile['cumulative_consumer_channel_creates'] != final_profile['cumulative_consumer_channel_destroy_calls'] or final_profile['contexts_live'] or final_profile['module_reference_count'] or not final_profile['actual_idle_both_cards'] or final_profile['selected_GPU_kernel_errors']:
        error(profile_path, 'profile native-close/idle claims disagree')
    if profile['next_hypothesis']['implemented'] or profile['next_hypothesis']['measured_speed_gain']:
        error(profile_path, 'unimplemented descriptor batching must remain a hypothesis')
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


def check_batched_transport():
    d = load('batched-collective-transport.json')
    path = ROOT / 'data/batched-collective-transport.json'
    if d['native_CUDA_peer_capabilities'] != [False, False] or d['native_NCCL_backend'] or d['native_changes']:
        error(path, 'batched application observation misstates unchanged native capability')
    b = d['bounds']
    if (b['input_bytes_per_rank'], b['export_bytes'], b['windows_per_buffer']) != (3 * 2**20, 2**20, 4):
        error(path, 'batched window bounds changed without separate qualification')
    if b['local_export_FDs_per_rank'] * 2 != b['original_export_objects'] or b['original_export_objects'] + b['additional_received_FDs_on_coordinator'] != b['total_userspace_FD_references'] or b['total_userspace_FD_references'] != 24:
        error(path, 'original exports and received FD references are conflated')
    protocol = d['protocol']
    if protocol['native_coordinator_rank'] != 0 or protocol['native_device_FDs'] != 1 or not protocol['both_directions_serial'] or not protocol['full_CPU_validation_preserved'] or protocol['registration_cache'] or protocol['GPU_digest_substitution'] or protocol['CPU_activation_payload_fallback']:
        error(path, 'batched protocol scope/verification changed')
    q = d['qualification']
    if (q['full_independent_GPU_comparisons'], q['source_and_guard_verdicts'], q['intentional_result_errors_detected'], q['non_root_None_contracts']) != (64, 70, 4, 6):
        error(path, 'batched independent result/guard qualification count disagrees')
    packages = [q[k] for k in ['raw', 'extended_collectives', 'extra_int32_BF16']]
    if sum(x['native_requests'] for x in packages) != 68 or sum(x['real_completions'] for x in packages) != 74:
        error(path, 'batched qualification requests/real completions disagree')
    if any(x['max_export_objects'] > 16 or x['max_userspace_FD_references'] > 24 or x['channel_closes'] != 2 or not x['full_sender_receiver_hashes_match'] for x in packages):
        error(path, 'batched qualification bounds/full verification/close disagrees')
    p = d['model_proof']
    if p['collective_pairs'] != sum(p['operations'].values()) or p['collective_pairs'] != p['shared_result_hash_pairs'] or p['directed_input_tensors'] != 2 * p['collective_pairs']:
        error(path, 'batched model pair/input/result counts disagree')
    if (p['native_requests'], p['native_completions'], p['native_contexts'], p['uses_per_context']) != (37180, 37182, 2, [18590, 18590]):
        error(path, 'batched model native request/retirement/lifecycle counts disagree')
    if p['maximum_input_bytes_per_rank'] > b['input_bytes_per_rank'] or not all(p[k] for k in ['full_sender_receiver_hashes_match', 'all_shared_result_hashes_match', 'all_real_completions_and_lifecycle_checks_pass']):
        error(path, 'batched model full data/retirement proof missing')
    pilot = d['pilot']
    if not 0 < pilot['actual_output_tokens'] <= pilot['output_token_cap'] == 8 or not pilot['full_TP_input_result_audit_before_measurement']:
        error(path, 'batched pilot cap and actual tokens conflated')
    compare = d['comparison']
    if compare['unchanged_SHM_replayed'] or not compare['actual_runtime_config_core_boot_clocks_requests_match'] or (compare['measured_sequential_requests'], compare['measured_concurrent_requests']) != (3, 4):
        error(path, 'batched short matched comparison scope disagrees')
    for row in compare['answer_hash_matches']:
        if not 0 <= row['matches'] <= row['requests'] == 7:
            error(path, 'batched answer hash count invalid')
    cleanup = d['cleanup']
    if cleanup['live_contexts'] or cleanup['module_references'] or not cleanup['actual_GPUs_idle'] or cleanup['additional_successful_native_session_closes'] != 8:
        error(path, 'batched actual cleanup missing')
    if d['next_candidate']['evidence_level'] != 'hypothesis' or d['next_candidate']['implemented'] or d['next_candidate']['logging_cost_measured']:
        error(path, 'unimplemented native-log hypothesis presented as measured work')


def check_native_log_transport():
    d = load('native-log-transport.json')
    path = ROOT / 'data/native-log-transport.json'
    if d['native_CUDA_peer_capabilities'] != [False, False] or d['native_NCCL_backend'] or d['native_data_operations_changed'] or not d['native_logging_changed']:
        error(path, 'quiet logging record misstates native data/capability scope')
    logs = d['logging_change']
    if logs['guarded_success_call_sites'] != ['lease', 'import_pin', 'import_dup', 'local_pages', 'finish'] or logs['total_info_call_sites'] != 11 or logs['unconditional_info_call_sites'] != 6:
        error(path, 'quiet logging sites differ from the qualified scope')
    option = logs['success_option']
    if option['default'] or option['observed'] or option['runtime_write_allowed'] or option['sysfs_mode'] != '0400':
        error(path, 'quiet logging option is not the qualified read-only state')
    if not logs['completion_record_and_extra_MMIO_argument_unchanged'] or not logs['native_original_text_restored_after_namespace_and_logging_erasure'] or logs['exact_user_data_files_restored_after_native_namespace_mapping'] != 10:
        error(path, 'quiet logging source/MMIO preservation evidence missing')
    cpu = d['CPU_predicate_fixture']
    if (cpu['quiet_success_cases'], cpu['verbose_success_cases'], cpu['failure_metadata_cases_visible']) != (5, 5, 36) or cpu['GPU_faults_injected']:
        error(path, 'CPU log-predicate controls misrepresented')
    q = d['qualification']
    if (q['full_independent_GPU_comparisons'], q['source_and_guard_verdicts'], q['intentional_result_errors_detected'], q['non_root_None_contracts'], q['native_requests'], q['real_completions'], q['successful_native_context_closes']) != (64, 70, 4, 6, 68, 74, 6):
        error(path, 'quiet consumer independent data/guard/close counts disagree')
    p = d['model_proof']
    if p['collective_pairs'] != sum(p['operations'].values()) or p['shared_result_hash_pairs'] != p['collective_pairs'] or p['directed_input_tensors'] != 2 * p['collective_pairs']:
        error(path, 'quiet consumer model pair/input/hash counts disagree')
    if (p['native_requests'], p['native_completions'], p['native_contexts'], p['uses_per_context']) != (37180, 37182, 2, [18590, 18590]):
        error(path, 'quiet consumer actual native lifetime counts disagree')
    if not p['full_CPU_verification_and_guards_preserved'] or p['registration_cache'] or p['GPU_digest_substitution'] or p['activation_CPU_payload_fallback']:
        error(path, 'quiet consumer verification/fallback scope changed')
    if not 0 < d['pilot']['actual_output_tokens'] <= d['pilot']['output_token_cap'] == 8 or not d['pilot']['full_TP_audit_before_measurement']:
        error(path, 'quiet consumer pilot cap/actual/proof disagree')
    compare = d['comparison']
    if compare['material_gain_established'] or compare['logging_bottleneck_proven'] or compare['unchanged_SHM_or_previous_batched_replayed'] or not compare['actual_runtime_config_core_boot_clocks_requests_match']:
        error(path, 'single narrow negative result overstated or mismatched')
    previous = next(x for x in compare['earlier_variants'] if x['name'] == 'tp2-ce-batch-b128-o32')
    ratio = compare['new_variant']['median_sequential_decode_tps_estimate'] / previous['median_sequential_decode_tps_estimate']
    if abs(ratio - compare['decode_ratio_to_previous_batched']) > 1e-10:
        error(path, 'quiet consumer descriptive decode ratio disagrees')
    counts = d['selected_journal']['counts']
    if counts['completion'] != p['native_completions'] + q['real_completions'] or any(counts[k] for k in counts if k.startswith('guarded_')) or not d['selected_journal']['log_counts_are_not_hardware_completion_verdicts']:
        error(path, 'quiet consumer selected diagnostic-log counts/scope disagree')
    cleanup = d['cleanup']
    if cleanup['successful_native_session_closes'] != 8 or cleanup['live_contexts'] or cleanup['module_references'] or not cleanup['actual_GPUs_idle'] or cleanup['previous_consumer_requests_unchanged'] != 77338:
        error(path, 'quiet consumer actual close/old-consumer preservation missing')
    if d['next_candidate']['implemented'] or d['next_candidate']['new_speed_claim_planned'] or d['next_candidate']['evidence_level'] != 'hypothesis':
        error(path, 'unimplemented native timing diagnostic overstated')


def check_native_cost_profile():
    d = load('native-cost-profile.json')
    path = ROOT / 'data/native-cost-profile.json'
    if d['native_CUDA_peer_capabilities'] != [False, False] or d['native_NCCL_backend'] or d['new_inference_speed_claim'] or d['native_data_operations_changed'] or d['native_logging_policy_changed']:
        error(path, 'native diagnostic overstates data/capability/performance changes')
    ins = d['instrumentation']
    if ins['timer'] != 'ktime_get_raw_ts64' or ins['clock'] != 'CLOCK_MONOTONIC_RAW' or ins['actual_timer_export'] != 'EXPORT_SYMBOL' or ins['timing_values_used_as_completion']:
        error(path, 'timer compatibility or completion scope disagrees')
    if (ins['groups'], ins['phases_including_root_per_group'], ins['count_and_ns_entries_each']) != (4, 15, 60) or not ins['only_disjoint_top_level_children'] or not ins['snapshot_only_quiescent'] or ins['read_only_parameter_mode'] != '0400':
        error(path, 'native aggregate bounds/accounting/readonly scope disagrees')
    q = d['qualification']
    if (q['full_independent_GPU_comparisons'], q['source_and_guard_verdicts'], q['intentional_result_errors_detected'], q['non_root_None_contracts'], q['native_requests'], q['real_completions'], q['successful_context_closes']) != (64, 70, 4, 6, 68, 74, 6):
        error(path, 'native timing independent qualification count disagrees')
    if q['payload_profile_completions'] + q['local_qualifications_excluded_from_phase_counters'] != q['real_completions']:
        error(path, 'local qualification silently mixed with payload timing')
    p = d['model_proof']
    if p['collective_pairs'] != sum(p['operations'].values()) or p['shared_result_hash_pairs'] != p['collective_pairs'] or p['directed_input_tensors'] != 2 * p['collective_pairs']:
        error(path, 'native timing model input/result pair counts disagree')
    if (p['collective_pairs'], p['native_requests'], p['native_completions'], p['uses_per_context']) != (1301, 2862, 2864, [1431, 1431]) or not p['full_CPU_input_incoming_result_hashes_and_guards_preserved'] or p['registration_cache'] or p['GPU_digest_substitution']:
        error(path, 'native timing actual pilot proof or unchanged verification disagrees')
    pilot = d['pilot']
    if not 0 < pilot['actual_output_tokens'] <= d['model_settings']['pilot_output_token_cap'] == 8 or not pilot['normal_stop'] or d['model_settings']['measured_speed_requests'] != 0:
        error(path, 'diagnostic pilot cap/actual/speed scope disagrees')
    profile = d['model_profile']
    if profile['accounting_errors'] or profile['payload_errors'] or profile['unprofiled_errors'] or profile['damaged_aggregate_copies_rejected'] != 5:
        error(path, 'native timing accounting/error controls missing')
    if sum(x['requests'] for x in profile['groups']) != p['native_requests'] or profile['payload_completions'] + profile['setup_qualifications_excluded'] != p['native_completions']:
        error(path, 'native timing counters do not match actual trace replies')
    for group in profile['groups']:
        phases = group['phases']
        if len(phases) != 14 or len({x['name'] for x in phases}) != 14 or group['total_root_ns'] != sum(x['total_ns'] for x in phases) + group['remainder_ns']:
            error(path, 'disjoint native phases/root/remainder do not reconcile')
        for phase in phases:
            expected = group['payload_completions'] if phase['name'] == 'CE_build_submit_retire_and_diagnostic' else group['requests']
            if phase['calls'] != expected or phase['total_ns'] < 0 or abs(phase['mean_ns'] - phase['total_ns'] / expected) > 1e-6 or abs(phase['share_of_root'] - phase['total_ns'] / group['total_root_ns']) > 1e-12:
                error(path, 'native phase count, units or normalized share disagrees')
    cache = d['cache_source_analysis']
    if cache['evidence_level'] != 'static-analysis' or not cache['allocation_argument_not_a_range_flush'] or cache['native_eviction_and_page_lookup_subcost_separated'] or cache['cache_barrier_removal_safety_established']:
        error(path, 'static cache attribution overstated as measured subcost or safe omission')
    nxt = d['next_candidate']
    if nxt['evidence_level'] != 'hypothesis' or nxt['implemented'] or nxt['qualified'] or not nxt['no_saving_established'] or (nxt['proposed_pre_evictions'], nxt['proposed_post_evictions'], nxt['previous_evictions_per_two_direction_window']) != (2, 2, 6):
        error(path, 'unimplemented cache epoch presented as a qualified result')
    cleanup = d['cleanup']
    if (cleanup['successful_native_sessions'], cleanup['payload_requests'], cleanup['actual_completions']) != (8, 2930, 2938) or cleanup['live_contexts'] or cleanup['module_references'] or not cleanup['actual_GPUs_idle']:
        error(path, 'native diagnostic cleanup/counters disagree')


def check_cache_epoch_transport():
    d = load('cache-epoch-transport.json')
    path = ROOT / 'data/cache-epoch-transport.json'
    if d['native_CUDA_peer_capabilities'] != [False, False] or any(d[k] for k in ['native_NCCL_backend', 'extra_usable_GiB', 'extra_SM', 'native_core_changed']):
        error(path, 'paired explicit epoch does not establish stock peer support or extra capacity')
    i = d['implementation']
    if (i['native_ABI_bytes'], i['actual_serial_directions'], i['held_actual_buffers'], i['standard_page_queries_per_pair'], i['actual_cache_controls_per_window']) != (288, 2, 4, 6, 4):
        error(path, 'paired epoch native/query/cache scope disagrees')
    if i['native_ABI_independently_enforces_cache_controls'] or not i['copies_retired_only_means_CE_retirement'] or not i['full_CPU_input_incoming_result_hashes_and_guards'] or i['registration_cache'] or i['GPU_digest_substitution'] or i['raw_mapping_used_in_payload']:
        error(path, 'application cache boundary or full verification scope overstated')
    if not i['actual_physical_byte_alias_check'] or not i['destination_page_invariance_checked'] or not i['all_tensor_FDs_and_native_backings_retained_until_mutual_verdict'] or not i['unknown_native_or_peer_work_parks_with_backing']:
        error(path, 'actual identity/page/alias/backing contracts missing')
    if i['tensor_userspace_FD_references_up_to'] != i['original_export_objects_up_to'] + i['received_FD_copies_up_to'] or i['additional_temporary_cache_control_and_GPU_FDs'] != 4:
        error(path, 'tensor FD bounds omit received references or cache client FDs')
    m = d['metadata_qualification']
    if (m['positive_batches'], m['expected_pre_copy_alias_rejections'], m['actual_standard_raw_page_array_comparisons'], m['full_independent_GPU_unchanged_comparisons']) != (3, 1, 16, 16) or m['payload_copies'] or m['peer_done'] != [0, 0]:
        error(path, 'metadata-only checks misrepresented as payload proof')
    q = d['qualification']
    if (q['full_independent_GPU_comparisons'], q['source_and_guard_verdicts'], q['intentional_result_errors_detected'], q['non_root_None_contracts'], q['native_requests'], q['real_completions'], q['successful_context_closes']) != (64, 70, 4, 6, 68, 74, 6):
        error(path, 'independent cache-epoch GPU/guard/close counts disagree')
    if q['native_pair_batches'] * 2 != q['native_requests'] or q['actual_successful_cache_controls'] != 4 * q['native_pair_batches'] or q['fresh_GPU_source_and_destination_rewrite_events'] != 20 or q['L2_dirty_line_state_independently_measured']:
        error(path, 'real cache counts or freshness evidence overstated')
    p = d['model_proof']
    if p['collective_pairs'] != sum(p['operations'].values()) or p['shared_result_hash_pairs'] != p['collective_pairs'] or p['directed_input_tensors'] != 2 * p['collective_pairs']:
        error(path, 'model input/result pair counts disagree')
    if (p['collective_pairs'], p['native_requests'], p['real_completions'], p['uses_per_context']) != (18331, 37180, 37182, [18590, 18590]) or p['native_pair_batches'] * 2 != p['native_requests'] or p['actual_successful_cache_controls'] != 4 * p['native_pair_batches']:
        error(path, 'actual model pair/cache/completion counts disagree')
    if not p['all_full_source_incoming_hashes_match'] or not p['all_shared_result_hashes_match'] or p['activation_CPU_payload_fallback']:
        error(path, 'model full input/result evidence or actual route disagrees')
    pilot = d['pilot']
    if not 0 < pilot['actual_output_tokens'] <= pilot['output_token_cap'] == 8 or not pilot['complete_audit_before_measurement']:
        error(path, 'pilot cap/actual/audit scope disagrees')
    compare = d['comparison']
    previous = next(x for x in compare['earlier_variants'] if x['name'] == 'tp2-ce-quiet-b128-o32')
    ratio = compare['new_variant']['median_sequential_decode_tps_estimate'] / previous['median_sequential_decode_tps_estimate']
    if abs(ratio - compare['decode_ratio_to_previous_quiet']) > 1e-10 or compare['material_gain_established'] or compare['repeated_statistical_speed_study'] or compare['unchanged_SHM_or_previous_batched_replayed'] or not compare['actual_request_hashes_identical']:
        error(path, 'narrow negative comparison overstated or mismatched')
    cost = d['cost_observation']
    share = cost['aggregate_cache_control_s'] / (cost['aggregate_cache_control_s'] + cost['aggregate_pair_ioctl_s'])
    if (cost['windows'], cost['native_window_bytes_per_direction'], cost['public_cache_controls']) != (12900, 10240, 51600) or abs(share - cost['cache_share_of_measured_control_plus_ioctl']) > 1e-12 or cost['syscall_lock_membar_and_L2_subcosts_separated'] or cost['payload_replayed'] or not cost['duplicated_native_chunk_wall_is_shared_pair_time']:
        error(path, 'bounded serial host-phase timing overstated or miscounted')
    close = d['cleanup']
    if (close['successful_native_session_closes'], close['payload_requests'], close['real_completions']) != (10, 37248, 37258) or close['real_completions'] != close['payload_requests'] + close['initial_local_qualifications'] or close['live_contexts'] or close['module_references'] or not close['actual_GPUs_idle']:
        error(path, 'actual epoch cleanup/completion accounting disagrees')
    if close['standard_page_queries'] != 3 * close['payload_requests'] + m['actual_standard_raw_page_array_comparisons']:
        error(path, 'actual standard page queries do not match payload and metadata')
    nxt = d['next_candidate']
    if nxt['evidence_level'] != 'hypothesis' or nxt['implemented'] or nxt['qualified'] or nxt['speed_gain_established']:
        error(path, 'future native cache epoch represented as completed')


def check_native_cache_epoch():
    d = load('native-cache-epoch.json')
    path = ROOT / 'data/native-cache-epoch.json'
    if d['native_CUDA_peer_capabilities'] != [False, False] or any(d[k] for k in ['native_NCCL_backend', 'extra_usable_GiB', 'extra_SM']):
        error(path, 'native epoch does not establish ordinary peer capability or extra capacity')
    i = d['implementation']
    if not i['core_changed'] or not i['kernel_cache_enforcement'] or i['native_ABI_bytes'] != 320 or (i['actual_checked_cache_controls_per_pair'], i['application_cache_controls_per_pair'], i['exact_original_native_helpers_after_namespace_mapping']) != (4, 0, 14):
        error(path, 'new core, ABI or real kernel cache boundary misrepresented')
    if not i['full_CPU_source_incoming_result_hashes_guards_and_CUDA_ordering_preserved'] or i['registration_cache'] or i['GPU_digest_substitution'] or not i['explicit_epoch_complete_only_after_four_successful_statuses_real_retirements_and_safe_cleanup']:
        error(path, 'native epoch data/status/lifetime verification changed')
    q = d['qualification']
    if (q['full_independent_GPU_comparisons'], q['source_and_guard_verdicts'], q['intentional_result_errors_detected'], q['non_root_None_contracts'], q['native_requests'], q['actual_completions']) != (64, 70, 4, 6, 68, 74) or q['actual_successful_native_cache_controls'] != 4 * q['native_pair_batches'] or q['actual_public_cache_controls'] or q['verifier_checks_replay_payload']:
        error(path, 'native epoch independent data/cache/verifier scope disagrees')
    p = d['model_proof']
    if p['collective_pairs'] != sum(p['operations'].values()) or p['shared_result_hash_pairs'] != p['collective_pairs'] or p['directed_input_tensors'] != 2 * p['collective_pairs']:
        error(path, 'diagnostic model operation/input/result counts disagree')
    if (p['collective_pairs'], p['native_requests'], p['actual_completions'], p['uses_per_context'], p['actual_successful_native_cache_controls']) != (1301, 2862, 2864, [1431, 1431], 5724) or p['actual_successful_native_cache_controls'] != 4 * p['native_pair_batches'] or p['actual_public_cache_controls'] or p['activation_CPU_payload_fallback']:
        error(path, 'actual native model cache/data/completion proof disagrees')
    if not p['all_full_source_incoming_hashes_match'] or not p['all_shared_result_hashes_match'] or not 0 < d['pilot']['actual_output_tokens'] <= d['model_settings']['pilot_output_token_cap'] == 8 or d['model_settings']['measured_speed_requests']:
        error(path, 'pilot data/cap/actual/speed scope disagrees')
    profile = d['native_cost'];phases = profile['phases']
    if len(phases) != 5 or not profile['disjoint_five_host_intervals'] or profile['timer_used_as_completion'] or profile['inner_SYS_membar_physical_RM_GSP_L2_subcosts_separated'] or profile['actual_inner_branch_hits_measured'] or profile['phase_errors']:
        error(path, 'bounded native cost or unknown inner dispatch scope overstated')
    for row in phases:
        if row['calls'] != p['native_pair_batches'] or row['total_ns'] < 0 or abs(row['mean_ns'] - row['total_ns'] / row['calls']) > 1e-8 or abs(row['mean_us'] - row['mean_ns'] / 1000) > 1e-8:
            error(path, 'native phase actual counts, sums or units disagree')
    cache = sum(r['total_ns'] for r in phases[:4]);body = phases[4]['total_ns']
    if abs(profile['four_cache_call_mean_us'] - cache / p['native_pair_batches'] / 1000) > 1e-8 or abs(profile['serial_pair_body_mean_us'] - body / p['native_pair_batches'] / 1000) > 1e-8 or abs(profile['cache_share_of_only_five_measured_phases'] - cache / (cache + body)) > 1e-12:
        error(path, 'five disjoint phase summary disagrees')
    if any(d['comparison'].values()):
        error(path, 'diagnostic-only core change overstates throughput or matched SHM')
    close = d['cleanup']
    if (close['successful_native_sessions'], close['payload_requests'], close['actual_completions'], close['successful_native_epochs'], close['successful_native_cache_controls']) != (10, 2930, 2940, 1465, 5860) or close['phase_calls'] != [1465] * 5 or any(close['phase_errors']) or close['live_contexts'] or close['module_references'] or not close['actual_GPUs_idle']:
        error(path, 'native epoch actual close/profile/cache counters disagree')
    if close['old_consumers_currently_loaded'] or not close['old_module_files_preserved'] or not close['historic_counters_reset_on_unload']:
        error(path, 'old loaded state confused with preserved recovery files')
    source = d['source_analysis']
    if source['evidence_level'] != 'static-analysis' or source['inner_status_policy_changed'] or source['actual_GSP_route_established']:
        error(path, 'unknown inner cache behavior presented as measured or changed')
    nxt = d['next_candidate']
    if nxt['implemented'] or nxt['qualified'] or nxt['speed_gain_established']:
        error(path, 'unimplemented inner-cache diagnosis presented as completed')


def check_inner_cache_profile():
    d=load('inner-cache-profile.json');path=ROOT/'data/inner-cache-profile.json'
    if d['ordinary_CUDA_peer_capabilities'] != [False,False] or any(d[k] for k in ['native_NCCL_backend','extra_usable_GiB','extra_SM']):
        error(path,'inner-cache diagnostics overstate peer support or capacity')
    i=d['implementation'];p=d['model'];a=d['inner_cache']
    if not all(i[k] for k in ['diagnostic_only','consumer_ABI_module_and_data_path_unchanged','cache_policy_status_retirement_lifetime_unchanged','all_full_CPU_hashes_and_guards_preserved','existing_consumer_import_CRCs_equal']) or i['timer_used_for_completion'] or i['new_RM_or_GPU_locks']:
        error(path,'diagnostic/data/status/lifetime boundary changed')
    if (p['collective_pairs'],p['requests'],p['actual_completions'],p['actual_cache_controls'],p['actual_output_tokens'],p['measured_speed_requests']) != (1301,2862,2864,5724,4,0) or not p['all_full_input_hashes_match'] or not p['all_shared_result_hashes_match']:
        error(path,'actual diagnostic model proof inconsistent')
    total=0
    for row in a['rows']:
        c=row['phase_count'];n=row['phase_total_ns'];base=row['calls'];total+=base
        if base != 2862 or any(c[k]!=base for k in ['cacheop','sys_child','l2_child','cacheop_exclusive_rest','physical_sys','physical_l2','gsp_sys','gsp_l2','video','video_evict','sys_single_kernel']) or any(c[k] for k in ['video_virtual_noop','sys_virtual_noop','local_sys','local_l2','invalid_accounting']):
            error(path,'actual cache route/counts misrepresented')
        if n['cacheop']!=n['sys_child']+n['l2_child']+n['cacheop_exclusive_rest'] or not n['gsp_sys']<=n['physical_sys']<=n['sys_child'] or not n['gsp_l2']<=n['physical_l2']<=n['l2_child']:
            error(path,'disjoint sum or nested cache accounting inconsistent')
    if total!=5724 or a['actual_RPC_issue_cache_hit_and_firmware_subcosts_separately_measured'] or any(d['comparison'].values()) or any(d['next_candidate'][k] for k in ['implemented','qualified','speed_gain_established']):
        error(path,'unmeasured RPC/firmware/speed or future candidate overstated')


def check_full_cache_route_transport():
    d=load('full-cache-route-transport.json');path=ROOT/'data/full-cache-route-transport.json'
    if d['ordinary_CUDA_peer_capabilities'] != [False,False] or any(d[k] for k in ['native_NCCL_backend','extra_usable_GiB','extra_SM']):
        error(path,'full-cache candidate overstates CUDA peers, capacity or SMs')
    i=d['implementation'];q=d['qualification'];p=d['measured_direct_model_proof'];c=d['comparison'];end=d['cleanup']
    if (i['consumer_ABI_bytes'],i['command'],i['flags'],i['actual_full_cache_controls_per_epoch'],i['local_done']) != (320,'0x2080130e','0x38',4,0) or not all(i[k] for k in ['original_external_device_access_and_lock_checks_preserved','actual_physical_RMAPI_GSP_route_observed','every_actual_returned_status_checked','ordinary_previous_route_unchanged','all_full_CPU_hashes_and_guards_preserved','imports_pages_aliases_retirement_poison_lifetime_checks_preserved']) or i['formal_runtime_equivalence']:
        error(path,'cache API, barrier, access, data or lifetime contract overstated')
    probe=d['support_probe']
    if (probe['actual_cache_calls'],probe['successful_returned_statuses'],probe['actual_GSP_wrapper_calls'],probe['payload_bytes'],probe['models_started'],probe['retained']) != (2,2,2,0,0,0) or not probe['successful_session_close']:
        error(path,'no-payload support probe confused with data proof or retention')
    if (q['independent_full_GPU_comparisons'],q['source_guard_verdicts'],q['intentional_result_errors_detected'],q['requests'],q['actual_completions'],q['actual_full_cache_controls']) != (64,70,4,68,74,136) or q['payload_replayed_to_test_verifier']:
        error(path,'finite independent qualification scope inconsistent')
    if p['collective_pairs'] != sum(p['operations'].values()) or p['directed_inputs'] != 2*p['collective_pairs'] or p['shared_result_hash_pairs'] != p['collective_pairs'] or p['requests'] != 2*p['uses_per_context'][0] or p['uses_per_context'][0] != p['uses_per_context'][1] or p['actual_completions'] != p['requests']+2 or p['actual_full_cache_controls'] != 2*p['requests'] or not p['all_full_input_hashes_match'] or not p['all_shared_result_hashes_match'] or p['CPU_activation_payload_fallback'] or p['public_application_cache_controls']:
        error(path,'actual direct model, cache or full-hash counts disagree')
    if not all(c[k] for k in ['fresh_same_core_SHM','actual_commands_equal_except_port','selected_environment_equal','eleven_installed_runtime_sources_and_model_config_pinned','pilot_excluded']) or (c['TP'],c['PP'],c['max_output_tokens'],c['max_num_batched_tokens'],c['sequential_requests'],c['simultaneous_requests']) != (2,1,32,128,3,4):
        error(path,'fresh matching comparison or workload scope misrepresented')
    ratio=c['SHM']['median_sequential_decode_tps_estimate']/c['direct']['median_sequential_decode_tps_estimate']
    if ratio <= 1 or abs(ratio-c['SHM_over_direct_decode_ratio']) > 1e-12 or not 0 <= c['answer_hash_matches_of_7'] <= 7 or c['quality_or_logit_equivalence'] or c['statistically_repeated_study'] or c['historical_direct_1_78586_is_a_fresh_controlled_baseline']:
        error(path,'speed ratio or finite quality/statistical conclusion overstated')
    if end['actual_completions'] != end['payload_requests']+end['successful_native_sessions'] or end['actual_full_cache_controls'] != 4*end['successful_epochs'] or end['total_observed_full_cache_route_calls'] != end['actual_full_cache_controls']+end['standalone_support_cache_calls'] or any(end[k] for k in ['cache_status_errors','phase_errors','live_contexts','consumer_module_references','selected_current_window_kernel_errors']) or not end['actual_GPUs_idle']:
        error(path,'actual completion/cache/cleanup counters disagree')
    if d['conclusion']['practical_speed_advantage_over_SHM'] or not d['conclusion']['further_optimization_paused']:
        error(path,'bounded negative practical conclusion contradicted')


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
        check_batched_transport()
        check_native_log_transport()
        check_native_cost_profile()
        check_cache_epoch_transport()
        check_native_cache_epoch()
        check_inner_cache_profile()
        check_full_cache_route_transport()
    except (ValueError, KeyError, TypeError) as exc:
        ERRORS.append('data contract: ' + str(exc))
    if ERRORS:
        print('\n'.join(ERRORS))
        return 1
    print(f'Publication check passed: {len(files)} text files; data contracts and local links consistent; no flagged disclosures.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
