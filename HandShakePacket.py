'''
Created on 20170926

@author: wangweizhou
'''

from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, UINT8, UINT16


'''
    PType: record packet type:
    PType==0    SYN packet
    PType==1    SYN&ACK packet
    PType==2    ACK packet
    PType==3    RIP
    PType==4    RIP-ACK
    PType==5    RST
    Seq: store SYN sequential number
    Ack: store Ack sequential number which should be (syn+1)
'''


class HsPkt(PacketType):
    DEFINITION_IDENTIFIER = "HandshakePacket"
    DEFINITION_VERSION = "1.0"
    FIELDS=[("Type",UINT8),
            ("SequenceNumber",UINT32),
            ("Acknowledgement",UINT32),
            ("Checksum",UINT16)]
    
    
    