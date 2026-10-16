"""CPU counterexamples for capacity-test methods; never opens a GPU.

Forty/eighty 4-KiB pages model two logical views of forty backing pages.
The upper-view XOR is a synthetic mapping compatible with one historical
observed offset, not a reconstruction of the GPU's complete address decoder.
"""
import json

PAGE_BYTES = 4096
WORD_BYTES = 8
WORDS = PAGE_BYTES // WORD_BYTES
BACKING_PAGES = 40
LOGICAL_PAGES = 80
OFFSET_XOR = 0x900
MASK64 = (1 << 64) - 1
SEEDS = (0xC0FFEE0000000000, 0x39193ED37E73A62B)


def address_pattern(page, word, seed):
    # Injective within this finite logical range, including the word offset.
    return seed ^ (page * WORDS + word)


def hbm45_pattern(page, word, seed):
    return (seed ^ (page * 0x1000000000000)
            ^ (word * 0x9E3779B97F4A7C15)) & MASK64


class Memory:
    def __init__(self, fold=True, offset_xor=OFFSET_XOR):
        self.fold = fold
        self.offset_xor = offset_xor
        self.data = [None] * ((BACKING_PAGES if fold else LOGICAL_PAGES) * WORDS)

    def index(self, page, word):
        if self.fold and page >= BACKING_PAGES:
            page -= BACKING_PAGES
            word ^= self.offset_xor // WORD_BYTES
        return page * WORDS + word

    def write(self, page, word, value):
        self.data[self.index(page, word)] = value

    def read(self, page, word):
        return self.data[self.index(page, word)]


def exercise(name, offsets, *, fold=True, offset_xor=OFFSET_XOR,
             sequential=False, pattern=address_pattern):
    results = []
    for seed in SEEDS:
        memory = Memory(fold, offset_xor)
        errors = 0
        first = None

        def fill(page):
            for word in offsets:
                memory.write(page, word, pattern(page, word, seed))

        def verify(page):
            nonlocal errors, first
            for word in offsets:
                expected = pattern(page, word, seed)
                actual = memory.read(page, word)
                if actual != expected:
                    errors += 1
                    if first is None:
                        first = {'logical_page': page, 'byte_offset': word * WORD_BYTES,
                                 'expected': hex(expected), 'actual': hex(actual)}

        if sequential:
            for page in range(LOGICAL_PAGES):
                fill(page)
                verify(page)
        else:
            for page in range(LOGICAL_PAGES):
                fill(page)
            for page in range(LOGICAL_PAGES):
                verify(page)
        results.append({'seed': hex(seed), 'mismatched_words': errors,
                        'first_mismatch': first})
    return {'name': name, 'folded_backing': fold, 'upper_byte_offset_xor': hex(offset_xor),
            'write_all_before_verify_all': not sequential,
            'words_checked_per_seed': LOGICAL_PAGES * len(offsets),
            'results': results}


def result_channel(copy_succeeded, device_error_count, checked):
    # Model the old zero-initialized destination and a failed copy that leaves it.
    host_count = None if checked else 0
    if copy_succeeded:
        host_count = device_error_count
    if checked and (not copy_succeeded or host_count is None):
        return 'TRANSPORT_ERROR'
    return 'CLEAN' if host_count == 0 else 'DATA_ERROR'


def run():
    cases = [
        exercise('one_tag_per_page_global', (0,)),
        exercise('two_offset_tags_global', (0, OFFSET_XOR // WORD_BYTES)),
        exercise('dense_address_pattern_global', range(WORDS)),
        exercise('dense_address_pattern_chunk_at_a_time', range(WORDS), sequential=True),
        exercise('one_tag_per_page_plain_fold', (0,), offset_xor=0),
        exercise('dense_address_pattern_independent_backing', range(WORDS), fold=False),
        exercise('dense_hbm45_pattern_global', range(WORDS), pattern=hbm45_pattern),
    ]
    expected_errors = (0, 80, 40 * WORDS, 0, 40, 0, 40 * WORDS)
    for case, expected in zip(cases, expected_errors, strict=True):
        assert all(r['mismatched_words'] == expected for r in case['results']), case
    channels = [
        {'name': 'unchecked_failed_copy_with_nonzero_device_errors',
         'copy_succeeded': False, 'device_error_count': 123,
         'verdict': result_channel(False, 123, False)},
        {'name': 'checked_failed_copy_with_nonzero_device_errors',
         'copy_succeeded': False, 'device_error_count': 123,
         'verdict': result_channel(False, 123, True)},
        {'name': 'checked_successful_copy_with_nonzero_device_errors',
         'copy_succeeded': True, 'device_error_count': 123,
         'verdict': result_channel(True, 123, True)},
        {'name': 'checked_successful_copy_with_zero_device_errors',
         'copy_succeeded': True, 'device_error_count': 0,
         'verdict': result_channel(True, 0, True)},
    ]
    assert [c['verdict'] for c in channels] == ['CLEAN', 'TRANSPORT_ERROR', 'DATA_ERROR', 'CLEAN']
    return {
        'schema_version': 1, 'kind': 'cpu-only-method-counterexamples',
        'hardware_capacity_proof': False, 'gpu_accesses': 0,
        'model': {'logical_pages': LOGICAL_PAGES, 'folded_backing_pages': BACKING_PAGES,
                  'page_bytes': PAGE_BYTES, 'word_bytes': WORD_BYTES,
                  'logical_bytes': LOGICAL_PAGES * PAGE_BYTES,
                  'folded_backing_bytes': BACKING_PAGES * PAGE_BYTES,
                  'upper_view_byte_offset_xor': hex(OFFSET_XOR),
                  'mapping_scope': 'Synthetic example, not a complete identified GPU mapping.'},
        'memory_cases': cases, 'result_channel_cases': channels,
        'limits': [
            'Not a reproduction of any historical GPU run.',
            'No conclusion that the external 77.5-GiB test used sparse tags.',
            'A dense whole-page unique-tag fill differs from one tagged word per page.',
            'A possible failed-copy false pass does not prove a past copy failed.',
            'Two offset tags detect this model but do not prove full physical capacity.',
        ],
    }


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
