from multiprocessing import Process, Queue, Condition
import time


def upload_video(upload_queue: Queue, condition: Condition):
    while True:
        video = upload_queue.get()
        if video is None:
            print('End of uploading videos')
            return
        print(f'process for video {video["title"]}')
        time.sleep(5)
        print(f'video {video["title"]} has uploaded')
        if upload_queue.empty():
            with condition:
                print('waiting for other videos')
                condition.wait()


def main():
    v1 = {'title': 'video 1'}
    v2 = {'title': 'video 2'}
    v3 = {'title': 'video 3'}

    queue = Queue()
    condition = Condition()

    queue.put(v1)

    process = Process(target=upload_video, args=(queue, condition))
    # q = multiprocessing.Queue()

    time.perf_counter()

    process.start()
    print('process has started')

    time.sleep(2)
    print('sleep 2s done')
    queue.put(v2)
    print('video 2 has putted in queue')

    with condition:
        condition.notify_all()

    print('script finished')

    queue.put(None)
    with condition:
        condition.notify_all()


if __name__ == '__main__':
    main()
