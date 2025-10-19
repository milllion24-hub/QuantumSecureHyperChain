ffrom typing import Tuple
from pqcrypto.sign import sphincs_sha3_512fs_simple
from pqcrypto.sign import falcon_512

class QuantumCrypto:
    @staticmethod
    def generate_keypair(algorithm: str) -> Tuple[object, object]:
        if algorithm == "sphincs":
            sk, pk = sphincs_sha3_512fs_simple.keypair()
            return sk, pk
        elif algorithm == "ntru":
            sk, pk = falcon_512.keypair()
            return sk, pk
        else:
            raise ValueError("Unsupported algorithm")

    @staticmethod
    def sign(message: bytes, private_key, algorithm: str) -> bytes:
        if algorithm == "sphincs":
            return sphincs_sha3_512fs_simple.sign(message, private_key)
        elif algorithm == "ntru":
            return falcon_512.sign(message, private_key)
        else:
            raise ValueError("Unsupported algorithm")

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key, algorithm: str) -> bool:
        try:
            if algorithm == "sphincs":
                sphincs_sha3_512fs_simple.verify(message, signature, public_key)
            elif algorithm == "ntru":
                falcon_512.verify(message, signature, public_key)
            return True
        except:
            return False
