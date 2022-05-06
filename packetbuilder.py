import base64
import pickle
from command import *


MSG_TYPE = {'invalid': -1,
                'keepalive': 1,
                'command_packet': 2,
                'status_packet': 3,
                'return_value_packet': 4,
                'error_packet': 5,
                'get_command_packet': 6}


class Packet:
    def __init__(self, msg_type):
        self.msg_type = msg_type

    # encode int to bytes
    def encode_int(self, i):
        return i.to_bytes(4, 'big')

    """
        Returns tuple (int - decoded, remainder of bytes)
    """
    @classmethod
    def decode_int(cls, raw_bytes, endian="big"):
        buffer = raw_bytes[0:4]
        return int.from_bytes(buffer, endian), bytes(raw_bytes[4:])

    """
        Data - byte array
    """
    def encode_with_size(self, data):
        return self.encode_int(len(data)) + data

    """
        Returns tuple (decoded data, remainder of bytes)
    """
    @classmethod
    def decode_with_size(cls, raw_bytes):
        size, data = cls.decode_int(raw_bytes, "little")
        return bytes(data[0:size]), bytes(data[size:])

    """
        This is the method that prepares the packet to go out to the network
    """
    def encode(self):
        return self.msg_type.to_bytes(1, byteorder='big') + self.encode_with_size(self.build_packet())

    @classmethod
    def decode(cls, packet_payload):
        return None

    def build_packet(self):
        return b""

    def __str__(self):
        return "Packet (" + str(self.msg_type) + ") "


class KeepAlivePacket(Packet):
    def __init__(self):
        super().__init__(MSG_TYPE['keepalive'])

    @classmethod
    def decode(cls, packet_payload):
        return KeepAlivePacket()

    def __str__(self):
        return super().__str__() + " Keep Alive Packet"


class CommandPacket(Packet):
    def __init__(self, command):
        super().__init__(MSG_TYPE['command_packet'])
        self.command = command

    def build_packet(self):
        return super().build_packet() + self.encode_with_size(self.command.serialize())

    def __str__(self):
        return super().__str__() + str(self.command)

    @classmethod
    def decode(cls, packet_payload):
        command_payload, remainder = cls.decode_with_size(packet_payload)
        command = Command.deserialize(bytes(command_payload))
        return CommandPacket(command)


class CommandIdentifierPacket(Packet):
    def __init__(self, msg_type, command_identifier):
        super().__init__(msg_type)
        self.command_identifier = command_identifier

    def __str__(self):
        return super().__str__() + " Command ID: " + str(self.command_identifier)

    def build_packet(self):
        return super().build_packet() + self.encode_int(self.command_identifier)

    @classmethod
    def decode(cls, packet_payload):
        return None


class StatusPacket(CommandIdentifierPacket):
    def __init__(self, command_identifier, status):
        super().__init__(MSG_TYPE["status_packet"], command_identifier)
        self.status = status

    def __str__(self):
        return super().__str__() + " Status: " + str(self.status)

    def build_packet(self):
        return super().build_packet() + self.encode_with_size(self.status.encode())

    @classmethod
    def decode(cls, packet_payload):
        command_identifier, remainder = cls.decode_int(packet_payload)
        status, remainder = cls.decode_with_size(remainder)
        return StatusPacket(command_identifier, status.decode())


class ErrorPacket(CommandIdentifierPacket):
    def __init__(self, command_identifier, error_msg):
        super().__init__(MSG_TYPE["error_packet"], command_identifier)
        self.error_msg = error_msg

    def __str__(self):
        return super().__str__() + " Error Message: " + str(self.error_msg)

    def build_packet(self):
        return super().build_packet() + self.error_msg.encode()

    @classmethod
    def decode(cls, packet_payload):
        command_identifier, remainder = cls.decode_int(packet_payload)
        error_message, remainder = cls.decode_with_size(remainder)
        return StatusPacket(command_identifier, error_message.decode())


class ReturnValuePacket(CommandIdentifierPacket):
    def __init__(self, command_identifier, return_value):
        super().__init__(MSG_TYPE["return_value_packet"], command_identifier)
        self.return_value = return_value

    def __str__(self):
        return super().__str__() + " Return Value: " + str(self.return_value)

    def build_packet(self):
        return super().build_packet() + self.encode_with_size(base64.b64encode(pickle.dumps(self.return_value)))

    @classmethod
    def decode(cls, packet_payload):
        command_identifier, remainder = cls.decode_int(packet_payload)
        raw_return_value, remainder = cls.decode_with_size(packet_payload)
        decoded_return_value = base64.b64decode(raw_return_value)
        deserialised_return_value = pickle.loads(decoded_return_value)
        return ReturnValuePacket(command_identifier, deserialised_return_value)


class GetCommandPacket(Packet):
    def __init__(self):
        super().__init__(MSG_TYPE['get_command_packet'])

    @classmethod
    def decode(cls, packet_payload):
        return GetCommandPacket()

    def __str__(self):
        return super().__str__() + " Get Command Packet"


if __name__ == "__main__":
    """p = KeepAlivePacket()
    print(p)
    p = StatusPacket(1024, "Running")
    print(p)
    p = ErrorPacket(1024, "Oh no!")
    print(p)
    p = CommandPacket(Command(None, 3, 1024, ['123', '456']))
    print(p)
    p = ReturnValuePacket(1024, ["hi", "gaya"])
    print(p)
    p = GetCommandPacket()
    print(p)"""

    p = ReturnValuePacket(1024, ['123', '456'])
    # CommandPacket(Command(None, 3, 1024, ['123', '456']))
    print(p)
    print("Encoding...")
    print(p.encode())
    print("Decoding...")
    print(ReturnValuePacket.decode(p.encode()[5:]))


