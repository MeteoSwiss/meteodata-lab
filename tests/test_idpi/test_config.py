# First-party
import idpi.config


def test_config():
    with idpi.config.set_values(opt1=1):
        assert idpi.config.get("opt1") == 1

        with idpi.config.set_values(opt1=False, opt2=2):
            assert idpi.config.get("opt1") is False
            assert idpi.config.get("opt2") == 2

        assert idpi.config.get("opt1") == 1
        assert idpi.config.get("opt2") is None

    assert idpi.config.get("opt1") is None
