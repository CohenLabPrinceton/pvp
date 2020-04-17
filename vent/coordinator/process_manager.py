import threading
import time


class ProcessManager:
    # Functions:
    def __init__(self, startCommandLine=None, maxHeartbeatInterval=None):
        self.thread = threading.Thread(target=self.start)
        self.thread.start()
        self.command_line = None  # TODO: what is this?
        self.max_heartbeat_interval = None
        self.previous_timestamp = None
        self.process_id = None

    def __del__(self):
        self.thread.join()

    def startProcess(self):
        pass

    def stopProcess(self):
        pass

    def restartProcess(self):
        pass

    def heartbeat(self, timestamp):
        # if no heartbeat in maxInterval restart
        pass

    def start(self):
        while True:
            time.sleep(10)

# Instance Variables:
#     commandLine
#     maxHeartbeatInterval
#     previousTimestamp
#     processId
