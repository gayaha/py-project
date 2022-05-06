import os
import pickle
import base64
import subprocess
from typing import List


class Command:

    def __init__(self, command_payload: bytearray, command_type, command_identifier: int,
                        command_arguments: List[str]):
        self._command_payload = command_payload
        self._command_type = command_type
        self._command_identifier = command_identifier
        self._command_arguments = command_arguments

    def __str__(self):
        return "Command: " + str(self._command_type) + " #" + str(self._command_identifier) + " (" + str(len(self._command_arguments)) + " arguments)"

    def serialize(self):
        file_bytes = pickle.dumps(self)
        base64_bytes = base64.b64encode(file_bytes)
        return base64_bytes

    @classmethod
    def deserialize(cls, raw_bytes): #cls = class
        decoded = base64.b64decode(raw_bytes) #decode base64
        loaded_command = pickle.loads(decoded) #deserialize pickle to an object

        return loaded_command

    def getPayload(self):
        return self._command_payload

    def save(self, file):
        file.write(self.serialize())

    @classmethod
    def load(cls, file):
        return cls.deserialize(file.read())

    def run(self):
        print(self._command_identifier) # switch to pass
        return "Command completed successfully."


class ShellExecuteCommand(Command):

    def __init__(self, command_type, command_identifier: int, command_arguments: List[str], shell_command):
        super().__init__(self, command_type, command_identifier, command_arguments)
        command_arguments.append(shell_command)
        self._command_arguments = command_arguments

    def run(self):
        return subprocess.check_output(self._command_arguments[0], shell=True).decode()

    def __str__(self):
        return "Shell Execute Command" + str(self._command_arguments[0])