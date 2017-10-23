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
from AppPacket import AppPacket

class ClientAppProtocol(Protocol):
    def __init__(self):
        self.transport=None        # transport contains the data you need to transfer while connecting
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        print("Client: Application layer connection made! ")
        self.transport = transport
        self.echo()
    def data_received(self, data):
        print("Data received by client")

    def echo(self):
        mypacket = AppPacket()
        mypacket.Message = "This is the transport layer test!"
        self.transport.write(mypacket.__serialize__())
        '''
        while(True):
            msg = input("Please input message:");
            if msg == "quit":
                print("Client: Application Stop!")
                break
            else:
                
                    Require Dumpling transport!
                
                mypacket = AppPacket()
                mypacket.Message = msg
                self.transport.write(mypacket.__serialize__())
        '''
    def connection_lost(self, exc):
        print('Connection stopped because {}'.format(exc))

