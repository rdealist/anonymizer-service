# app/anonymizer.py
import pydicom
from pydicom.errors import InvalidDicomError
from io import BytesIO
import yaml
from .utils import hash_value
from .config import settings
import os

class DicomAnonymizer:
    def __init__(self, profile_name: str = 'default'):
        self.profile_name = profile_name
        self.rules = self._load_rules(profile_name)
        # For persistent hashing, we might need a secret key.
        # This could be loaded from config for better security.
        self.persistent_hash_secret = os.getenv("PERSISTENT_HASH_SECRET", "default-secret-key")

    def _load_rules(self, profile_name):
        try:
            with open(settings.PROFILES_PATH, "r", encoding="utf-8") as f:
                all_profiles = yaml.safe_load(f)
            
            if not all_profiles or 'profiles' not in all_profiles:
                raise ValueError("Invalid profiles format in profiles.yaml")

            return all_profiles['profiles'].get(profile_name, [])
        except FileNotFoundError:
            raise ValueError(f"Profiles file not found at {settings.PROFILES_PATH}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing profiles.yaml: {e}")


    def anonymize(self, file_bytes: bytes) -> pydicom.Dataset:
        try:
            # Read from byte stream, no temporary file on disk
            dataset = pydicom.dcmread(BytesIO(file_bytes), force=True)
        except InvalidDicomError:
            raise ValueError("Invalid DICOM file.")

        for rule in self.rules:
            tag = tuple(rule['tag'])
            action = rule.get('action', 'keep')
          
            if tag in dataset:
                element = dataset[tag]
                if action == "remove":
                    del dataset[tag]
                elif action == "empty":
                    element.value = ""
                elif action == "replace":
                    element.value = rule.get('value', '')
                elif action == "hash":
                    element.value = hash_value(str(element.value))
                elif action == "hash_persistent":
                    element.value = hash_value(str(element.value), salt=self.persistent_hash_secret)
                # "keep" is the default action, so we do nothing.

        # Crucial step: Mark the file as anonymized as per DICOM standard
        dataset.add_new((0x0012, 0x0062), 'CS', 'YES')
        
        # Also update SOP Instance UID to ensure it's a new, derived object
        dataset.SOPInstanceUID = pydicom.uid.generate_uid()

        return dataset

    def anonymize_and_save_to_bytes(self, file_bytes: bytes) -> BytesIO:
        """
        Anonymizes a DICOM file and saves the result to an in-memory bytes buffer.
        """
        anonymized_dataset = self.anonymize(file_bytes)
        
        mem_file = BytesIO()
        # Use pydicom's high-level API to save, ensuring correct file meta info
        anonymized_dataset.save_as(mem_file, write_like_original=False)
        mem_file.seek(0) # Rewind the buffer to the beginning
        return mem_file
