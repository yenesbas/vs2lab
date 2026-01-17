import logging
import random
import time

from constMutex import ENTER, RELEASE, ALLOW, ACTIVE, CRASHED


class Process:
    """
    Implements access management to a critical section (CS) via fully
    distributed mutual exclusion (MUTEX).

    Processes broadcast messages (ENTER, ALLOW, RELEASE, CRASHED) timestamped with
    logical (lamport) clocks. All messages are stored in local queues sorted by
    logical clock time.

    Processes follow different behavioral patterns. An ACTIVE process competes 
    with others for accessing the critical section. A PASSIVE process will never 
    request to enter the critical section itself but will allow others to do so.

    A process broadcasts an ENTER request if it wants to enter the CS. A process
    that doesn't want to ENTER replies with an ALLOW broadcast. A process that
    wants to ENTER and receives another ENTER request replies with an ALLOW
    broadcast (which is then later in time than its own ENTER request).

    A process enters the CS if a) its ENTER message is first in the queue (it is
    the oldest pending message) AND b) all other processes have sent messages
    that are younger (either ENTER or ALLOW). RELEASE requests purge
    corresponding ENTER requests from the top of the local queues.
    
    When a process detects another process has crashed (after 3 timeouts), it
    broadcasts a CRASHED message with the crashed process ID. All processes
    receiving this message remove the crashed process from their lists.

    Message Format:

    <Message>: (Timestamp, Process_ID, <Request_Type>, [Crashed_Process_ID])

    <Request Type>: ENTER | ALLOW  | RELEASE | CRASHED

    """

    def __init__(self, chan):
        self.channel = chan  # Create ref to actual channel
        self.process_id = self.channel.join('proc')  # Find out who you are
        self.all_processes: list = []  # All procs in the proc group
        self.other_processes: list = []  # Needed to multicast to others
        self.queue = []  # The request queue list
        self.clock = 0  # The current logical clock
        self.peer_name = 'unassigned'  # The original peer name
        self.peer_type = 'unassigned'  # A flag indicating behavior pattern
        self.logger = logging.getLogger("vs2lab.lab5.mutex.process.Process")
        self.timeouts = {}

    def __mapid(self, id='-1'):
        # format channel member address
        if id == '-1':
            id = self.process_id
        return 'Proc-'+str(id)

    def __cleanup_queue(self):
        if len(self.queue) > 0:
            # self.queue.sort(key = lambda tup: tup[0])
            self.queue.sort()
            # There should never be old ALLOW messages at the head of the queue
            while self.queue[0][2] == ALLOW:
                del (self.queue[0])
                if len(self.queue) == 0:
                    break

    def __request_to_enter(self):
        self.clock = self.clock + 1  # Increment clock value
        request_msg = (self.clock, self.process_id, ENTER)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

    def __allow_to_enter(self, requester):
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)  # Permit other

    def __release(self):
        # need to be first in queue to issue a release
        assert self.queue[0][1] == self.process_id, 'State error: inconsistent local RELEASE'

        # construct new queue from later ENTER requests (removing all ALLOWS)
        tmp = [r for r in self.queue[1:] if r[2] == ENTER]
        self.queue = tmp  # and copy to new queue
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, RELEASE)
        # Multicast release notification
        self.channel.send_to(self.other_processes, msg)

    def __broadcast_crash(self, crashed_id):
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, CRASHED, crashed_id)
        self.logger.warning("{} broadcasting that {} has crashed".
                            format(self.__mapid(), self.__mapid(crashed_id)))
        self.channel.send_to(self.other_processes, msg)

    def __remove_crashed_process(self, crashed_id):
        # Remove crashed process from other_processes list if present
        if crashed_id in self.other_processes:
            self.other_processes.remove(crashed_id)
            self.logger.info("{} removed crashed {} from other_processes".
                            format(self.__mapid(), self.__mapid(crashed_id)))
        # Remove all messages from crashed process from queue
        self.queue = [r for r in self.queue if r[1] != crashed_id]
        self.__cleanup_queue()

    def __allowed_to_enter(self):
        # If queue is empty or no other processes exist, allow entry
        if len(self.queue) == 0:
            return False  # No request pending, should not enter
        if len(self.other_processes) == 0:
            return True  # No other processes to wait for
        
        # See who has sent a message (the set will hold at most one element per sender)
        processes_with_later_message = set([req[1] for req in self.queue[1:]])
        # Access granted if this process is first in queue and all others have answered (logically) later
        first_in_queue = self.queue[0][1] == self.process_id
        all_have_answered = len(self.other_processes) == len(processes_with_later_message)
        return first_in_queue and all_have_answered

    def __receive(self):
        # If there are no other processes, nothing to receive; avoid calling redis BLPOP with empty keys
        if len(self.other_processes) == 0:
            time.sleep(0.5)
            return

        # Pick up any message
        _receive = self.channel.receive_from(self.other_processes, 3)
        if _receive:
            msg = _receive[1]
            self.timeouts[msg[1]] = 0

            self.clock = max(self.clock, msg[0])  # Adjust clock value...
            self.clock = self.clock + 1  # ...and increment

            self.logger.debug("{} received {} from {}.".format(
                self.__mapid(),
                "ENTER" if msg[2] == ENTER
                else "ALLOW" if msg[2] == ALLOW
                else "CRASHED" if msg[2] == CRASHED
                else "RELEASE", self.__mapid(msg[1])))

            if msg[2] == ENTER:
                self.queue.append(msg)  # Append an ENTER request
                # and unconditionally allow (don't want to access CS oneself)
                self.__allow_to_enter(msg[1])
            elif msg[2] == ALLOW:
                self.queue.append(msg)  # Append an ALLOW
            elif msg[2] == RELEASE:
                # assure release requester indeed has access (his ENTER is first in queue)
                assert self.queue[0][1] == msg[1] and self.queue[0][2] == ENTER, 'State error: inconsistent remote RELEASE'
                del (self.queue[0])  # Just remove first message
            elif msg[2] == CRASHED:
                # Another process detected a crash - remove crashed process
                crashed_id = msg[3]
                self.__remove_crashed_process(crashed_id)

            self.__cleanup_queue()  # Finally sort and cleanup the queue
        else:
            self.logger.info("{} timed out on RECEIVE. Local queue: {}".
                             format(self.__mapid(),
                                    list(map(lambda msg: (
                                        'Clock '+str(msg[0]),
                                        self.__mapid(msg[1]),
                                        msg[2]), self.queue))))
            
            # Only count timeouts if we have an active ENTER request ourselves
            # (i.e., we're waiting to enter CS and expect ALLOW responses)
            my_enter_request = None
            for entry in self.queue:
                if entry[1] == self.process_id and entry[2] == ENTER:
                    my_enter_request = entry
                    break
            
            if my_enter_request is not None:
                # We're waiting to enter CS - check who hasn't sent ALLOW yet
                allow_ids = set([r[1] for r in self.queue if r[2] == ALLOW and r[1] != self.process_id])
                
                # Also check if someone is blocking at position 0
                blocker_id = None
                if len(self.queue) > 0 and self.queue[0][2] == ENTER and self.queue[0][1] != self.process_id:
                    blocker_id = self.queue[0][1]
                
                for p in list(self.other_processes):
                    should_timeout = False
                    
                    if p not in allow_ids:
                        # This process has not sent ALLOW yet
                        should_timeout = True
                    elif p == blocker_id:
                        # This process is blocking at the head of the queue
                        should_timeout = True
                    
                    if should_timeout:
                        self.timeouts[p] = self.timeouts.get(p, 0) + 1
                        self.logger.warning("{} did not answer. (Count: {})".
                                            format(self.__mapid(p), self.timeouts[p]))
                    
                    if self.timeouts[p] >= 3:
                        self.logger.warning("{} suspects {} to have crashed".
                                            format(self.__mapid(), self.__mapid(p)))
                        # Broadcast crash notification to all other processes
                        self.__broadcast_crash(p)
                        # Remove crashed process locally
                        self.__remove_crashed_process(p)
                    else:
                        # Reset timeout counter if process has responded and is not blocking
                        if not should_timeout:
                            self.timeouts[p] = 0
            else:
                # No active ENTER request - reset all timeouts
                self.timeouts = {}

    def init(self, peer_name, peer_type):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        # sort string elements by numerical order
        self.all_processes.sort(key=lambda x: int(x))

        self.other_processes = list(self.channel.subgroup('proc'))
        self.other_processes.remove(self.process_id)

        self.peer_name = peer_name  # assign peer name
        self.peer_type = peer_type  # assign peer behavior

        self.logger.info("{} joined channel as {}.".format(
            peer_name, self.__mapid()))

    def run(self):
        while True:
            # Enter the critical section if
            # 1) there are more than one process left and
            # 2) this peer has active behavior and
            # 3) random is true
            if len(self.all_processes) > 1 and \
                    self.peer_type == ACTIVE and \
                    random.choice([True, False]):
                self.logger.debug("{} wants to ENTER CS at CLOCK {}."
                                  .format(self.__mapid(), self.clock))

                self.__request_to_enter()
                while not self.__allowed_to_enter():
                    self.__receive()

                # Stay in CS for some time ...
                sleep_time = random.randint(0, 2000)
                self.logger.debug("{} enters CS for {} milliseconds."
                                  .format(self.__mapid(), sleep_time))
                print(" CS <- {}".format(self.__mapid()))
                time.sleep(sleep_time/1000)

                # ... then leave CS
                print(" CS -> {}".format(self.__mapid()))
                self.__release()
                continue

            # Occasionally serve requests to enter (
            if random.choice([True, False]):
                self.__receive()