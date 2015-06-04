import sys
import xbmc
import xbmcaddon
import xbmcgui
#import qfpynm
import time
import new
import optparse
import dbus
import dbus.service

from wicd import misc
from wicd.translations import _
#enable localization
getLS   = sys.modules[ "__main__" ].__language__
__cwd__ = sys.modules[ "__main__" ].__cwd__


#Longer term
#TODO Build a service that monitor state and display a notification about changes
#TODO Display network detail window
#TODO Create a new con name if name=ssid is taken
#TODO the > only indicates active connection. would be nice to show connectivity status as well
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

def getWirelessNetworks():
    print '#\tBSSID\t\t\tChannel\tESSID'
    for network_id in range(0, wireless.GetNumberOfNetworks()):
        print '%s\t%s\t%s\t%s' % (network_id,
        wireless.GetWirelessProperty(network_id, 'bssid'),
        wireless.GetWirelessProperty(network_id, 'channel'),
        wireless.GetWirelessProperty(network_id, 'essid'))
    return int(wireless.GetNumberOfNetworks())

def get_connections():
    print("get_connections")
    connection_list = []
    for network_id in range(0, wireless.GetNumberOfNetworks()):
        connection_dict = {}
        connection_dict['uuid'] = wireless.GetWirelessProperty(network_id, 'bssid')
        connection_dict['id'] = network_id
        connection_dict['ssid'] = wireless.GetWirelessProperty(network_id, 'essid')
        connection_list.append(connection_dict)
    return (connection_list)

class GUI(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.msg = kwargs['msg']
        self.first = kwargs['first']
        self.doModal()


    def onInit(self):
        self.defineControls()

        self.status_label.setLabel(self.msg)

        self.showDialog()

        if self.first == True:
            nm_OK, err = self.check_nm()
            if nm_OK == True:
                devlist = getWirelessNetworks()
                if len(devlist) > 1:
                    self.msg = getLS(30127)
                elif len(devlist) == 0:
                    self.msg = getLS(30128)
            else:
                self.msg = getLS(err)

        self.status_label.setLabel(self.msg)

        #self.disconnect_button.setEnabled(False)
        #self.delete_button.setEnabled(False)

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
            nm_proxy = bus.get_object("org.wicd.daemon", "/org/wicd/daemon")
            nm_iface = dbus.Interface(nm_proxy, "org.wicd.daemon")
        except:
            # could not connect to network-manager
            err = 30132
            return False, err

        return True, ''

    def defineControls(self):
        #actions
        self.action_cancel_dialog = (9, 10)
        #control ids
        self.control_heading_label_id         = 2
        self.control_list_label_id            = 3
        self.control_list_id                  = 10
        self.control_delete_button_id           = 11
        self.control_disconnect_button_id     = 13
        self.control_add_connection_button_id = 14
        self.control_status_button_id           = 15
        self.control_install_button_id        = 18
        self.control_cancel_button_id         = 19
        self.control_status_label_id          = 100

        #controls
        self.heading_label      = self.getControl(self.control_heading_label_id)
        self.list_label         = self.getControl(self.control_list_label_id)
        self.list               = self.getControl(self.control_list_id)
        self.delete_button        = self.getControl(self.control_delete_button_id)
        self.control_add_connection_button = self.getControl(self.control_add_connection_button_id)
        self.status_button        = self.getControl(self.control_status_button_id)
        self.disconnect_button  = self.getControl(self.control_disconnect_button_id)
        self.install_button     = self.getControl(self.control_install_button_id)
        self.cancel_button      = self.getControl(self.control_cancel_button_id)
        self.status_label       = self.getControl(self.control_status_label_id)

    def showDialog(self):
        print("showDialog")
        self.updateList()
        #state,stateTXT = new.get_nm_state()
        #msg = stateTXT
        #self.status_label.setLabel(msg)

    def closeDialog(self):
        self.close()

    def onClick(self, controlId):
        self.msg = ""
        self.status_label.setLabel(self.msg)

        #Activate connection from list
        if controlId == self.control_list_id:
            #position = self.list.getSelectedPosition()

            #Get UUID
            item = self.list.getSelectedItem()

            uuid =  item.getProperty('uuid')
            encryption = item.getProperty('encryption')
            #print uuid

            self.activate_connection(uuid)
            for i in range(1, 100):
                state,stateTXT = new.get_device_state(new.get_wifi_device())
                msg = stateTXT
                self.status_label.setLabel(msg)
                if (state == 100 and i >2):
                    break
                if (i > 2 and state == 60):
                    if encryption not in ['WPA','WEP']:
                        print ("Strange encryption:" + encryption)
                        break
                    #Prompt for key
                    key = ""
                    kb = xbmc.Keyboard("", getLS(30104), False)
                    kb.doModal()
                    if (kb.isConfirmed()):
                        key=kb.getText()
                        errors = new.validate_wifi_input(key,encryption)

                    if key == "" or errors != '':
                        self.msg = getLS(30109)
                        self.status_label.setLabel(self.msg)
                        break

                    new.update_wifi(uuid, key, encryption)
                    new.connectToWireless(uuid)
                    continue
                time.sleep(1)
                msg = ''
                self.status_label.setLabel(msg)
                time.sleep(1)
            if state == 100:
                msg = getLS(30120) #"Connected!"

            elif state == 60:
                msg = getLS(30121) #"Not Autorized!"
            else:
                msg = getLS(30122) #"Connection failed"
            self.updateList()
            self.status_label.setLabel(msg)

        #Add connection button
        elif controlId == self.control_add_connection_button_id:
            import addConnection
            addConnectionUI = addConnection.GUI("script_linux_xbmcwicd-add.xml", __cwd__, "default")
            self.close()
            del addConnectionUI

        #disconnect button
        elif controlId == self.control_disconnect_button_id:
            self.disconnect()

            for i in range(1, 20):
                state,stateTXT = new.get_device_state(new.get_wifi_device())
                self.msg = stateTXT
                self.status_label.setLabel(self.msg)

                if (state == 30):
                    break
                time.sleep(1)
            self.updateList()

        #Delete button
        elif controlId == self.control_delete_button_id:
            item = self.list.getSelectedItem()

            uuid =  item.getProperty('uuid')

            self.delete_connection(uuid)

            msg = getLS(30115) #Refreshing
            self.status_label.setLabel(msg)

            time.sleep(2)
            self.updateList()

            msg = getLS(30126) #Done
            self.status_label.setLabel(msg)
            self.setFocus(self.control_add_connection_button)

        #Status button
        elif controlId == self.control_status_button_id:
            state,stateTXT = new.getNetworkStatus()
            msg = stateTXT
            self.status_label.setLabel(msg)

        #cancel dialog
        elif controlId == self.control_cancel_button_id:
            self.closeDialog()

    def onAction(self, action):
        if action in self.action_cancel_dialog:
            self.closeDialog()

    def onFocus(self, controlId):
        msg = ""
        if hasattr(self, 'status_label'):
            self.status_label.setLabel(msg)

    def disconnect(self):
        new.deactive_wifi()

    def activate_connection(self,uuid):
        new.activate_connection(uuid)

    def delete_connection(self,uuid):
        new.delete_connection(uuid)

    def updateList(self):
        print "updating list"
        #self.list.reset()
        print(get_connections())
        connection_list = get_connections()

        for  connection_dict in connection_list:
            item = xbmcgui.ListItem (label=str(connection_dict['id']))
            item.setProperty('ssid',connection_dict['ssid'])
            item.setProperty('uuid',connection_dict['uuid'])
            self.list.addItem(item)
