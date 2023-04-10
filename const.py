# -----------------------------------------------------------------------------
# Heart Rate Monitor for Mi Band 6 and 7
# -----------------------------------------------------------------------------
# Author: Daniel Oliveira
# https://github.com/danielsousaoliveira
# -----------------------------------------------------------------------------
# Script to store Mi Band constants

___all__ = ['UUIDS']

class Immutable(type):

    def __call__(*args):
        raise Exception("No permission to create instance")

    def __setattr__(*args):
        raise Exception("No permission to modify object")

class UUIDS(object):

    __metaclass__ = Immutable

    BASE = "0000%s-0000-1000-8000-00805f9b34fb"
    CHAR_BASE = "0000%s-0000-3512-2118-0009af100700"

    SERVICE_MIBAND1 = BASE % 'fee0'
    SERVICE_MIBAND2 = BASE % 'fee1'
    SERVICE_ALERT = BASE % '1802'
    SERVICE_ALERT_NOTIFICATION = BASE % '1811'
    SERVICE_HEART_RATE = BASE % '180d'
    SERVICE_DEVICE_INFO = BASE % '180a'

    CHARACTERISTIC_HZ = CHAR_BASE % '0002'
    CHARACTERISTIC_SENSOR = CHAR_BASE % '0001'
    CHARACTERISTIC_AUTH = CHAR_BASE % '0009'
    CHARACTERISTIC_HEART_RATE_MEASURE = BASE % '2a37'
    CHARACTERISTIC_HEART_RATE_CONTROL = BASE % '2a39'
    CHARACTERISTIC_ALERT = BASE % '2a46'
    CHARACTERISTIC_BATTERY = CHAR_BASE % '0006'
    CHARACTERISTIC_STEPS = CHAR_BASE % '0007'
    CHARACTERISTIC_LE_PARAMS = BASE % "ff09"   
    CHARACTERISTIC_CONFIGURATION = CHAR_BASE % '0003'
    CHARACTERISTIC_DEVICEEVENT = CHAR_BASE % '0010'
    CHARACTERISTIC_CURRENT_TIME = BASE % '2a2b'
    CHARACTERISTIC_AGE = BASE % '2a80'
    CHARACTERISTIC_USER_SETTINGS = CHAR_BASE % '0008'
    CHARACTERISTIC_ACTIVITY_DATA = CHAR_BASE % '0005'
    CHARACTERISTIC_FETCH = CHAR_BASE % '0004'
    CHARACTERISTIC_CHUNKED_TRANSFER = CHAR_BASE % '0020'
    CHARACTERISTIC_CHUNKED_TRANSFER_WRITE = CHAR_BASE % '0016'
    CHARACTERISTIC_CHUNKED_TRANSFER_READ = CHAR_BASE % '0017'

    NOTIFICATION_DESCRIPTOR = 0x2902
    CHARACTERISTIC_REVISION = 0x2a28
    CHARACTERISTIC_SERIAL = 0x2a25
    CHARACTERISTIC_HRDW_REVISION = 0x2a27
    ADVERTISEMENT_SERVICE = 0xFEE0

    
