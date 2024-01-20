from src.config import Secret


def test_secret() -> None:
    assert str(Secret("")) == "        ****".strip()
    assert str(Secret("1")) == "       ****".strip()
    assert str(Secret("12")) == "      ****".strip()
    assert str(Secret("123")) == "     ****".strip()
    assert str(Secret("1234")) == "    ****".strip()
    assert str(Secret("12345")) == "   ****45".strip()
    assert str(Secret("123456")) == "  ****56".strip()
    assert str(Secret("1234567")) == " ****67".strip()
    assert str(Secret("12345678")) == "****78"

    assert repr(Secret("")) == "        ****".strip()
    assert repr(Secret("1")) == "       ****".strip()
    assert repr(Secret("12")) == "      ****".strip()
    assert repr(Secret("123")) == "     ****".strip()
    assert repr(Secret("1234")) == "    ****".strip()
    assert repr(Secret("12345")) == "   ****45".strip()
    assert repr(Secret("123456")) == "  ****56".strip()
    assert repr(Secret("1234567")) == " ****67".strip()
    assert repr(Secret("12345678")) == "****78"
