import queue
import threading

from glue_qt.viewers.matplotlib.compute_worker import ComputeWorker


class RecordingQueue(queue.Queue):

    def __init__(self):
        super(RecordingQueue, self).__init__()
        self.blocking = threading.Event()

    def get(self, block=True, timeout=None):
        if block:
            self.blocking.set()
        return super(RecordingQueue, self).get(block=block, timeout=timeout)


def test_compute_worker_blocks_when_idle():

    # An idle worker should wait on the queue rather than poll it, run a job
    # as soon as it is queued, and exit when asked to stop.

    resets = []
    done = threading.Event()

    def function(reset=False):
        resets.append(reset)
        done.set()

    worker = ComputeWorker(function)
    worker.work_queue = RecordingQueue()
    worker.start()

    try:
        assert worker.work_queue.blocking.wait(timeout=5)
        worker.work_queue.put(True)
        assert done.wait(timeout=5)
        assert resets == [True]
    finally:
        worker.work_queue.put('stop')
        assert worker.wait(5000)
