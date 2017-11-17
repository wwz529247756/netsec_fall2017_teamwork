'''
Created on 20170926

@author: wangweizhou
'''

from playground.network.common import *
from .HandShakePacket import *


'''
    Define Packet Size and Window Size!
'''
PACKET_SIZE = 1000
WINDOW_SIZE = 10



class myTransport(StackingTransport):

    def write(self, data):  
        if len(self.info_list.outBuffer) < 3:
            self.info_list.init_seq = self.info_list.sequenceNumber

        if self.info_list.sequenceNumber == self.info_list.init_seq + len(self.info_list.outBuffer):
            self.info_list.outBuffer += data
            self.sent_data()
        else:
            self.info_list.outBuffer += data

    def close(self):
        if self.info_list.readyToclose:
            self.lowerTransport().close()
        else:
            print("Waiting for close!")

    def sent_data(self):
        small_packet = PEEPPacket()
        recordSeq = self.info_list.sequenceNumber
        for n in range(0, WINDOW_SIZE):
            place_to_send = self.info_list.sequenceNumber - self.info_list.init_seq
            if place_to_send + PACKET_SIZE < len(self.info_list.outBuffer):
                packet_data = self.info_list.outBuffer[place_to_send:place_to_send + PACKET_SIZE]
                small_packet.SequenceNumber = self.info_list.sequenceNumber
                self.info_list.sequenceNumber += len(packet_data)
            else:
                packet_data = self.info_list.outBuffer[place_to_send:]
                small_packet.SequenceNumber = self.info_list.sequenceNumber
                self.info_list.sequenceNumber += len(packet_data)
                n = 999
            print("Sent seq number:" + str(self.info_list.sequenceNumber))
            small_packet.Type = 5  
            small_packet.Data = packet_data
            small_packet.Checksum = small_packet.calculateChecksum()
            self.lowerTransport().write(small_packet.__serialize__())

            if n > WINDOW_SIZE:
                break
        self.info_list.sequenceNumber = recordSeq
        
    def setinfo(self, info_list):
        self.info_list = info_list
    
    def get_data(self):
        return self.info_list.data
    
class item_list():
    sequenceNumber = 0
    SessionId = ''
    Acknowledgement = 0
    init_seq = 0
    outBuffer = b''
    readyToclose = False
