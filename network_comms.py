import socket
import queue
import threading
from packetbuilder import *

# this class is a blackbox which manges the network and returns output


class NetworkComms():
    STATE_WAITING = 0
    STATE_PACKET_LENGTH = 1
    STATE_READ_PACKET = 2
    STATE_DONE = 3

    def __init__(self, socket, address=""):
        self._incoming_data_buffer = queue.Queue()
        self._incoming_packets = queue.Queue()
        self._outgoing_packets = queue.Queue()
        self.socket = socket
        self.address = address

        self.closed = False

    def _incoming_packet_builder(self):
        # a thread which converts the data flow within the incoming data buffer into packets
        # implemented by a state machine
        current_state = self.STATE_WAITING
        msg_type = -1 # will hold the message type
        payload_length_buffer = []  # this buffer will be used to hold the bytes that represent the data's length
        payload_length = 0  # will hold the data's length (after converting the bytes into int)
        payload = []  # this buffer will hold the payload
        while True:
            if current_state == self.STATE_WAITING:
                # Take out the message type from the buffer
                msg_type = self._incoming_data_buffer.get()
                current_state = self.STATE_PACKET_LENGTH
            elif current_state == self.STATE_PACKET_LENGTH:
                # Take out the data length from the buffer
                for x in range(0, 4):
                    payload_length_buffer.append(self._incoming_data_buffer.get())

                payload_length = int.from_bytes(bytes(payload_length_buffer), "big")
                current_state = self.STATE_READ_PACKET
            elif current_state == self.STATE_READ_PACKET:
                # Take out the payload from the buffer (size = payload_length)
                if payload_length > 0:
                    for y in range(0, payload_length):
                        payload.append(self._incoming_data_buffer.get())

                current_state = self.STATE_DONE
            elif current_state == self.STATE_DONE:
                # Prepare the payload for decoding
                packet = None

                # Decode the payload according to its message type
                if msg_type == MSG_TYPE['keepalive']:
                    packet = KeepAlivePacket.decode(payload)
                elif msg_type == MSG_TYPE['command_packet']:
                    packet = CommandPacket.decode(payload)
                elif msg_type == MSG_TYPE['status_packet']:
                    packet = StatusPacket.decode(payload)
                elif msg_type == MSG_TYPE['return_value_packet']:
                    packet = ReturnValuePacket.decode(payload)
                elif msg_type == MSG_TYPE['error_packet']:
                    packet = ErrorPacket.decode(payload)
                elif msg_type == MSG_TYPE['get_command_packet']:
                    packet = GetCommandPacket.decode(payload)
                else:
                    print("Unknown packet type " + str(msg_type))

                # Pass the payload on to the next level
                self._incoming_packets.put(packet)

                # Clear the state variables
                msg_type = -1
                payload_length_buffer = []
                payload_length = 0
                payload = []
                current_state = self.STATE_WAITING

# this thread reads  from the socket and adds the bytes to the incoming data buffer

    def _receive_loop(self):
        while True:
            # receive data stream. it won't accept data packet greater than 1024 bytes
            try:
                data = self.socket.recv(1024)
                if data:
                    # We loop through all incoming bytes and add to the buffer
                    for b in data:
                        self._incoming_data_buffer.put(b)
            except ConnectionResetError:
                self.close()
                break

    def _send_loop(self):
        while True:
            packet = self._outgoing_packets.get()
            raw_bytes = packet.encode()
            try:
                self.socket.send(raw_bytes)
                #print("\nSent: " + str(packet) + ".")
            except ConnectionResetError:
                self.close()
                break

    def send_packet(self, packet):
        #print("\nQueued packet " + str(packet) + " for transmission.")
        self._outgoing_packets.put(packet)

    def get_packet(self, block=True):
        return self._incoming_packets.get(block=block)

    def start(self):
        threading.Thread(name="ReceiveLoop", target=self._receive_loop, daemon=True).start()
        threading.Thread(name="SendLoop", target=self._send_loop, daemon=True).start()
        threading.Thread(name="IncomingPacketBuilder", target=self._incoming_packet_builder, daemon=True).start()

    def close(self):
        try:
            self.socket.close()  # close the connection
        except Exception:
            pass
        self.closed = True
        print(str(self.address) + " disconnected.")
