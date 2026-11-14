from tldr_bot.utils import parse_and_validate_n


def test_parse_default_n():
    n, msg = parse_and_validate_n("/tldr")
    assert n == 100
    assert msg is None


def test_parse_valid_n():
    n, msg = parse_and_validate_n("/tldr 250")
    assert n == 250
    assert msg is None


def test_parse_under_min_boundary():
    n, msg = parse_and_validate_n("/tldr 49")
    assert n is None
    assert msg == "Just read it, bro"

    n, msg = parse_and_validate_n("/tldr 1")
    assert n is None
    assert msg == "Just read it, bro"

    n, msg = parse_and_validate_n("/tldr -10")
    assert n is None
    assert msg == "Just read it, bro"


def test_parse_over_max_boundary():
    n, msg = parse_and_validate_n("/tldr 1001")
    assert n is None
    assert msg == "It's too much, pay for my tokens first!"

    n, msg = parse_and_validate_n("/tldr 5000")
    assert n is None
    assert msg == "It's too much, pay for my tokens first!"


def test_parse_exact_boundaries():
    n, msg = parse_and_validate_n("/tldr 50")
    assert n == 50
    assert msg is None

    n, msg = parse_and_validate_n("/tldr 1000")
    assert n == 1000
    assert msg is None


def test_parse_invalid_argument():
    n, msg = parse_and_validate_n("/tldr abc")
    assert n is None
    assert "Please provide a valid integer" in msg
