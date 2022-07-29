# coding=UTF-8
#  Introduction: The map includes osds in 'host' bucket and osd's [network info & load info],
#                use CMD to adjust osd's primary-affinity
#
#  Environment: 1.redis:   yum -y install python-redis,
#                          if client is not in server host, you should modify redis-server config
#                          /etc/redis/redis.conf --> bind <really ip,not 127.0.0.1>
#              'bw':bps, 'delay':ms, 'cpu':%(max 100%), 'mem':%(max 100%), 'io':KrBytes/s(read+write)
#  Author:     lzk
#  UpdateTime: 2021/8/1
from __future__ import division
import os, sys
import re, json
import subprocess
import time
import redis
true = 1
false = 0

# use 'ceph osd dump' to update osd ip addr addr
def get_osd_addr():
    try:    
        osd_addr_dic = {}
        OSD_DUMP = subprocess.Popen(['ceph osd dump --format=json'], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        OSD_DUMP = OSD_DUMP.stdout.read()
        OSD_DUMP = eval(OSD_DUMP)
        for osd_num in range(len(OSD_DUMP['osds'])):
            if ((OSD_DUMP['osds'][osd_num]['up']) and (OSD_DUMP['osds'][osd_num]['in'])) == 1:
                osd_addr_temp = OSD_DUMP['osds'][osd_num]['cluster_addr']
                osd_addr = re.findall(r'(?<![\.\d])(?:\d{1,3}\.){3}\d{1,3}(?![\.\d])', osd_addr_temp)[0] #re.findall返回string中所有与pattern相匹配的全部字串，返回形式为数组
                osd_addr_dic[OSD_DUMP['osds'][osd_num]['osd']] = osd_addr
                print ("get_osd_ip: osd.%d ip is %s" % (osd_num, osd_addr))
        #print (osd_addr_dic)
        '''
        osd_addr_dic = {0: '192.168.1.104', 1: '192.168.1.100', 2: '192.168.1.101', 3: '192.168.1.105', 
                        4: '192.168.1.100', 5: '192.168.1.101', 6: '192.168.1.104', 7: '192.168.1.105'}   
        '''     
        return osd_addr_dic
    except:
        print ("Can't use Regular Expressions to get ceph_osd_ip!")

# use 'ceph osd df tree' to get osd range
def get_osd_range(optimize_range):
    flag = false
    osd_range = []
    # osd_type = {}
    # osd_size = {}
    # osd_per_host = {}
    osd_now_host = 0
    pgs_per_osd = {}
    OSD_RANGE = subprocess.Popen(['ceph osd df tree --format=json'], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    OSD_RANGE = OSD_RANGE.stdout.read()
    OSD_RANGE = eval(OSD_RANGE)
    for i in range(len(OSD_RANGE['nodes'])):
        if OSD_RANGE['nodes'][i]['name'] == optimize_range:
            if OSD_RANGE['nodes'][i]['children'][0] < 0:
                for j in range(i+1,len(OSD_RANGE['nodes'])):
                    if OSD_RANGE['nodes'][j]['name'] == 'ssd_host':
                        flag = true
                        break
                    if OSD_RANGE['nodes'][j]['id']  in OSD_RANGE['nodes'][i]['children']:
                        osd_now_host = len(OSD_RANGE['nodes'][j]['children'])
                        for item in OSD_RANGE['nodes'][j]['children']:
                            osd_range.append(item)
                        #osd_range.append(OSD_RANGE['nodes'][j]['children'])
                    if OSD_RANGE['nodes'][j]['id'] > 0:
                        # osd_type[OSD_RANGE['nodes'][j]['id']] = OSD_RANGE['nodes'][j]['device_class']
                        pgs_per_osd[OSD_RANGE['nodes'][j]['id']] = OSD_RANGE['nodes'][j]['pgs']
                        #print(OSD_RANGE['nodes'][j])
                        # osd_size[OSD_RANGE['nodes'][j]['id']] = round(OSD_RANGE['nodes'][j]['kb']/(1024**3),2)
                        # osd_per_host[OSD_RANGE['nodes'][j]['id']] = osd_now_host
            else:
                osd_range = OSD_RANGE['nodes'][i]['children']
                for j in range(i+1,len(OSD_RANGE['nodes'])):
                    if OSD_RANGE['nodes'][j]['id'] < 0:
                        flag = true
                        break
                    # osd_type[OSD_RANGE['nodes'][j]['id']] = OSD_RANGE['nodes'][j]['device_class']
                    pgs_per_osd[OSD_RANGE['nodes'][j]['id']] = OSD_RANGE['nodes'][j]['pgs']
                    # osd_size[OSD_RANGE['nodes'][j]['id']] = round(OSD_RANGE['nodes'][j]['kb']/(1024**3),2)
                # osd_range,osd_per_host = OSD_RANGE['nodes'][i]['children'],len(OSD_RANGE['nodes'][i]['children'])
            
        if flag == 1:
            break
    #print(osd_range)
    #print(osd_type)
    #print(osd_size)
    #print(osd_per_host)
    # return osd_range,osd_type,osd_size,osd_per_host,pgs_per_osd
    return osd_range, pgs_per_osd

# get osd and its' bandwidth for <length> times
def get_osd_info_dic(osd_addr_dic, dict, times, optimize_range, osd_range, pgs_per_osd):
    #print('get_osd_info_dict....begin\n')
    pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
    r = redis.StrictRedis(connection_pool=pool)
    #delete key in osd_bw but not in osd_addr_dic
    # in order that host is down in runtime
    if dict:
        for key in dict.keys():
            if key not in osd_addr_dic:
                del dict[key]
            for x in dict[key].keys():
                if len(dict[key][x]) == times:
                    dict[key][x].pop(0)
    #update osd_bw of the osd in osd_addr_dic
    for key in osd_addr_dic.keys():
        if r.get(osd_addr_dic[key]) is None:
            continue
        if(optimize_range == "ssd_host" or optimize_range == "hdd_host") and (key not in osd_range):
            continue
        # dict.setdefault(key, {'bw': [], 'delay': [], 'cpu': [], 'mem': [], 'pgs':[], 'r': [], 'w':[]})
        dict.setdefault(key, {'bw': [], 'cpu': [], 'mem': [], 'pgs':[], 'r': [], 'w':[]})
        osd_info_dic = eval(r.get(osd_addr_dic[key]))
        bw = osd_info_dic['bw']
        # delay = osd_info_dic['delay']
        cpu = osd_info_dic['cpu']
        mem = osd_info_dic['mem']
        pgs = pgs_per_osd[key]
        r_io = osd_info_dic['io'][key]['r']
        w_io = osd_info_dic['io'][key]['w']
        dict[key]['bw'].append(bw)
        # dict[key]['delay'].append(delay)
        dict[key]['cpu'].append(cpu)
        dict[key]['mem'].append(mem)
        dict[key]['pgs'].append(pgs)
        dict[key]['r'].append(r_io)
        dict[key]['w'].append(w_io)
    #print('get_osd_info_dict....end\n')

# calculate osd weight base on TOPSIS
def calc_osd_performance(osd_info_dic, optimize_mode):

    io = ''
    r_io = ''
    if optimize_mode == 0:
        io = 'w'
        r_io = 'r'
    else:
        io = 'r'
        r_io = 'w'

    osd_type = {4: 1, 5: 1, 6: 1, 7: 4, 8: 2, 9: 2, 10: 3, 12: 1, 16: 3, 17: 1, 18: 1, 19: 1, 23: 1, 25: 1, 30: 4} 

    rf_weight = {1: {'r': {'bw': 0.42, 'cpu': 0.17, 'mem': 0.12, 'pgs': 0.18, 'w': 0.11}, 'w': {'bw': 0.21, 'cpu': 0.08, 'mem': 0.22, 'pgs': 0.31, 'r': 0.18}},
                 2: {'r': {'bw': 0.63, 'cpu': 0.16, 'mem': 0.05, 'pgs': 0.10, 'w': 0.06}, 'w': {'bw': 0.11, 'cpu': 0.02, 'mem': 0.19, 'pgs': 0.57, 'r': 0.12}},
                 3: {'r': {'bw': 0.20, 'cpu': 0.08, 'mem': 0.15, 'pgs': 0.26, 'w': 0.31}, 'w': {'bw': 0.28, 'cpu': 0.01, 'mem': 0.14, 'pgs': 0.37, 'r': 0.20}},
                 4: {'r': {'bw': 0.07, 'cpu': 0.02, 'mem': 0.19, 'pgs': 0.44, 'w': 0.28}, 'w': {'bw': 0.25, 'cpu': 0.07, 'mem': 0.18, 'pgs': 0.39, 'r': 0.11}}
                }

    osd_weight_dic = {}
    bw_list = []
    cpu_list = []
    mem_list = []
    pgs_list = []
    iops_list = []

    sum_bw = 0
    sum_cpu = 0
    sum_mem = 0
    sum_pgs = 0
    sum_iops = 0

    for osd in osd_info_dic.keys():
        sum_bw += osd_info_dic[osd]['bw'] ** 2
        sum_cpu += osd_info_dic[osd]['cpu'] ** 2
        sum_mem += osd_info_dic[osd]['mem'] ** 2
        sum_pgs += osd_info_dic[osd]['pgs'] ** 2
        sum_iops += osd_info_dic[osd][io] ** 2
    
    sum_bw_sqrt = (sum_bw ** 0.5) or 1
    sum_cpu_sqrt = (sum_cpu ** 0.5) or 1
    sum_mem_sqrt = (sum_mem ** 0.5) or 1
    sum_pgs_sqrt = (sum_pgs ** 0.5) or 1
    sum_iops_sqrt = (sum_iops ** 0.5) or 1

    print ("-----------1:sum----------")
    print ([sum_bw_sqrt, sum_cpu_sqrt, sum_mem_sqrt, sum_pgs_sqrt, sum_iops_sqrt])
    for osd in osd_info_dic.keys():
        t = osd_type[osd]
        osd_info_dic[osd]['bw'] = ( osd_info_dic[osd]['bw'] / sum_bw_sqrt ) * rf_weight[t][io]['bw']
        osd_info_dic[osd]['pgs'] = ( osd_info_dic[osd]['pgs'] / sum_pgs_sqrt ) * rf_weight[t][io]['pgs']
        osd_info_dic[osd]['cpu'] = ( osd_info_dic[osd]['cpu'] / sum_cpu_sqrt ) * rf_weight[t][io]['cpu']
        osd_info_dic[osd]['mem'] = ( osd_info_dic[osd]['mem'] / sum_mem_sqrt ) * rf_weight[t][io]['mem']
        osd_info_dic[osd][io] = ( osd_info_dic[osd][io] / sum_iops_sqrt ) * rf_weight[t][io][r_io]
        bw_list.append(osd_info_dic[osd]['bw'])
        pgs_list.append(osd_info_dic[osd]['pgs'])
        cpu_list.append(osd_info_dic[osd]['cpu'])
        mem_list.append(osd_info_dic[osd]['mem'])
        iops_list.append(osd_info_dic[osd][io])

    bw_max = max(bw_list)
    bw_min = min(bw_list)
    iops_max = max(iops_list)
    iops_min = min(iops_list)
    cpu_max = max(cpu_list)
    cpu_min = min(cpu_list)
    mem_max = max(mem_list)
    mem_min = min(mem_list)
    pgs_max = max(pgs_list)
    pgs_min = min(pgs_list)
    print ("-----------2&3----------")
    print ('bw_list:%s\n io_list:%s\n cpu_list:%s\n mem_list:%s\n pgs_list:%s\n'%(bw_list, iops_list, cpu_list, mem_list, pgs_list))
    print ('bw_max:%s, iops_max:%s, cpu_max:%s, mem_max:%s, pgs_max:%s' %(bw_max, iops_max, cpu_max, mem_max, pgs_max))
    print ('bw_min:%s, iops_min:%s, cpu_min:%s, mem_min:%s, pgs_min:%s' %(bw_min, iops_min, cpu_min, mem_min, pgs_min))
    for osd in osd_info_dic.keys():
        bw = osd_info_dic[osd]['bw']
        iops = osd_info_dic[osd][io]
        cpu = osd_info_dic[osd]['cpu']
        mem = osd_info_dic[osd]['mem']
        pgs = osd_info_dic[osd]['pgs']
        d_better = ( ( ((bw - bw_max) ** 2) + ((iops - iops_max) ** 2) + ((cpu - cpu_max) ** 2) + ((mem - mem_max) ** 2) + ((pgs - pgs_max) ** 2) ) ** 0.5 )
        d_worst = ( ( ((bw - bw_min) ** 2) + ((iops - iops_min) ** 2) + ((cpu - cpu_min) ** 2) + ((mem - mem_min) ** 2) + ((pgs - pgs_min) ** 2) ) ** 0.5 )
        closeness = round((d_worst / (d_better + d_worst)), 2)
        osd_weight_dic[osd] = closeness
        print ("-----------4&5----------")
        print ('osd:%s, bw:%s, iops:%s, cpu:%s, mem:%s, pgs:%s, d_better:%s, d_worst:%s, closeness:%s' % (osd, bw, iops, cpu, mem, pgs, d_better, d_worst, closeness))
    return osd_weight_dic

# execute 'ceph heterogeneous osd primary-affinity to optimize read'
def exec_osd_primaff(osd_performance, osd_init_primaff, HP_flag):
    for osd in osd_performance.keys():
        if HP_flag == 1:
            temp_primaff = osd_init_primaff[osd] * osd_performance[osd]
        else:
            temp_primaff = osd_performance[osd]
        #primaff = temp_primaff if temp_primaff > 0.1 else 0.1
        primaff = temp_primaff 
        cmd = "ceph osd primary-affinity %s %s &" % (osd,primaff)
        print("osd is %s, primary-affinity is %s "% (osd, primaff))
        print ("ceph osd primary-affinity: calling %s" % cmd)
        out = os.system(cmd)
        print ("ceph osd primary-affinity: %s" % out)

# execute 'ceph heterogeneous osd weight to optimize write and read'
def exec_osd_weight(osd_performance, osd_init_weight, HW_flag):
    for osd in osd_performance.keys():
        if HW_flag == 1:
            temp_weight = osd_init_weight[osd] * osd_performance[osd]
        else:
            temp_weight = osd_performance[osd]
        #weight = temp_weight if temp_weight > 0.1 else 0.1
        weight = temp_weight
        cmd = "ceph osd crush reweight osd.%s %s &" % (osd, weight)
        print("osd.%s crush weight is %s "% (osd, weight))
        print ("ceph osd crush weight: calling %s" % cmd)
        out = os.system(cmd)
        print ("ceph osd crush weight: %s" % out)

def get_optimize_mode():
    print("Please select input optimize_mode!\n"
          "Enter 0:optimize_mode is heterogeneous_optimize_read or optimize_read;\n"
          "Enter 1:optimize_mode is heterogeneous_optimize_write or optimize_write;\n")
    optimize_mode = int(input('please input optimize_mode:'))
    return optimize_mode

def get_optimize_range():
    print("Please select optimize_range!\n"
          "Enter dynamic_host:optimize_range is root of dynamic_host;\n"
          "Enter hdd_host:optimize_range is root of hdd_host;\n"
          "Enter ssd_host:optimize_range is root of ssd_host;\n"
          "Enter ssd_host&hdd_host:optimize_range is root of ssd_host and hdd_host;\n")
    optimize_range = str(input('please input optimize_range:'))
    return optimize_range 

def get_HP_flag():
    print("Please select whether to use the HP algorithm!\n"
          "Enter 0:no;\n"
          "Enter 1:yes;\n")
    HP_flag = bool(input('please input HP_flag:'))
    return HP_flag

def get_HW_flag():
    print("Please select whether to use the HW algorithm!\n"
          "Enter 0:no;\n"
          "Enter 1:yes;\n")
    HW_flag = bool(input('please input HW_flag:'))
    return HW_flag

def main():
    # update <times> times osd bandwidth,eg:times=5,osd_bw={'0':[1,2,3,4,5],'1':[6,7,8,9,10]}
    times = 5
    while True:
        optimize_mode = get_optimize_mode()

        optimize_range = get_optimize_range()

        HP_flag = get_HP_flag() 
        HW_flag = get_HW_flag()

        osd_info = {}
        osd_addr_dic = get_osd_addr()
        osd_range, pgs_per_osd = get_osd_range(optimize_range)

        # evertime update's interval is 60s
        for i in range(times):
            get_osd_info_dic(osd_addr_dic, osd_info, times, optimize_range, osd_range, pgs_per_osd)
            print("----------------osd info is----------------")
            for key in osd_info.keys():
                print('osd%s:%s' % (key, osd_info[key]))
            time.sleep(7)
        # calculate the average osd_info <times> times
        new_osd_info = {}
        for key in osd_info.keys():
            new_osd_info.setdefault(key, {})
            for x in osd_info[key]:
                if x == 'r' or x == 'w' or x == 'pgs':
                #if x == 'pgs':
                    new_osd_info[key][x] = -(round(float(sum(osd_info[key][x])) / len(osd_info[key][x]), 2))    
                else:
                    new_osd_info[key][x] = round(float(sum(osd_info[key][x])) / len(osd_info[key][x]), 2)


        print("----------------new osd info is----------------")
        for key in new_osd_info.keys():
            print('osd%s:%s'%(key, new_osd_info[key]))

        # according osd info to optimize osd's performance
        osd_performance = calc_osd_performance(new_osd_info, optimize_mode)
        print("osd performance is :")
        print (osd_performance)

        osd_init_primaff = {4: 0.1, 5: 0.1, 6: 0.1, 7: 1, 8: 0.16, 9: 0.16, 10: 1, 12: 0.1, 16: 1, 17: 0.1, 18: 0.1, 19: 0.1, 23: 0.1, 25: 0.1, 30: 1}
        osd_init_weight = {4: 1.472, 5: 1.472, 6: 1.472, 7: 15.4, 8: 2.356, 9: 2.356, 10: 15.4, 12: 1.472, 16: 15.4, 17: 1.472, 18: 1.472, 19: 1.472, 23: 1.472, 25: 1.472, 30: 15.4}
        # 异构读 和 非异构读
        if optimize_mode == 0:
            exec_osd_primaff(osd_performance, osd_init_primaff, HP_flag)
        # 异构写 和 非异构写
        else:
            exec_osd_weight(osd_performance, osd_init_weight, HW_flag)
        #print("sleeping 30 minutes...")
        time.sleep(10)

if __name__ == "__main__":
    main()

'''
def calc_osd_performance(osd_info_dic, optimize_mode, pgs_per_osd):

    io = ''
    if optimize_mode == 0 or 2:
        io = 'w'
    else:
        io = 'r'

    osd_type = {4: 1, 5: 1, 6: 1, 7: 4, 8: 2, 9: 2, 10: 3, 12: 1, 16: 3, 17: 1, 18: 1, 19: 1, 23: 1, 25: 1, 30: 4} 

    rf_weight = {1: {'bw': 1, 'cpu': 1, 'mem': 1, 'pgs': 1, io: 1}
                 2: {'bw': 1, 'cpu': 1, 'mem': 1, 'pgs': 1, io: 1}
                 3: {'bw': 1, 'cpu': 1, 'mem': 1, 'pgs': 1, io: 1}
                 4: {'bw': 1, 'cpu': 1, 'mem': 1, 'pgs': 1, io: 1}}

    osd_weight_dic = {}
    # bw_list = []
    bw_list = {1: [], 2: [], 3: [], 4: []}
    # cpu_list = []
    cpu_list = {1: [], 2: [], 3: [], 4: []}
    # mem_list = []
    mem_list = {1: [], 2: [], 3: [], 4: []}
    # pgs_list = []
    pgs_list = {1: [], 2: [], 3: [], 4: []}
    # io_list = []
    io_list = {1: [], 2: [], 3: [], 4: []}

    # sum_bw = 0
    sum_bw = {1: 0, 2: 0, 3: 0, 4: 0}
    # sum_cpu = 0
    sum_cpu = {1: 0, 2: 0, 3: 0, 4: 0}
    # sum_mem = 0
    sum_mem = {1: 0, 2: 0, 3: 0, 4: 0}
    # sum_pgs = 0
    sum_pgs = {1: 0, 2: 0, 3: 0, 4: 0}
    # sum_io = 0
    sum_io = {1: 0, 2: 0, 3: 0, 4: 0}

    for osd in osd_info_dic.keys():
        t = osd_type[osd] 
        # sum_bw += osd_info_dic[osd]['bw'] ** 2
        sum_bw[t] += osd_info_dic[osd]['bw'] ** 2
        # sum_cpu += osd_info_dic[osd]['cpu'] ** 2
        sum_cpu[t] += osd_info_dic[osd]['cpu'] ** 2
        # sum_mem += osd_info_dic[osd]['mem'] ** 2
        sum_mem[t] += osd_info_dic[osd]['mem'] ** 2
        # sum_pgs += pgs_per_osd[osd] ** 2
        sum_pgs[t] += pgs_per_osd[osd] ** 2
        # sum_io += osd_info_dic[osd][io] ** 2
        sum_io[t] += osd_info_dic[osd][io] ** 2
    
    sum_bw_sqrt = {1: 0, 2: 0, 3: 0, 4: 0}
    sum_cpu_sqrt = {1: 0, 2: 0, 3: 0, 4: 0}
    sum_mem_sqrt = {1: 0, 2: 0, 3: 0, 4: 0}
    sum_pgs_sqrt = {1: 0, 2: 0, 3: 0, 4: 0}
    sum_io_sqrt = {1: 0, 2: 0, 3: 0, 4: 0}
    for i in range(4):
        sum_bw_sqrt[i+1] = (sum_bw[i+1] ** 0.5) or 1
        sum_cpu_sqrt[i+1] = (sum_cpu[i+1] ** 0.5) or 1
        sum_mem_sqrt[i+1] = (sum_mem[i+1] ** 0.5) or 1
        sum_pgs_sqrt[i+1] = (sum_pgs[i+1] ** 0.5) or 1
        sum_io_sqrt[i+1] = (sum_io[i+1] ** 0.5) or 1
    print('sum_bw_sqrt: ', sum_bw_sqrt)
    print('sum_cpu_sqrt: ', sum_cpu_sqrt)
    print('sum_mem_sqrt: ', sum_mem_sqrt)
    print('sum_pgs_sqrt: ', sum_pgs_sqrt)
    print('sum_io_sqrt: ', sum_io_sqrt)

    print ("-----------1:sum----------")
    # print ([sum_bw_sqrt, sum_cpu_sqrt, sum_mem_sqrt, sum_pgs_sqrt, sum_io_sqrt])
    for osd in osd_info_dic.keys():
        t = osd_type[osd]
        osd_info_dic[osd]['bw'] = ( osd_info_dic[osd]['bw'] / sum_bw_sqrt[t] ) * rf_weight[t]['bw']
        pgs_per_osd[osd] = ( pgs_per_osd[osd] / sum_pgs_sqrt[t] ) * rf_weight[t]['pgs']
        osd_info_dic[osd]['cpu'] = ( osd_info_dic[osd]['cpu'] / sum_cpu_sqrt[t] ) * rf_weight[t]['cpu']
        osd_info_dic[osd]['mem'] = ( osd_info_dic[osd]['mem'] / sum_mem_sqrt[t] ) * rf_weight[t]['mem']
        osd_info_dic[osd][io] = ( osd_info_dic[osd][io] / sum_io_sqrt[t] ) * rf_weight[t][io]
        bw_list[t].append(osd_info_dic[osd]['bw'])
        pgs_list[t].append(pgs_per_osd[osd])
        cpu_list[t].append(osd_info_dic[osd]['cpu'])
        mem_list[t].append(osd_info_dic[osd]['mem'])
        io_list[t].append(osd_info_dic[osd][io])

    bw_max = {1: 0, 2: 0, 3: 0, 4: 0}
    bw_min = {1: 0, 2: 0, 3: 0, 4: 0}
    pgs_max = {1: 0, 2: 0, 3: 0, 4: 0}
    pgs_min = {1: 0, 2: 0, 3: 0, 4: 0}
    cpu_max = {1: 0, 2: 0, 3: 0, 4: 0}
    cpu_min = {1: 0, 2: 0, 3: 0, 4: 0}
    mem_max = {1: 0, 2: 0, 3: 0, 4: 0}
    mem_min = {1: 0, 2: 0, 3: 0, 4: 0}
    io_max = {1: 0, 2: 0, 3: 0, 4: 0}
    io_min = {1: 0, 2: 0, 3: 0, 4: 0}
    for i in range(4):
        bw_max[i+1] = max(bw_list[i+1])
        bw_min[i+1] = min(bw_list[i+1])
        pgs_max[i+1] = max(pgs_list[i+1])
        pgs_min[i+1] = min(pgs_list[i+1])
        cpu_max[i+1] = max(cpu_list[i+1])
        cpu_min[i+1] = min(cpu_list[i+1])
        mem_max[i+1] = max(mem_list[i+1])
        mem_min[i+1] = min(mem_list[i+1])
        io_max[i+1] = max(io_list[i+1])
        io_min[i+1] = min(io_list[i+1])
    print ("-----------2&3----------")
    print ('bw_list:%s\n io_list:%s\n cpu_list:%s\n mem_list:%s\n pgs_list:%s\n'%(bw_list, io_list, cpu_list, mem_list, pgs_list))
    # print ('bw_max:%s, io_max:%s, cpu_max:%s, mem_max:%s, pgs_max:%s' %(bw_max, io_max, cpu_max, mem_max, pgs_max))
    # print ('bw_min:%s, io_min:%s, cpu_min:%s, mem_min:%s, pgs_min:%s' %(bw_min, io_min, cpu_min, mem_min, pgs_min))
    for osd in osd_info_dic.keys():
        t = osd_type[osd]
        bw = osd_info_dic[osd]['bw']
        io = osd_info_dic[osd][io]
        cpu = osd_info_dic[osd]['cpu']
        mem = osd_info_dic[osd]['mem']
        pgs = pgs_per_osd[osd]
        print ('bw_max:%s, io_max:%s, cpu_max:%s, mem_max:%s, pgs_max:%s' %(bw_max[t], io_max[t], cpu_max[t], mem_max[t], pgs_max[t]))
        print ('bw_min:%s, io_min:%s, cpu_min:%s, mem_min:%s, pgs_min:%s' %(bw_min[t], io_min[t], cpu_min[t], mem_min[t], pgs_min[t]))
        d_better = ( ( ((bw - bw_max[t]) ** 2) + ((io - io_max[t]) ** 2) + ((cpu - cpu_max[t]) ** 2) + ((mem - mem_max[t]) ** 2) + ((pgs - pgs_max[t]) ** 2) ) ** 0.5)
        d_worst = ( ( ((bw - bw_min[t]) ** 2) + ((io - io_min[t]) ** 2) + ((cpu - cpu_min[t]) ** 2) + ((mem - mem_min[t]) ** 2) + ((pgs - pgs_min[t]) ** 2) ) ** 0.5)
        closeness = round((d_worst / (d_better + d_worst)), 2)
        osd_weight_dic[osd] = closeness
        print ("-----------4&5----------")
        print ('osd:%s, bw:%s, io:%s, cpu:%s, mem:%s, pgs:%s, d_better:%s, d_worst:%s, closeness:%s' % (osd, bw, io, cpu, mem, pgs, d_better, d_worst, closeness))
    return osd_weight_dic
'''
