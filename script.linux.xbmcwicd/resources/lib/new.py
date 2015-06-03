#!/usr/bin/python

""" Scriptable command-line interface. """
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import optparse
import dbus
import dbus.service
import sys
from wicd import misc
from wicd.translations import _

misc.RenameProcess('xbmc-wicd')

exit_status = 0

if getattr(dbus, 'version', (0, 0, 0)) < (0, 80, 0):
    import dbus.glib
else:
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

bus = dbus.SystemBus()
try:
    daemon = dbus.Interface(
        bus.get_object('org.wicd.daemon', '/org/wicd/daemon'),
        'org.wicd.daemon'
    )
    wireless = dbus.Interface(
        bus.get_object('org.wicd.daemon', '/org/wicd/daemon/wireless'),
        'org.wicd.daemon.wireless'
    )
    wired = dbus.Interface(
        bus.get_object('org.wicd.daemon', '/org/wicd/daemon/wired'),
        'org.wicd.daemon.wired'
    )
    config = dbus.Interface(
        bus.get_object('org.wicd.daemon', '/org/wicd/daemon/config'),
        'org.wicd.daemon.config'
    )
except dbus.DBusException:
    print 'Error: Could not connect to the daemon. ' + \
        'Please make sure it is running.'
    sys.exit(3)

if not daemon:
    print 'Error connecting to wicd via D-Bus. ' + \
        'Please make sure the wicd service is running.'
    sys.exit(3)


def check_nm(self):
    try:
        import dbus
    except:
        # dbus not available
        err = 30130
        return False, err

    try:
        bus = dbus.SystemBus()
    except:
        # could not connect to dbus
        err =  30131
        return False, err

    try:
        nm_proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
        nm_iface = dbus.Interface(nm_proxy, "org.freedesktop.NetworkManager")
    except:
        # could not connect to network-manager
        err = 30132
        return False, err

    return True, ''

# Test Cases
def numOfNetworks():
    print ("Number of networks: " )
    print( wireless.GetNumberOfNetworks())
def wiredProfileList():
    print ("Wired Profile list: " )
    print( wired.GetWiredProfileList())

def getWirelessNetworks():
    print '#\tBSSID\t\t\tChannel\tESSID'
    for network_id in range(0, wireless.GetNumberOfNetworks()):
        print '%s\t%s\t%s\t%s' % (network_id,
        wireless.GetWirelessProperty(network_id, 'bssid'),
        wireless.GetWirelessProperty(network_id, 'channel'),
        wireless.GetWirelessProperty(network_id, 'essid'))

def connectToWireless(netid):
    check = None
    last = None
    name = wireless.GetWirelessProperty(netid, 'essid')
    encryption = wireless.GetWirelessProperty(netid, 'enctype')
    print "Connecting to %s with %s on %s" % (name, encryption, wireless.DetectWirelessInterface())
    wireless.ConnectWireless(netid)
    if check:
    	while check():
    		next_ = status()
    		if next_ != last:
    			# avoid a race condition where status is updated to "done" after
    			# the loop check
    			if next_ == "done":
    				break
    	print message()
    	last = next_
    print "done!"



def getNetworkStatus():
    status, info = daemon.GetConnectionStatus()
    if status in (misc.WIRED, misc.WIRELESS):
    	connected = True
    	status_msg = _('Connected')
    	if status == misc.WIRED:
    		conn_type = _('Wired')
    	else:
    		conn_type = _('Wireless')
    else:
    	connected = False
    	status_msg = misc._const_status_dict[status]

    print _('Connection status') + ': ' + status_msg
    if connected:
    	print _('Connection type') + ': ' + conn_type
    	if status == misc.WIRELESS:
    		strength = daemon.FormatSignalForPrinting(info[2])
    		print _('Connected to $A at $B (IP: $C)') \
    		.replace('$A', info[1]) \
    		.replace('$B', strength) \
    		.replace('$C', info[0])
    		print _('Network ID: $A') \
    		.replace('$A', info[3])
    	else:
    		print _('Connected to wired network (IP: $A)') \
    		.replace('$A', info[0])
    else:
    	if status == misc.CONNECTING:
    		if info[0] == 'wired':
    			print _('Connecting to wired network.')
    		elif info[0] == 'wireless':
    			print _('Connecting to wireless network "$A".') \
    			.replace('$A', info[1])
#getNetworkStatus()
getWirelessNetworks()
#connectToWireless(1)
