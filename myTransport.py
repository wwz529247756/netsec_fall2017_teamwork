'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from HandShakePacket import PEEPPacket
import random

class TranTransport(StackingTransport):
    def write(self, data):
        self.Size = 20
        #PacketSize = 50
        Slices = [data[i:(i+self.Size)] for i in range(0, len(data), self.Size)]
        #Seq = self.CurrentSeq
        
        for SingleSlice in Slices:
            
            Pkt = PEEPPacket()
            Pkt.Type = 5
            Pkt.SequenceNumber = 0
            #Seq = Seq + 1
            Pkt.Acknowledgement = 0
            Pkt.Data = SingleSlice
            Pkt.Checksum = 0
            Pkt.updateChecksum()
            #self.PktsBuffer.put(Pkt)
            self.lowerTransport().write(Pkt.__serialize__())
            print("Client: Transport packet sent! ")
        '''
            Require data packet type definition here!
        '''
        
    def close(self):
        print("Client: Rip request sent!")
        closePacket = PEEPPacket()
        closePacket.Type = 3
        closePacket.SequenceNumber = random.randint(0, 1000)
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        closePacket.updateChecksum()
        self.lowerTransport().write(closePacket.__serialize__())

