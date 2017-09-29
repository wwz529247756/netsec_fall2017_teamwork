'''
Created on 2017年9月28日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL
from playground.network.packet import PacketType
import playground
from asyncio import *


class ServerAppProtocol(Protocol):
    def __init__(self):
        self.transport=None        # transport contains the data you need to transfer while connecting
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        print("Server: Application layer connection made! ")
        self.transport = transport
    
    
    def data_received(self, data):
        print("Data received by server")
            
            
    def connection_lost(self, exc):
        print('Connection stopped because {}'.format(exc))