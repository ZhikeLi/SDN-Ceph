# SDN-Ceph
In Software Defined Network(SDN), we propose An Adaptive Read/Write Optimized Algorithm for Ceph Heterogeneous Systems via Performance Prediction and Multi-attribute Decision-making


# Step 1: Deploy the SDN network environment of the cluster.

# Environment: Ubuntu20.04

# 1. Let's download the original RYU controller

# Execute the command: pip install ryu

# 2. We modified the source code of RYU controller to obtain the new version RYU_M1.0, which mainly modified the functions of SDn_monitor. py. The modified RYU_M1.0 can actively obtain the network status of Ceph cluster nodes. It can also passively receive load information from OSDs collected by the underlying nodes.

# Step 2: Deploy the Ceph heterogeneous cluster in the SDN environment.

# Environment: CentOS7

# 1. When we complete the preparations, we use the CEPh-ansible tool to automate the Ceph cluster deployment.

# 2. We integrate the revised osd_client. py and ceph_monitor_optimize. py code into the Ceph source code to adaptively optimize the read and write performance of the cluster. Osd_client. py is responsible for collecting OSDs load information and uploading it to SDN_Monitor. The cePH_MONITor_optimize.py code receives load information from SDN_Monitor delivery. The random forest algorithm running on Ceph_Monitor then receives the load information and trains the prediction model. Finally, Ceph_Monitor uses prediction model and mathematical model to make decision optimization.
