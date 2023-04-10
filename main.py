# -----------------------------------------------------------------------------
# Heart Rate Monitor for Mi Band 6 and 7
# -----------------------------------------------------------------------------
# Author: Daniel Oliveira
# https://github.com/danielsousaoliveira
# -----------------------------------------------------------------------------
# Main script

import sys
import argparse
import time
from dbus.exceptions import DBusException
from band6 import *
from band7 import *
from const import *

# -----------------------------------------------------------------------------
# Interaction with Mi Band Class
# -----------------------------------------------------------------------------

def ping_band(device):

    """ Function to query Heart Rate
        Avoids interruptions while continuously measuring heart rate """
    
    device.ping_hr()
    return True

def main():

    """ Main function
        Creates argument parser to receive MAC address and band type from the user
        Starts connection loop to restore it when lost
        Stops when the user presses keyboard interrupt """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mac',  required=True, help='Mac address of the device')
    parser.add_argument('-b', '--band', required=True, help='Type of Mi Band')
    args = parser.parse_args()
    mac_add = args.mac
    band_type = int(args.band)

    with open("auth_key.txt") as f:
        auth_key = f.read()

    # Initialize device manager
    manager = gatt.DeviceManager(adapter_name='hci0')

    while True:
        try:
            # Try to connect with the device
            if band_type == 6:
                device = MiBand6(mac_address = mac_add, manager = manager)
            elif band_type == 7:
                device = MiBand7(mac_address = mac_add, manager = manager)
            device.connect(auth_key)
            print("Connected")

            # Enable notifications to start authentication process
            device.enable_notifications_chunked()

            # Initialize callback to ping heart rate
            manager.notification_query(ping_band,device)

            # Start GObject loop to continuosly check for notifications
            manager.run()

        except DBusException as e:
            print(f"Failed to connect to device {args.mac}: {e}")
            print("Retrying...\n")
            time.sleep(2)

        except KeyboardInterrupt:
            print("Keyboard interrupt detected. Exiting...")

            # Plot recorded heart rate measures
            device.print_hr()
            device.disconnect()
            manager.stop()
            sys.exit(0)

        except AttributeError as e:
            print("Bluetooth problems found, try to restart your bluetooth")

if __name__ == "__main__":
    main()

