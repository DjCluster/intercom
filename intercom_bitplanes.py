# Adding a buffer.

import sounddevice as sd
import numpy as np
import struct
from intercom_buffer import Intercom_buffer
from intercom import Intercom

if __debug__:
    import sys

class Intercom_bitplanes(Intercom_buffer):

    def init(self, args):
        Intercom_buffer.init(self, args)
        self.bitplaneregister = np.zeros(self.chunks_to_buffer,dtype="int16")
        self.packet_format="!hhh{}c".format(self.sample_per_chunk/8)

    def run(self):
        self.recorded_chunk_number = -1
        self.played_chunk_number = 0
        self.currentbit = 16
        self.channelbuffer = np.zeros((self.samples_per_chunk, self.number_of_channels),dtype=np.int16)
        
        def receive_and_buffer():
            message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
            bitplanenumber, chunk_number, *bitplane = struct.unpack(self.packet_format, message)

            msg=np.unpackbits(bitplane)
            msgchannel=msg.astype(np.int16)

            msgout=msgchannel.reshape((self.samples_per_chunk))
            
            self._buffer[chunk_number % self.cells_in_buffer]=self._buffer[chunk_number % self.cells_in_buffer][nrchannel]+msgout
            #self._buffer[chunk_number % self.cells_in_buffer] = np.asarray(chunk).reshape(self.frames_per_chunk, self.number_of_channels)
            return chunk_number

        def record_send_and_play(indata, outdata, frames, time, status):

            msg=np.frombuffer(message, np.int16).reshape(self.frames_per_chunk, self.number_of_channels)

            for i in range(self.number_of_channels):
                self.channelbuffer[i]=msg[:,i]

                for b in range(16)
                    bitplane=self.channelbuffer[i] >> (15-b) & 1
                    conversion=bitplane.astype(np.byte)
                    bitpack=np.packbits(convert)

                    message = struct.pack(self.packet_format, (15-b), self.recorded_chunk_number, *(bitpack))
                    self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port)
            
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
