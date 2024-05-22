import os
import storage

def file_exists(file):
    try:
        return os.stat(file)[0] & 0x8000 != 0
    except:
        return False

def is_readonly():
    return storage.getmount("/").readonly