from pqcrypto.sign import sphincs, ntru_hps_2048_509_509

class QuantumCrypto:
    @staticmethod
    def generate_keypair(algorithm: str):
        if algorithm == "sphincs":
            sk = sphincs.generate_keypair()
            return sk, sk.public_key()
        elif algorithm == "ntru":
            sk = ntru_hps_2048_509_509.generate_keypair()
            return sk, sk.public_key()
        else:
            raise ValueError("Unsupported algorithm")

    @staticmethod
    def sign(message: bytes, private_key, algorithm: str) -> bytes:
        if algorithm == "sphincs":
            return sphincs.sign(message, private_key)
        elif algorithm == "ntru":
            return ntru_hps_2048_509_509.sign(message, private_key)
        else:
            raise ValueError("Unsupported algorithm")

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key, algorithm: str) -> bool:
        try:
            if algorithm == "sphincs":
                sphincs.verify(message, signature, public_key)
            elif algorithm == "ntru":
                ntru_hps_2048_509_509.verify(message, signature, public_key)
            else:
                return False
            return True
        except:
            return False
