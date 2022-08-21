***********
OSD Service
***********
.. _device management: ../rados/operations/devices
.. _libstoragemgmt: https://github.com/libstorage/libstoragemgmt

List Devices
============

``ceph-volume`` scans each cluster in the host from time to time in order
to determine which devices are present and whether they are eligible to be
used as OSDs.

To print a list of devices discovered by ``cephadm``, run this command:

.. prompt:: bash #

    ceph orch device ls [--hostname=...] [--wide] [--refresh]

Example
::

  Hostname  Path      Type  Serial              Size   Health   Ident  Fault  Available
  srv-01    /dev/sdb  hdd   15P0A0YFFRD6         300G  Unknown  N/A    N/A    No
  srv-01    /dev/sdc  hdd   15R0A08WFRD6         300G  Unknown  N/A    N/A    No
  srv-01    /dev/sdd  hdd   15R0A07DFRD6         300G  Unknown  N/A    N/A    No
  srv-01    /dev/sde  hdd   15P0A0QDFRD6         300G  Unknown  N/A    N/A    No
  srv-02    /dev/sdb  hdd   15R0A033FRD6         300G  Unknown  N/A    N/A    No
  srv-02    /dev/sdc  hdd   15R0A05XFRD6         300G  Unknown  N/A    N/A    No
  srv-02    /dev/sde  hdd   15R0A0ANFRD6         300G  Unknown  N/A    N/A    No
  srv-02    /dev/sdf  hdd   15R0A06EFRD6         300G  Unknown  N/A    N/A    No
  srv-03    /dev/sdb  hdd   15R0A0OGFRD6         300G  Unknown  N/A    N/A    No
  srv-03    /dev/sdc  hdd   15R0A0P7FRD6         300G  Unknown  N/A    N/A    No
  srv-03    /dev/sdd  hdd   15R0A0O7FRD6         300G  Unknown  N/A    N/A    No

Using the ``--wide`` option provides all details relating to the device,
including any reasons that the device might not be eligible for use as an OSD.

In the above example you can see fields named "Health", "Ident", and "Fault".
This information is provided by integration with `libstoragemgmt`_. By default,
this integration is disabled (because `libstoragemgmt`_ may not be 100%
compatible with your hardware).  To make ``cephadm`` include these fields,
enable cephadm's "enhanced device scan" option as follows;

.. prompt:: bash #

    ceph config set mgr mgr/cephadm/device_enhanced_scan true

.. warning::
    Although the libstoragemgmt library performs standard SCSI inquiry calls,
    there is no guarantee that your firmware fully implements these standards.
    This can lead to erratic behaviour and even bus resets on some older
    hardware. It is therefore recommended that, before enabling this feature,
    you test your hardware's compatibility with libstoragemgmt first to avoid
    unplanned interruptions to services.

    There are a number of ways to test compatibility, but the simplest may be
    to use the cephadm shell to call libstoragemgmt directly - ``cephadm shell
    lsmcli ldl``. If your hardware is supported you should see something like
    this: 

    ::

      Path     | SCSI VPD 0x83    | Link Type | Serial Number      | Health Status
      ----------------------------------------------------------------------------
      /dev/sda | 50000396082ba631 | SAS       | 15P0A0R0FRD6       | Good
      /dev/sdb | 50000396082bbbf9 | SAS       | 15P0A0YFFRD6       | Good


After you have enabled libstoragemgmt support, the output will look something
like this:

::

  # ceph orch device ls
  Hostname   Path      Type  Serial              Size   Health   Ident  Fault  Available
  srv-01     /dev/sdb  hdd   15P0A0YFFRD6         300G  Good     Off    Off    No
  srv-01     /dev/sdc  hdd   15R0A08WFRD6         300G  Good     Off    Off    No
  :

In this example, libstoragemgmt has confirmed the health of the drives and the ability to
interact with the Identification and Fault LEDs on the drive enclosures. For further
information about interacting with these LEDs, refer to `device management`_.

.. note::
    The current release of `libstoragemgmt`_ (1.8.8) supports SCSI, SAS, and SATA based
    local disks only. There is no official support for NVMe devices (PCIe)

.. _cephadm-deploy-osds:

Deploy OSDs
===========

Listing Storage Devices
-----------------------

In order to deploy an OSD, there must be a storage device that is *available* on
which the OSD will be deployed.

Run this command to display an inventory of storage devices on all cluster hosts:

.. prompt:: bash #

  ceph orch device ls

A storage device is considered *available* if all of the following
conditions are met:

* The device must have no partitions.
* The device must not have any LVM state.
* The device must not be mounted.
* The device must not contain a file system.
* The device must not contain a Ceph BlueStore OSD.
* The device must be larger than 5 GB.

Ceph will not provision an OSD on a device that is not available.

Creating New OSDs
-----------------

There are a few ways to create new OSDs:

* Tell Ceph to consume any available and unused storage device:

  .. prompt:: bash #

    ceph orch apply osd --all-available-devices

* Create an OSD from a specific device on a specific host:

  .. prompt:: bash #

    ceph orch daemon add osd *<host>*:*<device-path>*

  For example:

  .. prompt:: bash #

    ceph orch daemon add osd host1:/dev/sdb

* You can use :ref:`drivegroups` to categorize device(s) based on their
  properties. This might be useful in forming a clearer picture of which
  devices are available to consume. Properties include device type (SSD or
  HDD), device model names, size, and the hosts on which the devices exist:

  .. prompt:: bash #

    ceph orch apply -i spec.yml

Dry Run
-------

The ``--dry-run`` flag causes the orchestrator to present a preview of what
will happen without actually creating the OSDs.

For example:

   .. prompt:: bash #

     ceph orch apply osd --all-available-devices --dry-run

   ::

     NAME                  HOST  DATA      DB  WAL
     all-available-devices node1 /dev/vdb  -   -
     all-available-devices node2 /dev/vdc  -   -
     all-available-devices node3 /dev/vdd  -   -

.. _cephadm-osd-declarative:

Declarative State
-----------------

The effect of ``ceph orch apply`` is persistent. This means that drives that
are added to the system after the ``ceph orch apply`` command completes will be
automatically found and added to the cluster.  It also means that drives that
become available (by zapping, for example) after the ``ceph orch apply``
command completes will be automatically found and added to the cluster.

We will examine the effects of the following command:

   .. prompt:: bash #

     ceph orch apply osd --all-available-devices

After running the above command: 

* If you add new disks to the cluster, they will automatically be used to
  create new OSDs.
* If you remove an OSD and clean the LVM physical volume, a new OSD will be
  created automatically.

To disable the automatic creation of OSD on available devices, use the
``unmanaged`` parameter:

If you want to avoid this behavior (disable automatic creation of OSD on available devices), use the ``unmanaged`` parameter:

.. prompt:: bash #

   ceph orch apply osd --all-available-devices --unmanaged=true

.. note::

  Keep these three facts in mind:

  - The default behavior of ``ceph orch apply`` causes cephadm constantly to reconcile. This means that cephadm creates OSDs as soon as new drives are detected.

  - Setting ``unmanaged: True`` disables the creation of OSDs. If ``unmanaged: True`` is set, nothing will happen even if you apply a new OSD service.

  - ``ceph orch daemon add`` creates OSDs, but does not add an OSD service.

* For cephadm, see also :ref:`cephadm-spec-unmanaged`.


Remove an OSD
=============

Removing an OSD from a cluster involves two steps:

#. evacuating all placement groups (PGs) from the cluster
#. removing the PG-free OSD from the cluster

The following command performs these two steps:

.. prompt:: bash #

  ceph orch osd rm <osd_id(s)> [--replace] [--force]

Example:

.. prompt:: bash #

  ceph orch osd rm 0

Expected output::

   Scheduled OSD(s) for removal

OSDs that are not safe to destroy will be rejected.

Monitoring OSD State
--------------------

You can query the state of OSD operation with the following command:

.. prompt:: bash #

   ceph orch osd rm status

Expected output::

    OSD_ID  HOST         STATE                    PG_COUNT  REPLACE  FORCE  STARTED_AT
    2       cephadm-dev  done, waiting for purge  0         True     False  2020-07-17 13:01:43.147684
    3       cephadm-dev  draining                 17        False    True   2020-07-17 13:01:45.162158
    4       cephadm-dev  started                  42        False    True   2020-07-17 13:01:45.162158


When no PGs are left on the OSD, it will be decommissioned and removed from the cluster.

.. note::
    After removing an OSD, if you wipe the LVM physical volume in the device used by the removed OSD, a new OSD will be created.
    For more information on this, read about the ``unmanaged`` parameter in :ref:`cephadm-osd-declarative`.

Stopping OSD Removal
--------------------

It is possible to stop queued OSD removals by using the following command:

.. prompt:: bash #

  ceph orch osd rm stop <svc_id(s)>

Example:

.. prompt:: bash #

    ceph orch osd rm stop 4

Expected output::

    Stopped OSD(s) removal

This resets the initial state of the OSD and takes it off the removal queue.


Replacing an OSD
----------------

.. prompt:: bash #

  orch osd rm <svc_id(s)> --replace [--force]

Example:

.. prompt:: bash #

  ceph orch osd rm 4 --replace

Expected output::

   Scheduled OSD(s) for replacement

This follows the same procedure as the procedure in the "Remove OSD" section, with
one exception: the OSD is not permanently removed from the CRUSH hierarchy, but is
instead assigned a 'destroyed' flag.

**Preserving the OSD ID**

The 'destroyed' flag is used to determine which OSD ids will be reused in the
next OSD deployment.

If you use OSDSpecs for OSD deployment, your newly added disks will be assigned
the OSD ids of their replaced counterparts. This assumes that the new disks
still match the OSDSpecs.

Use the ``--dry-run`` flag to make certain that the ``ceph orch apply osd`` 
command does what you want it to. The ``--dry-run`` flag shows you what the
outcome of the command will be without making the changes you specify. When
you are satisfied that the command will do what you want, run the command
without the ``--dry-run`` flag.

.. tip::

  The name of your OSDSpec can be retrieved with the command ``ceph orch ls``

Alternatively, you can use your OSDSpec file:

.. prompt:: bash #

  ceph orch apply osd -i <osd_spec_file> --dry-run

Expected output::

  NAME                  HOST  DATA     DB WAL
  <name_of_osd_spec>    node1 /dev/vdb -  -


When this output reflects your intention, omit the ``--dry-run`` flag to
execute the deployment.


Erasing Devices (Zapping Devices)
---------------------------------

Erase (zap) a device so that it can be reused. ``zap`` calls ``ceph-volume
zap`` on the remote host.

.. prompt:: bash #

  orch device zap <hostname> <path>

Example command:

.. prompt:: bash #

  ceph orch device zap my_hostname /dev/sdx

.. note::
    If the unmanaged flag is unset, cephadm automatically deploys drives that
    match the DriveGroup in your OSDSpec.  For example, if you use the
    ``all-available-devices`` option when creating OSDs, when you ``zap`` a
    device the cephadm orchestrator automatically creates a new OSD in the
    device.  To disable this behavior, see :ref:`cephadm-osd-declarative`.


.. _drivegroups:

Advanced OSD Service Specifications
===================================

:ref:`orchestrator-cli-service-spec` of type ``osd`` are a way to describe a cluster layout using the properties of disks.
It gives the user an abstract way tell ceph which disks should turn into an OSD
with which configuration without knowing the specifics of device names and paths.

Instead of doing this

.. prompt:: bash [monitor.1]#

  ceph orch daemon add osd *<host>*:*<path-to-device>*

for each device and each host, we can define a yaml|json file that allows us to describe
the layout. Here's the most basic example.

Create a file called i.e. osd_spec.yml

.. code-block:: yaml

    service_type: osd
    service_id: default_drive_group  <- name of the drive_group (name can be custom)
    placement:
      host_pattern: '*'              <- which hosts to target, currently only supports globs
    data_devices:                    <- the type of devices you are applying specs to
      all: true                      <- a filter, check below for a full list

This would translate to:

Turn any available(ceph-volume decides what 'available' is) into an OSD on all hosts that match
the glob pattern '*'. (The glob pattern matches against the registered hosts from `host ls`)
There will be a more detailed section on host_pattern down below.

and pass it to `osd create` like so

.. prompt:: bash [monitor.1]#

  ceph orch apply osd -i /path/to/osd_spec.yml

This will go out on all the matching hosts and deploy these OSDs.

Since we want to have more complex setups, there are more filters than just the 'all' filter.

Also, there is a `--dry-run` flag that can be passed to the `apply osd` command, which gives you a synopsis
of the proposed layout.

Example

.. prompt:: bash [monitor.1]#

  [monitor.1]# ceph orch apply osd -i /path/to/osd_spec.yml --dry-run



Filters
-------

.. note::
   Filters are applied using a `AND` gate by default. This essentially means that a drive needs to fulfill all filter
   criteria in order to get selected.
   If you wish to change this behavior you can adjust this behavior by setting

    `filter_logic: OR`  # valid arguments are `AND`, `OR`

   in the OSD Specification.

You can assign disks to certain groups by their attributes using filters.

The attributes are based off of ceph-volume's disk query. You can retrieve the information
with

.. code-block:: bash

  ceph-volume inventory </path/to/disk>

Vendor or Model:
^^^^^^^^^^^^^^^^

You can target specific disks by their Vendor or by their Model

.. code-block:: yaml

    model: disk_model_name

or

.. code-block:: yaml

    vendor: disk_vendor_name


Size:
^^^^^

You can also match by disk `Size`.

.. code-block:: yaml

    size: size_spec

Size specs:
___________

Size specification of format can be of form:

* LOW:HIGH
* :HIGH
* LOW:
* EXACT

Concrete examples:

Includes disks of an exact size

.. code-block:: yaml

    size: '10G'

Includes disks which size is within the range

.. code-block:: yaml

    size: '10G:40G'

Includes disks less than or equal to 10G in size

.. code-block:: yaml

    size: ':10G'


Includes disks equal to or greater than 40G in size

.. code-block:: yaml

    size: '40G:'

Sizes don't have to be exclusively in Gigabyte(G).

Supported units are Megabyte(M), Gigabyte(G) and Terrabyte(T). Also appending the (B) for byte is supported. MB, GB, TB


Rotational:
^^^^^^^^^^^

This operates on the 'rotational' attribute of the disk.

.. code-block:: yaml

    rotational: 0 | 1

`1` to match all disks that are rotational

`0` to match all disks that are non-rotational (SSD, NVME etc)


All:
^^^^

This will take all disks that are 'available'

Note: This is exclusive for the data_devices section.

.. code-block:: yaml

    all: true


Limiter:
^^^^^^^^

When you specified valid filters but want to limit the amount of matching disks you can use the 'limit' directive.

.. code-block:: yaml

    limit: 2

For example, if you used `vendor` to match all disks that are from `VendorA` but only want to use the first two
you could use `limit`.

.. code-block:: yaml

  data_devices:
    vendor: VendorA
    limit: 2

Note: Be aware that `limit` is really just a last resort and shouldn't be used if it can be avoided.


Additional Options
------------------

There are multiple optional settings you can use to change the way OSDs are deployed.
You can add these options to the base level of a DriveGroup for it to take effect.

This example would deploy all OSDs with encryption enabled.

.. code-block:: yaml

    service_type: osd
    service_id: example_osd_spec
    placement:
      host_pattern: '*'
    data_devices:
      all: true
    encrypted: true

See a full list in the DriveGroupSpecs

.. py:currentmodule:: ceph.deployment.drive_group

.. autoclass:: DriveGroupSpec
   :members:
   :exclude-members: from_json

Examples
--------

The simple case
^^^^^^^^^^^^^^^

All nodes with the same setup

.. code-block:: none

    20 HDDs
    Vendor: VendorA
    Model: HDD-123-foo
    Size: 4TB

    2 SSDs
    Vendor: VendorB
    Model: MC-55-44-ZX
    Size: 512GB

This is a common setup and can be described quite easily:

.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_default
    placement:
      host_pattern: '*'
    data_devices:
      model: HDD-123-foo <- note that HDD-123 would also be valid
    db_devices:
      model: MC-55-44-XZ <- same here, MC-55-44 is valid

However, we can improve it by reducing the filters on core properties of the drives:

.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_default
    placement:
      host_pattern: '*'
    data_devices:
      rotational: 1
    db_devices:
      rotational: 0

Now, we enforce all rotating devices to be declared as 'data devices' and all non-rotating devices will be used as shared_devices (wal, db)

If you know that drives with more than 2TB will always be the slower data devices, you can also filter by size:

.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_default
    placement:
      host_pattern: '*'
    data_devices:
      size: '2TB:'
    db_devices:
      size: ':2TB'

Note: All of the above DriveGroups are equally valid. Which of those you want to use depends on taste and on how much you expect your node layout to change.


The advanced case
^^^^^^^^^^^^^^^^^

Here we have two distinct setups

.. code-block:: none

    20 HDDs
    Vendor: VendorA
    Model: HDD-123-foo
    Size: 4TB

    12 SSDs
    Vendor: VendorB
    Model: MC-55-44-ZX
    Size: 512GB

    2 NVMEs
    Vendor: VendorC
    Model: NVME-QQQQ-987
    Size: 256GB


* 20 HDDs should share 2 SSDs
* 10 SSDs should share 2 NVMes

This can be described with two layouts.

.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_hdd
    placement:
      host_pattern: '*'
    data_devices:
      rotational: 0
    db_devices:
      model: MC-55-44-XZ
      limit: 2 (db_slots is actually to be favoured here, but it's not implemented yet)
    ---
    service_type: osd
    service_id: osd_spec_ssd
    placement:
      host_pattern: '*'
    data_devices:
      model: MC-55-44-XZ
    db_devices:
      vendor: VendorC

This would create the desired layout by using all HDDs as data_devices with two SSD assigned as dedicated db/wal devices.
The remaining SSDs(8) will be data_devices that have the 'VendorC' NVMEs assigned as dedicated db/wal devices.

The advanced case (with non-uniform nodes)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The examples above assumed that all nodes have the same drives. That's however not always the case.

Node1-5

.. code-block:: none

    20 HDDs
    Vendor: Intel
    Model: SSD-123-foo
    Size: 4TB
    2 SSDs
    Vendor: VendorA
    Model: MC-55-44-ZX
    Size: 512GB

Node6-10

.. code-block:: none

    5 NVMEs
    Vendor: Intel
    Model: SSD-123-foo
    Size: 4TB
    20 SSDs
    Vendor: VendorA
    Model: MC-55-44-ZX
    Size: 512GB

You can use the 'host_pattern' key in the layout to target certain nodes. Salt target notation helps to keep things easy.


.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_node_one_to_five
    placement:
      host_pattern: 'node[1-5]'
    data_devices:
      rotational: 1
    db_devices:
      rotational: 0
    ---
    service_type: osd
    service_id: osd_spec_six_to_ten
    placement:
      host_pattern: 'node[6-10]'
    data_devices:
      model: MC-55-44-XZ
    db_devices:
      model: SSD-123-foo

This applies different OSD specs to different hosts depending on the `host_pattern` key.

Dedicated wal + db
^^^^^^^^^^^^^^^^^^

All previous cases co-located the WALs with the DBs.
It's however possible to deploy the WAL on a dedicated device as well, if it makes sense.

.. code-block:: none

    20 HDDs
    Vendor: VendorA
    Model: SSD-123-foo
    Size: 4TB

    2 SSDs
    Vendor: VendorB
    Model: MC-55-44-ZX
    Size: 512GB

    2 NVMEs
    Vendor: VendorC
    Model: NVME-QQQQ-987
    Size: 256GB


The OSD spec for this case would look like the following (using the `model` filter):

.. code-block:: yaml

    service_type: osd
    service_id: osd_spec_default
    placement:
      host_pattern: '*'
    data_devices:
      model: MC-55-44-XZ
    db_devices:
      model: SSD-123-foo
    wal_devices:
      model: NVME-QQQQ-987


It is also possible to specify directly device paths in specific hosts like the following:

.. code-block:: yaml

    service_type: osd
    service_id: osd_using_paths
    placement:
      hosts:
        - Node01
        - Node02
    data_devices:
      paths:
        - /dev/sdb
    db_devices:
      paths:
        - /dev/sdc
    wal_devices:
      paths:
        - /dev/sdd


This can easily be done with other filters, like `size` or `vendor` as well.

Activate existing OSDs
======================

In case the OS of a host was reinstalled, existing OSDs need to be activated
again. For this use case, cephadm provides a wrapper for :ref:`ceph-volume-lvm-activate` that
activates all existing OSDs on a host.

.. prompt:: bash #

   ceph cephadm osd activate <host>...

This will scan all existing disks for OSDs and deploy corresponding daemons.
