# test/__init__.py
import os
import sys

# เพิ่ม path ของโปรเจคเข้าไปใน Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)