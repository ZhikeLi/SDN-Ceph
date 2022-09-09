#coding=UTF-8
import sys
import time
import re
import psutil
import subprocess
import commands,json
from socket import *
from scapy.all import *
# get host network delay

global delay_all
delay_all = []

# 获取网络时延
def _get_delay(ip):
    time_str = []
    #delay_time = 0
    delay_time_sum = 0
    for i in range(15):
        p = subprocess.Popen(["ping -c 1 "+ ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        out = p.stdout.read()
        out_re = re.search((u'time=\d+\.+\d*'), out)
        if out_re is not None:
            time_tmp1 = filter(lambda x: x in '1234567890.', out_re.group())
            time_tmp2 = max(time_tmp1, 0)
            delay_all.append(time_tmp2)
            delay_time_sum += float(time_tmp2)
    delay_time = round(float(delay_time_sum / 15), 2)
    #print(max(delay_time , 0))    
    return delay_time

def _get_packet_loss(ip):
    p =subprocess.Popen(["ping -c 20 "+ ip], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True) 
    out = p.stdout.read()
    out_re = re.search(r'\d+%', out)
    if out_re is not None:
        lost = out_re.group()[0:]
        lost_tmp = int((lost.split('%'))[0]) 
    return (lost_tmp*100)
def _get_delay_jitter(ip):
    delay_dif = 0
# 时延抖动
    for each in range(-1, -16, -1):
        if each >= -14:
            delay_tmp3 = abs(float(delay_all[each]) - float(delay_all[each-1])) 
            delay_dif += delay_tmp3
    #print(round(delay_dif/14, 2))            
    return(round(delay_dif/14, 2))
  
# 调用psutil模块获取CPU和内存负载
def _get_cpu():
    cpu_tmp = min(psutil.cpu_percent(interval=1), 100)
    return round(cpu_tmp, 2)

def _get_mem():
    mem_tmp = min(psutil.virtual_memory().percent, 100)
    return round(mem_tmp, 2)

def _get_io():
    devices = {}
    osd_io = {}

    #use 'ceph-volume lvm list' to update osd_disk_postion
    osd_disk_json = commands.getoutput('ceph-volume lvm list --format=json')
    osd_disk = json.loads(osd_disk_json)
    #去除u'转化成str
    osd_disk = json.dumps(osd_disk)
    #将str转换成字典dict
    osd_disk = eval(osd_disk)
    #print(osd_disk)

    # use regular expression matches the ceph disk and record
    partitions = psutil.disk_partitions(all=True)
    #print(partitions)
    pattern = re.compile(r'/var/lib/ceph/osd/')
    # find device and it's index in partitions
    # devices --> result:{'10': 'sdb', '39': 'sdd', '59': 'sdf', '23': 'sdc', '49': 'sde', '0': 'sda'}
    for p in partitions:
        if pattern.match(p.mountpoint):
            #print(p.mountpoint)
            devices_name = p.mountpoint[23:]
            devices[devices_name] = osd_disk[str(devices_name)][0]['devices'][0][5:]
    #print(devices)

    # osd_io --> result:{0: 0.0, 39: 0.0, 10: 0.0, 49: 0.0, 23: 0.0, 59: 0.0}
    for key in devices:
        osd_num = int(key)
        osd_io.setdefault(osd_num,{'r':0,'w':0})
        pre_read_bytes = psutil.disk_io_counters(perdisk=True)[devices[key]].read_bytes
        pre_write_bytes = psutil.disk_io_counters(perdisk=True)[devices[key]].write_bytes
        time.sleep(1)
        after_read_bytes = psutil.disk_io_counters(perdisk=True)[devices[key]].read_bytes
        after_write_bytes = psutil.disk_io_counters(perdisk=True)[devices[key]].write_bytes
        read_bytes = float(after_read_bytes - pre_read_bytes)/1024
        write_bytes = float(after_write_bytes - pre_write_bytes)/1024
        osd_io[osd_num]['r'] = read_bytes
        osd_io[osd_num]['w'] = write_bytes
        #total_kbytes_temp = float(read_bytes + write_bytes)/1024
        #total_kbytes = round(total_kbytes_temp, 2)
        #osd_io[osd_num] = total_kbytes
    #print(osd_io)
    return osd_io

# send data
# give a host which in the network but no host bound it (IP, PORT)
# udp发送报文，udp报文必须指定一个当前交换机路由表找不到的地址，这样才能触发匹配流表table-miss，并将信息上传给SDN控制器
def _send_data():
    while True:
        try:
            delay = _get_delay('192.168.0.100')
            #packet_loss = _get_packet_loss('192.168.1.105')
            #print(packet_loss)
            #delay_jitter = _get_delay_jitter('192.168.1.105')
            #print(delay_jitter)
            cpu = _get_cpu()
            mem = _get_mem()
            io = _get_io()
            #data = str((delay, packet_loss, delay_jitter, cpu, mem, io))
            data = str((delay, cpu, mem, io))
            print(data)
            #print("delay",delay,"packet_loss",packet_loss,"delay_jitter",delay_jitter,"cpu",cpu,"mem",mem,"io",io)
            if not data:
                break
            #send(IP(src='172.25.7.191',dst='172.25.7.223')/ARP())
            send(IP(src='192.168.0.100',dst='192.168.0.225')/UDP(dport=12345)/Raw(load=data))
            time.sleep(1)
        except Exception as e:
            print ('Error: ', e)

if __name__ == '__main__':
        _send_data()
