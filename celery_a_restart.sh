#!/bin/sh

echo "restart A"

/etc/init.d/celeryd_a restart
/etc/init.d/celerybeat_a restart
/etc/init.d/celeryevcam_a restart
