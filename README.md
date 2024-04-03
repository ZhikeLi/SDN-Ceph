# SDN-Ceph
In Software Defined Network(SDN), we propose An Adaptive Read/Write Optimized Algorithm for Ceph Heterogeneous Systems via Performance Prediction and Multi-attribute Decision-making


## Step 1: Deploy the SDN network environment of the cluster.

Environment: Ubuntu20.04

1. Let's download the original RYU controller

Execute the command: pip install ryu

2. We modified the source code of RYU controller to obtain the new version RYU_M1.0, which mainly modified the functions of SDn_monitor. py. The modified RYU_M1.0 can actively obtain the network status of Ceph cluster nodes. It can also passively receive load information from OSDs collected by the underlying nodes.

## Step 2: Deploy the Ceph heterogeneous cluster in the SDN environment.

Environment: CentOS7

1. When we complete the preparations, we use the CEPh-ansible tool to automate the Ceph cluster deployment.

2. We have added a custom OSD_INFO_MAP to the Ceph source code. OSD_INFO_MAP can be combined with SDN network model to maintain the load and network status information of OSD in real time and can be sensed by CRUSH algorithm. Finally, we use this information to build prediction model and multi-attribute decision mathematical model to optimize the read and write performance of the cluster.

# Tiered Data Sets
Olsync references Amazon Redshift clusters to achieve the optimal "performance-cost" balance. Links to Amazon Redshift clusters and their datasets can be found here: https://github.com/aws-samples /amazon-redshift-tiered-storage.The IBM Object Storage datasets that Olsync used for testing is linked here: http://iotta.snia.org/traces/key-value/36305.
