# -----------------------------------------------------------------------------
# Heart Rate Monitor for Mi Band 6 and 7
# -----------------------------------------------------------------------------
# Author: Daniel Oliveira
# https://github.com/danielsousaoliveira
# -----------------------------------------------------------------------------
# Mi Band 6 Class script

import numpy as np
import gatt
from Crypto.Cipher import AES
import matplotlib.pyplot as plt
import time
from const import *
from ecdh import *

initialTime = 0

# -----------------------------------------------------------------------------
# Mi Band 6 Class
# -----------------------------------------------------------------------------

class MiBand6(gatt.Device):

    def __init__(self, mac_address, manager):

        """ Initialize device class using gatt-python library """

        super().__init__(mac_address, manager)

    def connect(self, authKey):

        """ Connect with the device
            Initialize important variables
            Search for service and characteristics and store them """

        super().connect()

        self.privateKey = np.zeros(6,dtype=np.uint32)
        self.publicKey = np.zeros(12,dtype=np.uint32)
        self.secretKey = np.zeros(12,dtype=np.uint32)
        self.reassemble = np.zeros(64,dtype=np.uint8)
        self.authKey = authKey

        self.create_public_key()

        self.service1 = self.serviceHeart = self.serviceNotif = None
        self.charChunked = self.charChunkedW = self.charNotif = None
        self.charHrControl = self.charHrMeasure = self.charTime = None              
        self.handle = self.lastNumber = self.expectedB = self.pointer = 0

        self.hrHist = [[],[]]

        for s in self.services:
            if s.uuid == UUIDS.SERVICE_MIBAND1:
                self.service1 = s
                for c in self.service1.characteristics:
                    if c.uuid == UUIDS.CHARACTERISTIC_CHUNKED_TRANSFER_READ:
                        self.charChunked = c
                    if c.uuid == UUIDS.CHARACTERISTIC_CHUNKED_TRANSFER_WRITE:
                        self.charChunkedW = c
            if s.uuid == UUIDS.SERVICE_HEART_RATE:
                self.serviceHeart = s
                for c in self.serviceHeart.characteristics:
                    if c.uuid == UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL:
                        self.charHrControl = c
                    if c.uuid == UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE:
                        self.charHrMeasure = c
            if s.uuid == UUIDS.SERVICE_ALERT_NOTIFICATION:
                self.serviceNotif = s
                for c in self.serviceNotif.characteristics:
                    if c.uuid == UUIDS.CHARACTERISTIC_ALERT:
                        self.charNotif = c

    def create_public_key(self):

        """ Use ECDH private-public key agreement to create a public key for the user 
            Stores private and public key in the class """

        privateKey = np.zeros(6,dtype=np.uint32)
        publicKey = np.zeros(12,dtype=np.uint32)
        for i in range(6):
            privateKey[i] = np.random.randint(4294967296, dtype=np.uint32)

        self.privateKey, self.publicKey = ecdh_generate_keys(privateKey,publicKey)

    def enable_notifications_chunked(self):

        """ Enable notifications of Chunked Transfer Characteristic
            Used to start authentication process """

        self.charChunked.enable_notifications()

    def ping_hr(self):

        """ Function used to query heart rate """

        # Starts continuous measurement
        self.charHrControl.write_value([0x15, 0x01, 0x01])
        # Sets measurement interval
        self.charHrControl.write_value([0x14, 0x00, 0x01])

    def start_hr_measure(self):

        """ Start Heart Rate Measurement """

        global initialtime
        initialtime = time.time()

        print("Starting Heart Rate Measurement:")
        self.charHrMeasure.enable_notifications()

        # Starts continuous measurement
        self.charHrControl.write_value([0x15, 0x01, 0x01])
        # Sets measurement interval
        self.charHrControl.write_value([0x14, 0x00, 0x01])
     
    def send_alert(self):

        """ Function that sends call notification to the band """

        print("Sending Call Notification to the band")
        self.charNotif.write_value([0x03, 0x01, 0x0a, 0x0a, 0x0a])

    def print_hr(self):
        
        """ Function to plot recorded heart rate """

        plt.plot(self.hrHist[1], self.hrHist[0])
        plt.scatter(self.hrHist[1], self.hrHist[0], color="red")
        plt.show()


    def write_chunked_value(self,handle,data):

        """  Splits data to send in different packets

        Arguments:
        int   handle: Identify the packages
        bytes[] data: Data to send to the band """

        remaining = len(data)
        count = 0
        header_size = 11
        mMTU = 23

        while remaining > 0:
            MAX_CHUNKLENGTH = mMTU - 3 - header_size
            copybytes = min(remaining, MAX_CHUNKLENGTH)
            chunk = np.zeros(copybytes + header_size,dtype=np.uint8)

            flags = 0

            if count == 0:
                flags |= 0x01
                chunk[5] = len(data) & 0xff
                chunk[6] = (len(data) >> 8) & 0xff
                chunk[7] = (len(data) >> 16) & 0xff
                chunk[8] = (len(data) >> 24) & 0xff
                chunk[9] = 0x82 & 0xff
                chunk[10] = (0x82 >> 8) & 0xff
            if remaining <= MAX_CHUNKLENGTH:
                flags |= 0x06
            chunk[0] = 0x03
            chunk[1] = flags
            chunk[2] = 0
            chunk[3] = handle
            chunk[4] = count

            chunk[header_size:] = data[len(data) - remaining:len(data) - remaining + copybytes]
            self.charChunkedW.write_value(chunk.tolist())
            remaining -= copybytes
            header_size = 5
            count += 1

    def characteristic_enable_notifications_succeeded(self, characteristic):

        """ Function from gatt-python that is used as callback when
            the notifications are enabled 
            
        Arguments:
        org.bluez.GattCharacteristic1 characteristic: Identify characteristic that now have notif enabled """
        
        if str(characteristic.uuid) == UUIDS.CHARACTERISTIC_CHUNKED_TRANSFER_READ:

            # Whenever the notifications are enabled, send 1st package to the band, starting authentication process
            auth = np.append(np.array([0x04, 0x02, 0x00, 0x02],dtype=np.uint8),self.publicKey.view(dtype=np.uint8))
            print("Sending 1st auth part")
            self.write_chunked_value(self.handle, auth)

    def characteristic_value_updated(self, characteristic, value):

        """ Function from gatt-python that is used as callback when
            a notification is received 
            
        Arguments:
        org.bluez.GattCharacteristic1 characteristic: Identify characteristic that sent notification
        bytes[] value : Value received from the band """

        if str(characteristic.uuid) == UUIDS.CHARACTERISTIC_CHUNKED_TRANSFER_READ:

            # Checks the format of message received
            data = np.frombuffer(value,np.uint8)
            headerSize = 0
            if len(data) > 1 and data[0] == 0x03:
                sequenceNumber = data[4]
                if sequenceNumber == 0 and \
                data[9] == 0x82 and \
                data[10] == 0x00 and \
                data[11] == 0x10 and \
                data[12] == 0x04 and \
                data[13] == 0x01:
                    print("1st auth part done")
                    self.pointer = 0
                    headerSize = 14
                    self.expectedB = data[5] - 3
                elif sequenceNumber > 0:
                    if sequenceNumber != self.lastNumber + 1:
                        print("Unexpected sequence number")
                    headerSize = 5
                elif data[9] == 0x82 and \
                    data[10] == 0x00 and \
                    data[11] == 0x10 and \
                    data[12] == 0x05 and \
                    data[13] == 0x01:
                    print("Successfully authenticated")
                    self.start_hr_measure()
                else:
                    print("Unhandled characteristic change")
                
                bytesToCopy = len(data) - headerSize

                if self.handle == 0:
                    self.reassemble[self.pointer:self.pointer+bytesToCopy] = data[headerSize:]

                self.pointer += len(data) - headerSize
                self.lastNumber = sequenceNumber

                # If the format indicates that the 1st auth part is passed:
                if self.pointer == self.expectedB:

                    remoteRandom = self.reassemble[0:16]
                    remotePublic = self.reassemble[16:64]

                    # Calculate shared key between band and the user
                    self.secretKey = ecdh_shared_secret(self.privateKey, remotePublic.view(dtype=np.uint32))
                    secretKey8 = self.secretKey.view(dtype=np.uint8)

                    secretKey = np.frombuffer(bytes.fromhex(self.authKey), dtype=np.uint8)
                    finalSharedSessionAES = np.zeros(16, dtype=np.uint8)
                    for i in range(16):
                        finalSharedSessionAES[i] = secretKey8[i + 8] ^ secretKey[i]

                    # Use AES encryption and prepare data to send
                    aesCbc1 = AES.new(secretKey.tobytes(), AES.MODE_CBC, iv=bytes([0]*16))
                    out1 = aesCbc1.encrypt(remoteRandom.tobytes())

                    aesCbc2 = AES.new(finalSharedSessionAES.tobytes(), AES.MODE_CBC, iv=bytes([0]*16))
                    out2 = aesCbc2.encrypt(remoteRandom.tobytes())

                    if len(out1) == 16 and len(out2) == 16:
                        command = np.zeros(33, dtype=np.uint8)
                        command[0] = 0x05
                        command[1:17] = np.frombuffer(out1,np.uint8)
                        command[17:33] = np.frombuffer(out2,np.uint8)
                        print("Sending 2nd auth part")
                        self.handle += 1
                        self.write_chunked_value(self.handle, command)

        elif str(characteristic.uuid) == UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE:

            global initialTime
            hRate = int.from_bytes(value,"big")

            # Save received heart rate value and the time of it
            if hRate != 255 and hRate != 0:
                self.hrHist[0].append(hRate)
                self.hrHist[1].append(time.time()-initialTime)

                # Check if the heart rate is decreasing and send alert if needed
                if len(self.hrHist[0]) > 60 and hRate < np.mean(np.array(self.hrHist[0])) - 15:
                    self.send_alert()
        
            print("Heart Rate: " + str(hRate))