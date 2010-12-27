from datetime import timedelta
import time

class Timer:
  def __init__(self, name):
    self.name =name

  def __enter__(self):
    self.start = time.time()

  def __exit__(self, *args):
    elapsed = time.time() - self.start
    end = time.time()
    print("%s:\t%0.11s" % (self.name, timedelta(seconds=elapsed)))
