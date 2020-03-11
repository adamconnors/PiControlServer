import threading
import time


class ArmMover(threading.Thread):
    a0 = 0
    a1 = 0
    a2 = 0
    a3 = 0
    def run(self):
        while True:
            time.sleep(2)
            print("a0=%d a1=%d a2=%d a3=%d" % (self.a0, self.a1, self.a2, self.a3))

def main():
        armMover = ArmMover()
        armMover.start()
        print("Thread started")
        time.sleep(5)
        print("Setting a0")
        armMover.a0 = 1


if __name__ == '__main__':
    main()