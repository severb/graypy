from Queue import Queue
from graypy import GELFHandler
from threading import Thread


class AsyncGELFHandler(GELFHandler, Thread):
    def __init__(self, *args, **kwargs):
        super(AsyncGELFHandler, self).__init__(*args, **kwargs)
        Thread.__init__(self)
        self.output_queue = Queue()

        # Start thread
        self.start()

    def send(self, s):
        self.output_queue.put(s)

    def _process_queue_record(self, s):
        super(AsyncGELFHandler, self).send(s)

    def run(self):

        while True:
            try:
                record = self.output_queue.get()
                self._process_queue_record(record)
                self.output_queue.task_done()
            except Exception as ex:
                pass
