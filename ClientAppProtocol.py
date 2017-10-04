'''
Created on 2017年9月28日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL,UINT8
from playground.network.packet import PacketType
import playground
from asyncio import *
from ctypes.test.test_random_things import callback_func
from HandShakePacket import PEEPPacket

class AppPacket(PacketType):
    DEFINITION_IDENTIFIER = "AppRequest"
    DEFINITION_VERSION = "1.0"
    FIELDS=[("Message",STRING)]


class ClientAppProtocol(Protocol):
    def __init__(self):
        self.transport=None        # transport contains the data you need to transfer while connecting
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        print("Client: Application layer connection made! ")
        self.transport = transport
        self.echo()

    def SentRequest(self,callback=None):
        self.callback = callback
        request = AppPacket()
        request.Message = "Request"
        self.transport.write(request.__serialize__())
        print("data sent!")

    def data_received(self, data):
        print("Data received by client")

    def echo(self):
        while(True):
            msg = input("Please input message:");
            if msg == "quit":
                print("Client: Application Stop!")
                break
            else:
                '''
                    Require Dumpling transport!
                '''
                mypacket = PEEPPacket()
                mypacket.Checksum = 0
                mypacket.SequenceNumber = 0
                mypacket.Acknowledgement=0
                mypacket.Data = msg.encode()
                mypacket.Type = 5
                self.transport.write(mypacket.__serialize__())
    def connection_lost(self, exc):
        print('Connection stopped because {}'.format(exc))

