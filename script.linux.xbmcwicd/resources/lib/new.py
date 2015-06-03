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
