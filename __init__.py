'''
Created on 2017年10月4日

@author: wangweizhou
'''

from playground.network.common import StackingProtocolFactory
import playground
import HandShakePacket
from TranSerProto import *
from TranCliProto import *
from ServerPassThrough import *
from ClientPassThrough import *

lab2ClientFactory = StackingProtocolFactory(lambda: ClientPassThrough(), lambda: TranCliProto())
lab2ServerFactory = StackingProtocolFactory(lambda: ServerPassThrough(), lambda: TranSerProto())
lab2Connector = playground.Connector(protocolStack=(lab2ClientFactory, lab2ServerFactory))
playground.setConnector("lab2_protocol", lab2Connector)