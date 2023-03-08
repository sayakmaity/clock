import multiprocessing
import time
import random
import glob
import os
import datetime
import csv
import signal

# set seed
random.seed(0)


class Machine:
    def __init__(self, id, clock_rate):
        self.id = id
        self.clock_rate = clock_rate
        self.logical_clock = 0
        self.message_queue = multiprocessing.Queue()
        self.connections = {}
        self.message_queue_count = multiprocessing.Value("i", 0)
        self.all_machines = []
        self.prev_logical_clock = 0

    def connect(self, other_machine):
        self.connections[other_machine.id] = other_machine

    def connect_all(self, machines):
        self.all_machines = machines
        for machine in machines:
            if machine.id != self.id:
                self.connect(machine)
                machine.connect(self)

    def send_message(self, message, recipient_id):
        """
        > The function sends a message to a recipient process, and increments the logical clock

        :param message: The message to be sent
        :param recipient_id: The id of the process to send the message to
        """
        self.logical_clock += 1
        recipient = self.connections[recipient_id]
        recipient.message_queue.put((message, self.id, self.logical_clock))
        recipient.message_queue_count.value += 1

    def handle_random_event(self):
        """
        If the random value is 1, send a message to the first connection. If the random value is 2, send
        a message to the second connection. If the random value is 3, send a message to all connections.
        Otherwise, handle an internal event
        """
        rand_val = random.randint(1, 10)
        conn = list(self.connections.keys())
        if rand_val == 1:
            recipient_id = conn[0]
            self.send_message(self.logical_clock, recipient_id)
            self.log(f"Sent message to {recipient_id}")
        elif rand_val == 2:
            recipient_id = conn[1]
            self.send_message(self.logical_clock, recipient_id)
            self.log(f"Sent message to {recipient_id}")
        elif rand_val == 3:
            for recipient_id in conn:
                self.send_message(self.logical_clock, recipient_id)
            self.log("Sent message to all recipients")
        else:
            self.logical_clock += 1
            self.log("Internal event")

    def log(self, message):
        """
        It writes a message to a log file and a csv file

        :param message: The message to be logged
        """
        global_time = time.time()
        queue_length = self.message_queue_count.value
        logical_clock = self.logical_clock
        logical_clock_diff = logical_clock - self.prev_logical_clock
        log_message = f"Global Time: {global_time} | Queue Length: {queue_length} | Logical Clock: {logical_clock} | {message}"
        with open(f"machine_{self.id}.log", "a") as f:
            f.write(log_message + "\n")
        csv_row = [
            global_time,
            queue_length,
            logical_clock,
            logical_clock_diff,
            message,
        ]
        with open(f"machine_{self.id}.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(csv_row)
        self.prev_logical_clock = logical_clock

    def rec_message(self):
        """
        > The `rec_message` function is called by the `rec_message_thread` thread. It receives a message
        from the `message_queue` and updates the `logical_clock` accordingly
        """
        message, sender_id, senderical_clock = self.message_queue.get(block=True)
        self.logical_clock = max(self.logical_clock, senderical_clock) + 1
        self.log(f"Received message from {sender_id}")
        self.message_queue_count.value -= 1

    def run(self):
        """
        The `run` function is the main loop of the program. It runs at the clock rate specified by the user.
        It checks if there are any messages in the queue, and if so, it calls the `rec_message` function. If
        there are no messages in the queue, it calls the `handle_random_event` function
        """
        while True:
            # if :
            if (not self.message_queue.empty()) and self.message_queue_count.value > 0:
                self.rec_message()
            else:
                self.handle_random_event()

            time.sleep(1 / self.clock_rate)


if __name__ == "__main__":
    # Deleting all the log and csv files in the directory.
    for f in glob.glob("*.log"):
        os.remove(f)
    for f in glob.glob("*.csv"):
        os.remove(f)

    machines = []
    fixed_freq = [4, 5, 6]
    # Creating 3 machines with clock rates 1, 3, and 6.
    for i in range(3):
        # set clock_rate to be a random number between 1 and 6 inclusive
        # clock_rate = random.randint(1, 6)
        clock_rate = fixed_freq[i]
        machine = Machine(i, clock_rate)
        machine.log(f"Initialized machine {i} with clock rate {clock_rate}")
        machines.append(machine)

    # Connecting all the machines to each other.
    for machine in machines:
        machine.connect_all(machines)

    # Creating a list of processes and starting them.
    processes = []
    for machine in machines:
        process = multiprocessing.Process(target=machine.run)
        process.start()
        processes.append(process)

    # Waiting for all the processes to finish or until 60 seconds have elapsed.
    start_time = time.time()
    for process in processes:
        process.join(timeout=10 - (time.time() - start_time))
        if process.is_alive():
            process.terminate()
            process.join()
