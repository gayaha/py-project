import socket
from configparser import ConfigParser

config = ConfigParser()
config.read('configuration.ini')

# connection info
#port = config.get('login', 'PORT')


# client msg status
msg_status = config.get('Client', 'MSG_STATUS')
msg_return_value = config.get('Client', 'MSG_RETURN_VALUE')
msg_error = config.get('Client', 'MSG_ERROR')

# keepalive time in sec
keepalive_seconds = config.get('Client', 'KEEPALIVE_SECONDS')


#host = config.get('login', 'HOST')

# print(host)