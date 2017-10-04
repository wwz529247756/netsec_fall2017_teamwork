'''
Created on 2017年9月28日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL,UINT8
from playground.network.packet import PacketType
import playground
from asyncio import *
from HandShakePacket import PEEPPacket


class AppPacket(PacketType):
    DEFINITION_IDENTIFIER = "AppRequest"
    DEFINITION_VERSION = "1.0"
    FIELDS=[("Message",STRING),
            ("State",UINT8)]

class ServerAppProtocol(Protocol):
    def __init__(self):
        self.transport=None        # transport contains the data you need to transfer while connecting
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        print("Server: Application layer connection made! ")
        self.transport = transport


    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            msg = pkt.Data.decode()
        print("Server:"+msg)
        

    def connection_lost(self, exc):
        print('Connection stopped because {}'.format(exc))



