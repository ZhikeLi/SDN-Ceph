Client Configuration
====================

Updating Client Configuration
-----------------------------

Certain client configurations can be applied at runtime. To check if a configuration option can be applied (taken into affect by a client) at runtime, use the `config help` command::

   ceph config help debug_client
    debug_client - Debug level for client
    (str, advanced)                                                                                                                      Default: 0/5
    Can update at runtime: true

    The value takes the form 'N' or 'N/M' where N and M are values between 0 and 99.  N is the debug level to log (all values below this are included), and M is the level to gather and buffer in memory.  In the event of a crash, the most recent items <= M are dumped to the log file.

`config help` tells if a given configuration can be applied at runtime along with the defaults and a description of the configuration option.

To update a configuration option at runtime, use the `config set` command::

   ceph config set client debug_client 20/20

Note that this changes a given configuration for all clients.

To check configured options use the `config get` command::

   ceph config get client
    WHO    MASK LEVEL    OPTION                    VALUE     RO 
    client      advanced debug_client              20/20          
    global      advanced osd_pool_default_min_size 1            
    global      advanced osd_pool_default_size     3            

Client Config Reference
------------------------

``client_acl_type``

:Description: Set the ACL type. Currently, only possible value is ``"posix_acl"`` to enable POSIX ACL, or an empty string. This option only takes effect when the ``fuse_default_permissions`` is set to ``false``.

:Type: String
:Default: ``""`` (no ACL enforcement)

``client_cache_mid``

:Description: Set client cache midpoint. The midpoint splits the least recently used lists into a hot and warm list.
:Type: Float
:Default: ``0.75``

``client_cache_size``

:Description: Set the number of inodes that the client keeps in the metadata cache.
:Type: Integer
:Default: ``16384``

``client_caps_release_delay``

:Description: Set the delay between capability releases in seconds. The delay sets how many seconds a client waits to release capabilities that it no longer needs in case the capabilities are needed for another user space operation.
:Type: Integer
:Default: ``5`` (seconds)

``client_debug_force_sync_read``

:Description: If set to ``true``, clients read data directly from OSDs instead of using a local page cache.
:Type: Boolean
:Default: ``false``

``client_dirsize_rbytes``

:Description: If set to ``true``, use the recursive size of a directory (that is, total of all descendants).
:Type: Boolean
:Default: ``true``

``client_max_inline_size``

:Description: Set the maximum size of inlined data stored in a file inode rather than in a separate data object in RADOS. This setting only applies if the ``inline_data`` flag is set on the MDS map.
:Type: Integer
:Default: ``4096``

``client_metadata``

:Description: Comma-delimited strings for client metadata sent to each MDS, in addition to the automatically generated version, host name, and other metadata.
:Type: String
:Default: ``""`` (no additional metadata)

``client_mount_gid``

:Description: Set the group ID of CephFS mount.
:Type: Integer
:Default: ``-1``

``client_mount_timeout``

:Description: Set the timeout for CephFS mount in seconds.
:Type: Float
:Default: ``300.0``

``client_mount_uid``

:Description: Set the user ID of CephFS mount.
:Type: Integer
:Default: ``-1``

``client_mountpoint``

:Description: Directory to mount on the CephFS file system. An alternative to the ``-r`` option of the ``ceph-fuse`` command.
:Type: String
:Default: ``"/"``

``client_oc``

:Description: Enable object caching.
:Type: Boolean
:Default: ``true``

``client_oc_max_dirty``

:Description: Set the maximum number of dirty bytes in the object cache.
:Type: Integer
:Default: ``104857600`` (100MB)

``client_oc_max_dirty_age``

:Description: Set the maximum age in seconds of dirty data in the object cache before writeback.
:Type: Float
:Default: ``5.0`` (seconds)

``client_oc_max_objects``

:Description: Set the maximum number of objects in the object cache.
:Type: Integer
:Default: ``1000``

``client_oc_size``

:Description: Set how many bytes of data will the client cache.
:Type: Integer
:Default: ``209715200`` (200 MB)

``client_oc_target_dirty``

:Description: Set the target size of dirty data. We recommend to keep this number low.
:Type: Integer
:Default: ``8388608`` (8MB)

``client_permissions``

:Description: Check client permissions on all I/O operations.
:Type: Boolean
:Default: ``true``

``client_quota``

:Description: Enable client quota checking if set to ``true``.
:Type: Boolean
:Default: ``true``

``client_quota_df``

:Description: Report root directory quota for the ``statfs`` operation.
:Type: Boolean
:Default: ``true``

``client_readahead_max_bytes``

:Description: Set the maximum number of bytes that the client reads ahead for future read operations. Overridden by the ``client_readahead_max_periods`` setting.
:Type: Integer
:Default: ``0`` (unlimited)

``client_readahead_max_periods``

:Description: Set the number of file layout periods (object size * number of stripes) that the client reads ahead. Overrides the ``client_readahead_max_bytes`` setting.
:Type: Integer
:Default: ``4``

``client_readahead_min``

:Description: Set the minimum number bytes that the client reads ahead.
:Type: Integer
:Default: ``131072`` (128KB)

``client_reconnect_stale``

:Description: Automatically reconnect stale session.
:Type: Boolean
:Default: ``false``

``client_snapdir``

:Description: Set the snapshot directory name.
:Type: String
:Default: ``".snap"``

``client_tick_interval``

:Description: Set the interval in seconds between capability renewal and other upkeep.
:Type: Float
:Default: ``1.0`` (seconds)

``client_use_random_mds``

:Description: Choose random MDS for each request.
:Type: Boolean
:Default: ``false``

``fuse_default_permissions``

:Description: When set to ``false``, ``ceph-fuse`` utility checks does its own permissions checking, instead of relying on the permissions enforcement in FUSE. Set to ``false`` together with the ``client acl type=posix_acl`` option to enable POSIX ACL.
:Type: Boolean
:Default: ``true``

``fuse_max_write``

:Description: Set the maximum number of bytes in a single write operation.
              A value of 0 indicates no change; the
              FUSE default of 128 kbytes remains in force.
:Type: Integer
:Default: ``0``

``fuse_disable_pagecache``

:Description: If set to ``true``, kernel page cache is disabled for ``ceph-fuse``
              mounts. When multiple clients read/write to a file at the same
              time, readers may get stale data from page cache. Due to
              limitations of FUSE, ``ceph-fuse`` can't disable page cache dynamically.
:Type: Boolean
:Default: ``false``

Developer Options
#################

.. important:: These options are internal. They are listed here only to complete the list of options.

``client_debug_getattr_caps``

:Description: Check if the reply from the MDS contains required capabilities.
:Type: Boolean
:Default: ``false``

``client_debug_inject_tick_delay``

:Description: Add artificial delay between client ticks.
:Type: Integer
:Default: ``0``

``client_inject_fixed_oldest_tid``

:Description:
:Type: Boolean
:Default: ``false``

``client_inject_release_failure``

:Description:
:Type: Boolean
:Default: ``false``

``client_trace``

:Description: The path to the trace file for all file operations. The output is designed to be used by the Ceph `synthetic client <../../man/8/ceph-syn>`_.
:Type: String
:Default: ``""`` (disabled)

