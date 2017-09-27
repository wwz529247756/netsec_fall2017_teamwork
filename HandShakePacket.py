'''
Created on 2017年9月26日

@author: wangweizhou
'''

from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL

class HsPkt(PacketType):
    DEFINITION_IDENTIFIER = "Handshake"
    DEFINITION_VERSION = "1.0"
    FIELDS=[("PType",UINT32),("Seq",UINT32),("Ack",UINT32)]