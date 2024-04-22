# First-party
import meteodatalab.config


def test_config():
    with meteodatalab.config.set_values(opt1=1):
        assert meteodatalab.config.get("opt1") == 1

        with meteodatalab.config.set_values(opt1=False, opt2=2):
            assert meteodatalab.config.get("opt1") is False
            assert meteodatalab.config.get("opt2") == 2

        assert meteodatalab.config.get("opt1") == 1
        assert meteodatalab.config.get("opt2") is None

    assert meteodatalab.config.get("opt1") is None
