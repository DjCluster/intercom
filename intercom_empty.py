# Don't send empty bitplanes.
#
# The sender adds to the number of received bitplanes the number of
# skipped (zero) bitplanes of the chunk sent.

# The receiver computes the first received
# bitplane (apart from the bitplane with the signs) and report a
# number of bitplanes received equal to the real number of received
# bitplanes plus the number of skipped bitplanes.

import struct
import numpy as np
from intercom import Intercom
from intercom_dfc import Intercom_DFC

if __debug__:
    import sys

class Intercom_empty(Intercom_DFC):

    def init(self, args):
        Intercom_DFC.init(self, args)
        self.empty_planes = 0
        self.previous_empty_planes = 0

    def send_bitplane(self, indata, bitplane_number):
        bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
        bitplane = bitplane.astype(np.uint8)
        bitplane = np.packbits(bitplane)

        #Check if bitplane is empty. If it is empty we will not send bitplane. If not we will send it.
        if(np.any(bitplane)):
            message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, self.received_bitplanes_per_chunk[(self.played_chunk_number+1) % self.cells_in_buffer]+1, *bitplane)
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
            return 0
        else:
            return 1

    def send(self, indata):
            signs = indata & 0x8000
            magnitudes = abs(indata)
            indata = signs | magnitudes
            
            self.NOBPTS = int(0.75*self.NOBPTS + 0.25*self.NORB)
            self.NOBPTS += 1
            
            #Add empty bitplanes to awaited ones for congestion calculation. If last sent < 8 bitplanes because of 0 bitplanes, no consider congestion
            self.NOBPTS += self.empty_planes

            if self.NOBPTS > self.max_NOBPTS or int(self.previous_empty_planes//self.number_of_channels)<8:
                self.NOBPTS = self.max_NOBPTS

            #Reset empty counter.
            self.previous_empty_planes = self.empty_planes
            self.empty_planes = 0
            last_BPTS = self.max_NOBPTS - self.NOBPTS - 1
            
            #We increase the empty counter if the bitplane is empty.
            self.empty_planes += self.send_bitplane(indata, self.max_NOBPTS-1)
            self.empty_planes += self.send_bitplane(indata, self.max_NOBPTS-2)
            for bitplane_number in range(self.max_NOBPTS-3, last_BPTS, -1):
                self.empty_planes += self.send_bitplane(indata, bitplane_number)
            self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER

if __name__ == "__main__":
    intercom = Intercom_empty()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
