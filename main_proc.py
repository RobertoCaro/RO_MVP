import multiprocessing
import Ocus_check
import time


if __name__ == "__main__":  # confirms that the code is under main function

    procs = []
    ShareDataPool=multiprocessing.Array('i',100)

    for i in range(len(ShareDataPool)):
        ShareDataPool[i]=0
    Value=multiprocessing.Value('d',0.0)


    proc = multiprocessing.Process(target=Ocus_check.networker, args=(ShareDataPool,Value))  # instantiating without any argument
    procs.append(proc)
    proc.start()


    for proc in procs:
        proc.join()

