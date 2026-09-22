import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'experiments/work/buffalo/rlwe_sa'))
from rlwe_sa import RlweSA
from rlwe_sa.cc.python import _shell_encryption as native

print('NATIVE_EXTENSION:', native.__file__, flush=True)
assert native.__file__.endswith('.so')

if len(sys.argv) > 1 and sys.argv[1] == 'roundtrip':
    instance = RlweSA(2048, 11)
    key = instance.gen_secret_key()
    plaintext = [position % 257 for position in range(2048)]
    print('Encrypting 2048 elements through upstream wrapper', flush=True)
    assert instance.decrypt(key, instance.encrypt(key, plaintext)) == plaintext
elif len(sys.argv) > 1 and sys.argv[1] == 'seeded-roundtrip':
    source = native.RlweSecAgg(2048, 11)
    seed = source.get_seed()
    instance = native.RlweSecAgg(2048, 11, seed)
    key = instance.sample_key()
    plaintext = [position % 257 for position in range(2048)]
    assert instance.decrypt(key, instance.encrypt(key, plaintext)) == plaintext
    print('PASS seeded matrix roundtrip at 2048 elements', flush=True)
else:
    ptxt_bits = 11
    plaintext_modulus = (1 << ptxt_bits) + 1
    modulus = 332366567264636929
    for size in (2048,):
        server = native.RlweSecAgg(size, ptxt_bits)
        aggregate = None
        sum_key = None
        expected = [0] * size
        for client_index in range(5):
            plaintext = [(position * 17 + client_index * 13) % plaintext_modulus for position in range(size)]
            key = server.sample_key()
            ciphertext = server.encrypt(key, plaintext)
            assert server.decrypt(key, ciphertext) == plaintext
            expected = [(left + right) % plaintext_modulus for left, right in zip(expected, plaintext)]
            key_vector = server.convert_key(key)
            if aggregate is None:
                aggregate = ciphertext
                sum_key = key_vector
            else:
                aggregate = server.aggregate(aggregate, ciphertext)
                sum_key = [(left + right) % modulus for left, right in zip(sum_key, key_vector)]
        actual = server.decrypt(server.create_key(sum_key), aggregate)
        assert actual == expected
        print(f'PASS independent keys=5 elements={size} blocks={len(aggregate)} modular_sum=True key_roundtrip=True', flush=True)
    wrapper = RlweSA(2048, ptxt_bits)
    key = wrapper.gen_secret_key()
    plaintext = [position % 257 for position in range(2048)]
    assert wrapper.decrypt(key, wrapper.encrypt(key, plaintext)) == plaintext
    print('PASS wrapper roundtrip 2048 elements', flush=True)
