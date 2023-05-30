import pytest

def add(a, b):
    return a + b

@pytest.mark.security
def test_add_01():
    assert 3 == add(1, 2)

@pytest.mark.memory
def test_add_02():
    assert 3 == add(2, 1)

@pytest.mark.ras
class TestDemo:
    def test_add_03(self):
        assert 4 == add(1, 3)

    def test_add_04(self):
        assert 5 == add(2, 3)

