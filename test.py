import unittest
import multiprocessing
from clock import Machine
import time
import os
import glob

class TestMachine(unittest.TestCase):

    def setUp(self):
        self.machines = []
        self.fixed_freq = [4,5,6]
        for i in range(3):
            clock_rate = self.fixed_freq[i]
            machine = Machine(i, clock_rate)
            self.machines.append(machine)

        for machine in self.machines:
            machine.connect_all(self.machines)

        self.processes = []
        for machine in self.machines:
            process = multiprocessing.Process(target=machine.run)
            process.start()
            self.processes.append(process)

    def tearDown(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join()
        for f in glob.glob("*.log"):
            os.remove(f)
        for f in glob.glob("*.csv"):
            os.remove(f)

    def test_handle_random_event(self):
        machine = self.machines[0]
        for i in range(10):
            machine.handle_random_event()
        self.assertGreater(machine.logical_clock, 0)
    def test_machine_connection(self):
        m1 = Machine(1, 1)
        m2 = Machine(2, 1)
        m1.connect(m2)
        m2.connect(m1)
        time.sleep(0.01)
        self.assertEqual(len(m1.connections), 1)
        self.assertEqual(len(m2.connections), 1)
        self.assertEqual(m1.connections[m2.id], m2)
        self.assertEqual(m2.connections[m1.id], m1)

    def test_machine_send_message(self):
        m1 = Machine(1, 1)
        m2 = Machine(2, 1)
        m1.connect(m2)
        m1.send_message("hello", m2.id)
        message, sender_id, sender_logical_clock = m2.message_queue.get()
        self.assertEqual(message, "hello")
        self.assertEqual(sender_id, m1.id)
        self.assertEqual(sender_logical_clock, 1)

    def test_machine_receive_message(self):
        m1 = Machine(1, 1)
        m2 = Machine(2, 1)
        m3 = Machine(3, 1)
        machines = [m1, m2, m3]
        m1.connect_all(machines)
        m2.connect_all(machines)
        m3.connect_all(machines)
        m1.send_message("hello", m2.id)
        m2.rec_message()
        self.assertEqual(m2.logical_clock, 2)



    def test_machine_log(self):
        m = Machine(1, 1)
        m.log("test")
        with open("machine_1.log", "r") as f:
            log_message = f.readlines()[-1].strip()
        self.assertIn("Global Time", log_message)
        self.assertIn("Queue Length", log_message)
        self.assertIn("Logical Clock", log_message)
        self.assertIn("test", log_message)

    def test_machine_run(self):
        m1 = Machine(1, 1)
        m2 = Machine(2, 1)
        m3 = Machine(3, 1)
        machines = [m1, m2, m3]

        m1.connect_all(machines)
        m2.connect_all(machines)
        m3.connect_all(machines)
        processes = []
        for m in [m1, m2, m3]:
            process = multiprocessing.Process(target=m.run, args=())
            process.start()
            processes.append(process)
        time.sleep(2)

        start_time = time.time()
        for process in processes:
            process.join(timeout=3 - (time.time() - start_time))
            if process.is_alive():
                process.terminate()
                process.join()


if __name__ == "__main__":
    unittest.main()
