#!/bin/sh -ex

cwd=`pwd`
cat > conf <<EOF
[mon]
admin socket = 
EOF

rm -f mm
monmaptool --create mm \
    --add a 127.0.0.1:6789 \
    --add b 127.0.0.1:6790 \
    --add c 127.0.0.1:6791

rm -f keyring
ceph-authtool --create-keyring keyring --gen-key -n client.admin
ceph-authtool keyring --gen-key -n mon.

ceph-mon -c conf -i a --mkfs --monmap mm --mon-data $cwd/mon.a -k keyring
ceph-mon -c conf -i b --mkfs --monmap mm --mon-data $cwd/mon.b -k keyring
ceph-mon -c conf -i c --mkfs --monmap mm --mon-data $cwd/mon.c -k keyring

ceph-mon -c conf -i a --mon-data $cwd/mon.a
ceph-mon -c conf -i c --mon-data $cwd/mon.b
ceph-mon -c conf -i b --mon-data $cwd/mon.c

ceph -c conf -k keyring --monmap mm health

## expand via a kludged monmap
monmaptool mm --add d 127.0.0.1:6792
ceph-mon -c conf -i d --mkfs --monmap mm --mon-data $cwd/mon.d -k keyring
ceph-mon -c conf -i d --mon-data $cwd/mon.d

while true; do
    ceph -c conf -k keyring --monmap mm health
    if ceph -c conf -k keyring --monmap mm mon stat | grep d=; then
	break
    fi
    sleep 1
done

killall ceph-mon

echo OK
