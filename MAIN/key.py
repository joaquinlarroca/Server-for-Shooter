from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import base64
import aiofiles
import os
import sys
import datetime

import color


os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print(color.FAIL + "THIS IS NOT THE MAIN PY FILE" + color.ENDC)
    sys.exit()

private_key = None
public_key = None
public_key_pem = None


async def load_keys():
    global private_key, public_key, public_key_pem
    try:
        os.mkdir("key")
    except FileExistsError:
        pass
    except PermissionError:
        print(
            f"{color.FAIL}Permission denied: Unable to create 'key'.{color.ENDC}"
        )
    except Exception as e:
        print(f"{color.FAIL}Unexpected error: {e}{color.ENDC}")
    try:
        async with aiofiles.open("./key/date.txt", "r") as file:
            keydate = await file.read()
            if keydate != datetime.datetime.now().strftime("%d-%m-%Y"):
                try:
                    os.remove("./key/private_key.pem")
                    os.remove("./key/public_key.pem")
                    async with aiofiles.open("./key/date.txt", "w") as file:
                        await file.write(datetime.datetime.now().strftime("%d-%m-%Y"))

                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"{color.FAIL}Unexpected error: {e}{color.ENDC}")
    except FileNotFoundError:
        try:
            async with aiofiles.open("./key/date.txt", "w") as file:
                await file.write(datetime.datetime.now().strftime("%d-%m-%Y"))
        except Exception as e:
            print(f"{color.FAIL}Error writing data: {e}{color.ENDC}")
            
    try:
        async with aiofiles.open("./key/private_key.pem", "rb") as file:
            private_key = serialization.load_pem_private_key(
                await file.read(),
                password=None,  # If your private key is encrypted, provide the password here
            )
    except FileNotFoundError:
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048
            )
            async with aiofiles.open("./key/private_key.pem", "wb") as file:
                await file.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
        except Exception as e:
            print(f"{color.FAIL}Error generating private key: {e}{color.ENDC}")

    except Exception as e:
        print(f"{color.FAIL}Error loading private key: {e}{color.ENDC}")

    try:
        async with aiofiles.open("./key/public_key.pem", "rb") as file:
            public_key = serialization.load_pem_public_key(await file.read())
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
    except FileNotFoundError:
        try:
            public_key = private_key.public_key()
            async with aiofiles.open("./key/public_key.pem", "wb") as file:
                await file.write(
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        except Exception as e:
            print(f"{color.FAIL}Error generating public key: {e}{color.ENDC}")

    except Exception as e:
        print(f"{color.FAIL}Error loading public key: {e}{color.ENDC}")


def decrypt_data(encrypted_data):
    global private_key
    decoded_data = base64.b64decode(encrypted_data)
    try:
        decrypted_data = private_key.decrypt(
            decoded_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return decrypted_data.decode("utf-8")  # Assuming the original data was text
    except Exception as e:
        print(f"{color.FAIL}Error decrypting data: {e}{color.ENDC}")
        return None
