from command import *
import uuid
from typing import List
import os
import socket
import time
import threading
import queue
from packetbuilder import *
from network_comms import *
import read_config


class Client:
    STATUS_RECEIVED = "Received"
    STATUS_INITIALIZED = "Initialized"
    STATUS_RUNNING = "Running"
    STATUS_FINISHED = "Finished"
    STATUS_ERROR = "Error"
    network = None
    MSG_STATUS = "STATUS"
    MSG_RETURN_VALUE = "RETURN_VALUE"
    MSG_ERROR = "ERROR"
    #KEEPALIVE_SECONDS = 10

    # add to the messages queue a new status packet
    def _send_status(self, command_identifier, status):
        self.network.send_packet(StatusPacket(command_identifier, status))

    # add to the messages queue a new return value packet
    def _send_return_value(self, command_identifier, return_value):
        self.network.send_packet(ReturnValuePacket(command_identifier, return_value))

    def _send_error_msg(self, command_identifier, error_msg):
        self.network.send_packet(ErrorPacket(command_identifier, error_msg))

    def keepalive_thread(self):
        while True:
            self.network.send_packet(KeepAlivePacket())
            time.sleep(int(read_config.keepalive_seconds))

    def command_pull_thread(self):
        while True:
            self.network.send_packet(GetCommandPacket())
            time.sleep(30)

    def command_worker(self):
        while True:
            for command_file_name in os.listdir("."):  # edit configuration file
                if command_file_name.endswith(".gaya"):
                    # This is a command payload
                    with open(command_file_name, "rb") as command_file_object:
                        # Open the command
                        cmd = Command.load(command_file_object)
                        self._send_status(cmd._command_identifier, self.STATUS_INITIALIZED)
                        print("Running> " + str(cmd))
                        self._send_status(cmd._command_identifier, self.STATUS_RUNNING)
                        try:
                            return_value = cmd.run()  # 5
                            self._send_return_value(cmd._command_identifier, return_value)
                        except Exception as e:
                            self._send_error_msg(cmd._command_identifier, "An exception of type " + str(e.__class__) + " occurred")
                        self._send_status(cmd._command_identifier, self.STATUS_FINISHED)
                    try:
                        os.remove(command_file_name) #9
                    except PermissionError:
                        print("Could not delete " + command_file_name)

    def run(self):
        host = socket.gethostname()  # as both code is running on same pc
        port = 5001  # socket server port number

        client_socket = socket.socket()  # instantiate
        client_socket.connect((host, port))  # connect to the server

        self.network = NetworkComms(client_socket)
        self.network.start()

        # Start child threads
        threading.Thread(target=self.command_worker, daemon=True).start()
        threading.Thread(target=self.keepalive_thread, daemon=True).start()
        threading.Thread(target=self.command_pull_thread, daemon=True).start()

        while True:
            packet = self.network.get_packet()
            if isinstance(packet, KillPacket):
                # Exit program
                pass
            elif isinstance(packet, CommandPacket):
                new_command = packet.command
                ts = str(time.time())

                # Write the command to a temporary file
                with open('payload' + ts + '.gayatemp', 'wb') as file:
                    new_command.save(file)

                # Move temporary file to permanent file
                os.rename('payload' + ts + '.gayatemp', 'payload' + str(ts) + '.gaya')

                print('Received from server: ' + str(new_command))  # show in terminal
                self._send_status(new_command._command_identifier, self.STATUS_RECEIVED)

        self.network.close()


if __name__ == "__main__":
    c = Client()
    c.run()









