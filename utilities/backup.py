import os
import zipfile
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

from datetime import datetime

class BackupSystem:
    def __init__(self, source_folder: str, backup_destination_folder: str):
        self.source_folder = source_folder
        self.backup_destination_folder = backup_destination_folder
        self.zipped_file_path = None
        self.encrypted_file_path = None

        os.makedirs(self.backup_destination_folder, exist_ok=True)

    def _create_zip_backup(self) -> str | None:
        folder_path = self.source_folder
        if not folder_path or not os.path.exists(folder_path):
            return None

        # Generate timestamped backup filename
        timestamp = datetime.now().strftime("Backup_%d-%m_%I-%M_DB.zip")
        self.zipped_file_path = os.path.join(self.backup_destination_folder, timestamp)

        try:
            # Create the ZIP backup
            with zipfile.ZipFile(self.zipped_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)  # Maintain folder structure
                        zipf.write(file_path, arcname)
            return self.zipped_file_path
        except Exception as e:
            return None

    def _unzip_file(self, zipped_file_path: str, destination_folder: str) -> bool:

        if not os.path.exists(zipped_file_path):
            return False

        os.makedirs(destination_folder, exist_ok=True)

        try:
            with zipfile.ZipFile(zipped_file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_folder)
            os.remove(zipped_file_path)
            return True
        except Exception as e:
            return False

    def _encrypt_file(self, file_path: str, password: str) -> str | None:
        # Determine the output file path based on the desired naming convention
        output_file_path = file_path
        if output_file_path.endswith(".zip"):
            # Replace .zip with .enc
            output_file_path = output_file_path[:-4] + ".enc"
        else:
            # If not a zip, just append .enc
            output_file_path = output_file_path + ".enc"

        try:
            # Generate a random salt for key derivation
            salt = get_random_bytes(16)
            # Derive a 32-byte (256-bit) key from the password and salt using PBKDF2
            # Increased iteration count for stronger security
            key = PBKDF2(password, salt, dkLen=32, count=1267489, hmac_hash_module=SHA256)

            # Create an AES cipher object in GCM mode
            cipher = AES.new(key, AES.MODE_GCM)

            with open(file_path, 'rb') as infile:
                plaintext = infile.read()

            # Encrypt the data
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)

            with open(output_file_path, 'wb') as outfile:
                # Write salt, nonce, tag, and ciphertext to the output file
                # The salt is needed for key derivation during decryption
                # The nonce is needed for AES GCM decryption
                # The tag is used for integrity verification (authenticity)
                outfile.write(salt)
                outfile.write(cipher.nonce)
                outfile.write(tag)
                outfile.write(ciphertext)

            self.encrypted_file_path = output_file_path
            return output_file_path
        except Exception as e:
            self.encrypted_file_path = None
            return None

    def _decrypt_file(self, encrypted_file_path: str, password: str, output_file_path: str | None = None) -> str | None:

        output_file_path = encrypted_file_path[:-4] + ".zip"

        try:
            with open(encrypted_file_path, 'rb') as infile:
                # Read salt, nonce, tag, and ciphertext from the encrypted file
                salt = infile.read(16)
                nonce = infile.read(16)
                tag = infile.read(16)
                ciphertext = infile.read()

            # Derive the key using the same password and salt
            key = PBKDF2(password, salt, dkLen=32, count=1267489, hmac_hash_module=SHA256)

            # Create an AES cipher object with the derived key and nonce
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

            # Decrypt the data and verify the tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            with open(output_file_path, 'wb') as outfile:
                outfile.write(plaintext)

            return output_file_path
        except ValueError:
            return None
        except Exception as e:
            return None

    def perform_backup_and_encrypt(self, encryption_password: str) -> str | None:
        """
        Performs the zip backup and then encrypts the created zip file.
        Returns the path to the encrypted file if successful, otherwise None.
        """
        self.zipped_file_path = self._create_zip_backup()

        if not self.zipped_file_path:
            return None

        # Step 2: Encrypt the Zip File
        encrypted_file = self._encrypt_file(self.zipped_file_path, encryption_password)

        if not encrypted_file:
            return None

        return encrypted_file
    
    def perform_decrypt_and_restore(self, encrypted_file_path: str, password: str) -> bool:
        """
        Decrypts a given encrypted file.
        Returns True if decryption is successful, otherwise False.
        """
        decrypted_file = self._decrypt_file(encrypted_file_path, password)

        if not decrypted_file:
            return False
        
        unzip_file = self._unzip_file(decrypted_file, self.source_folder)

        if not unzip_file:
            return False          
        
        return True
    
    def cleanup_temp_zip(self):
        if self.zipped_file_path and os.path.exists(self.zipped_file_path):
            try:
                os.remove(self.zipped_file_path)
            except Exception:
                return
            
