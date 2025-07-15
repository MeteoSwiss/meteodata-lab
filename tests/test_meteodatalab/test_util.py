import pytest

from meteodatalab import util


def test_queue():
    queue = util.Queue(maxsize=5)
    for i in range(5):
        queue.add_item(i)

    with pytest.raises(queue.Full):
        queue.add_item(5)

    queue.add_item(3)
    assert queue.pop_item() == 0
    queue.add_item(1)
    assert queue.pop_item() == 2
    assert queue.pop_item() == 4
    assert queue.pop_item() == 3
    assert queue.pop_item() == 1
    queue.add_item(5)
    assert queue.pop_item() == 5

    with pytest.raises(KeyError):
        queue.pop_item()
