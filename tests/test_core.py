import pytest

@pytest.fixture
def d():
    import dominos
    return dominos.Dominos()

def test_search_store(d):
    stores = d.search_stores('ig8')
    assert len(stores) == 1


