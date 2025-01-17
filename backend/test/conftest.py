# conftest.py
import pytest

def pytest_configure(config):
    """กำหนดค่าพื้นฐานสำหรับการทดสอบ"""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )