import multiprocessing

from vent.coordinator import rpc


class ProcessManager:
    # Functions:
    def __init__(self, sim_mode, startCommandLine=None, maxHeartbeatInterval=None):
        self.sim_mode = sim_mode
        self.command_line = None  # TODO: what is this?
        self.max_heartbeat_interval = None
        self.previous_timestamp = None
        self.child_process = multiprocessing.Process(target=rpc.rpc_server_main, args=(self.sim_mode,))
        self.child_process.daemon = True
        self.child_process.start()
        self.child_pid = self.child_process.pid

    def __del__(self):
        self.stop_process()

    def start_process(self):
        if self.child_process is not None:
            # Child process already started
            return
        self.child_process = multiprocessing.Process(target=rpc.rpc_server_main, args=(self.sim_mode,))
        self.child_process.daemon = True

        self.child_process.start()
        self.child_pid = self.child_process.pid

    def stop_process(self):
        if self.child_process is not None:
            # print(f'kill process {self.child_pid}')
            self.child_process.kill()

    def restart_process(self):
        if self.child_process is not None:
            self.stop_process()
        self.start_process()

    def heartbeat(self, timestamp):
        # if no heartbeat in maxInterval restart
        pass

