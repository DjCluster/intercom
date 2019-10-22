# Adding a buffer.

#Current Version 1.4 - status: working
#Restriction:   -increase samples per chunk to 2048
#               -samples per have to be multiply of 8
#Version history

#1.3 - Added code comments
#1.2 - Cleaning up metods
#1.1 - new structure for seperat channel sending
#1.0 - implementation bitplane object

import sounddevice as sd
import numpy as np
import struct
from intercom_buffer import Intercom_buffer
#Import Object Intercom
from intercom import Intercom

if __debug__:
    import sys

class Intercom_bitplanes(Intercom_buffer):

    def init(self, args):
        Intercom_buffer.init(self, args)
        self.bitplaneregister = np.zeros(self.chunks_to_buffer,dtype="int16")
        self.packet_format="!BBH{}B".format((self.samples_per_chunk//8)//self.number_of_channels)
        #sys.stderr.write("\n\nFORMAT: {}".format(self.packet_format)); sys.stderr.flush()
    def run(self):
        self.recorded_chunk_number = 0
        self.played_chunk_number = 0

        def receive_and_buffer():
            message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)

            #Get elements of sent message
            #bp_number = bitplane number of package
            #channel_number = channel number of package
            #chunk_number = chunk number of package
            bp_number, channel_number,chunk_number, *bitplane = struct.unpack(self.packet_format, message)

            #Get sent Bitplane list and but in converted numpy array
            bp_channel_array=np.asarray(bitplane, dtype=np.uint8)

            #Unpack bits
            bp_channel_raw=np.unpackbits(bp_channel_array)
            
            #Convert values to signed integer 16 BIT
            bp_channel_received=bp_channel_raw.astype(np.int16)

            #Binary compare channel in message buffer with received Bitplane
            self._buffer[chunk_number % self.cells_in_buffer][:,channel_number]=self._buffer[chunk_number % self.cells_in_buffer][:,channel_number] | bp_channel_received << bp_number

            #if bp_number==0:
            #    sys.stderr.write("\nREC_MSG[{}]: {}".format(chunk_number,self._buffer[chunk_number % self.cells_in_buffer])); sys.stderr.flush()                        
    
            return chunk_number

        def record_send_and_play(indata, outdata, frames, time, status):

            #Get message from sound card buffer
            msg=np.frombuffer(indata, np.int16).reshape(self.frames_per_chunk, self.number_of_channels)

            #sys.stderr.write("\n\nSND_MSG[{}]: {}".format(self.recorded_chunk_number,msg)); sys.stderr.flush()
            
            #Iterate channels
            for i in range(self.number_of_channels):
                #Iterate Bitplanes
                for b in range(15,-1,-1):
                    #Get bitplane "b" of channel "i"
                    bitplane=msg[:,i] >> b & 1
                    #Conversion bits to unsigned integer
                    bitplane_raw=bitplane.astype(np.uint8)
                    #Pack bits to packet
                    bitpack=np.packbits(bitplane_raw)

                    #Create message with structure
                    message = struct.pack(self.packet_format, b,i, self.recorded_chunk_number, *(bitpack))

                    #Send message
                    self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))

            #Increase chunk number
            self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER    

            chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
            self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
            self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
            outdata[:] = chunk

            if __debug__:
                sys.stderr.write("."); sys.stderr.flush()

        with sd.Stream(samplerate=self.frames_per_second, blocksize=self.frames_per_chunk, dtype=np.int16, channels=self.number_of_channels, callback=record_send_and_play):
            print("-=- Press CTRL + c to quit -=-")
            first_received_chunk_number = receive_and_buffer()
            self.played_chunk_number = (first_received_chunk_number - self.chunks_to_buffer) % self.cells_in_buffer
            while True:
                receive_and_buffer()
                
if __name__ == "__main__":
    intercom = Intercom_bitplanes()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
