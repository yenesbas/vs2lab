import rpc
import logging
import time

from context import lab_logging

def callback(result_tuple):
    # result_tuple is (APPEND, DBList)
    if len(result_tuple) > 1:
        print("Result: {}".format(result_tuple[1].value))
    else:
        print("Result: {}".format(result_tuple))

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})
cl.append('bar', base_list, callback)

for i in range(15):
    print("Client is doing other work...")
    time.sleep(1)

cl.stop()
