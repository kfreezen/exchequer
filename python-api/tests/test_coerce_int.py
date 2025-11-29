from python_api.models import CamelModel, CoerceToInt


def test_coerce_int():
    class T(CamelModel):
        a: CoerceToInt

    t = T(a=None)
    assert t.a == 0
