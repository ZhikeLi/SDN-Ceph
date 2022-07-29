from scapy.all import *
import binascii
import redis

while True:
    '''
        print('a',a,'type(a)',type(a))
        ('a', <Sniffed: TCP:0 UDP:1 ICMP:0 Other:0>, 'type(a)', <class 'scapy.plist.PacketList'>)
              <Sniffed: TCP:0 UDP:1 ICMP:0 Other:0> type(a) <class 'scapy.plist.PacketList'>
        print('type(data)',type(data))
        ('type(data)', <type 'str'>)
        
        print('binascii.a2b_hex(data)',binascii.a2b_hex(data))
        ('binascii.a2b_hex(data)', "{'172.25.7.191': {'bw': 99996.83, 'delay': 0.03, 'cpu': 0.2, 'mem': 9.5, 'io': {0: 0.0, 39: 0.0, 10: 0.0, 49: 0.0, 23: 0.0, 59: 0.0}}}")
        
        print('type(binascii.a2b_hex(data))',type(binascii.a2b_hex(data)))
        ('type(binascii.a2b_hex(data))', <type 'str'>)
    '''

    # 1.HW
    #data = [{'192.168.0.116': {'bw': 99981.4, 'delay': 0.01, 'cpu': 7.92, 'mem': 12.0, 'io': {30: {'r': 448.0, 'w': 736.0}}}, '192.168.0.107': {'bw': 99982.68, 'delay': 0.02, 'cpu': 7.94, 'mem': 12.0, 'io': {7: {'r': 504.0, 'w': 864.0}}}, '192.168.0.104': {'bw': 99977.35, 'delay': 0.02, 'cpu': 7.94, 'mem': 10.0, 'io': {8: {'r': 56.0, 'w': 72.0}, 16: {'r': 660.0, 'w': 688.0}}}, '192.168.0.109': {'bw': 99991.95, 'delay': 0.05, 'cpu': 7.91, 'mem': 5.0, 'io': {4: {'r': 60.0, 'w': 120.0}, 18: {'r': 48.0, 'w': 176.0}, 12: {'r': 40.0, 'w': 72.0}}}, '192.168.0.103': {'bw': 99979.4, 'delay': 0.01, 'cpu': 7.93, 'mem': 10.0, 'io': {9: {'r': 84.0, 'w': 312.0}, 10: {'r': 556.0, 'w': 588.0}}}, '192.168.0.108': {'bw': 99993.77, 'delay': 0.03, 'cpu': 7.96, 'mem': 3.0, 'io': {17: {'r': 64.0, 'w': 84.0}, 6: {'r': 0.0, 'w': 76.0}, 23: {'r': 80.0, 'w': 128.0}}}}, {'192.168.0.116': {'bw': 99984.97, 'delay': 0.02, 'cpu': 7.91, 'mem': 12.0, 'io': {30: {'r': 676.0, 'w': 1252.0}}}, '192.168.0.107': {'bw': 99985.68, 'delay': 0.02, 'cpu': 7.92, 'mem': 12.0, 'io': {7: {'r': 676.0, 'w': 1304.0}}}, '192.168.0.104': {'bw': 99981.58, 'delay': 0.02, 'cpu': 7.94, 'mem': 10.0, 'io': {8: {'r': 36.0, 'w': 60.0}, 16: {'r': 748.0, 'w': 852.0}}}, '192.168.0.109': {'bw': 99993.45, 'delay': 0.04, 'cpu': 7.91, 'mem': 5.0, 'io': {4: {'r': 72.0, 'w': 116.0}, 18: {'r': 60.0, 'w': 116.0}, 12: {'r': 40.0, 'w': 64.0}}}, '192.168.0.103': {'bw': 99983.52, 'delay': 0.01, 'cpu': 7.94, 'mem': 10.0, 'io': {9: {'r': 100.0, 'w': 180.0}, 10: {'r': 284.0, 'w': 532.0}}}, '192.168.0.108': {'bw': 99994.02, 'delay': 0.03, 'cpu': 7.97, 'mem': 3.0, 'io': {17: {'r': 68.0, 'w': 80.0}, 6: {'r': 8.0, 'w': 88.0}, 23: {'r': 80.0, 'w': 132.0}}}}, {'192.168.0.116': {'bw': 99984.42, 'delay': 0.02, 'cpu': 7.9, 'mem': 12.0, 'io': {30: {'r': 484.0, 'w': 680.0}}}, '192.168.0.107': {'bw': 99985.54, 'delay': 0.02, 'cpu': 7.95, 'mem': 12.0, 'io': {7: {'r': 480.0, 'w': 604.0}}}, '192.168.0.104': {'bw': 99981.23, 'delay': 0.02, 'cpu': 7.93, 'mem': 10.0, 'io': {8: {'r': 52.0, 'w': 92.0}, 16: {'r': 672.0, 'w': 1100.0}}}, '192.168.0.109': {'bw': 99993.07, 'delay': 0.04, 'cpu': 7.92, 'mem': 5.0, 'io': {4: {'r': 68.0, 'w': 184.0}, 18: {'r': 56.0, 'w': 108.0}, 12: {'r': 92.0, 'w': 92.0}}}, '192.168.0.103': {'bw': 99983.23, 'delay': 0.01, 'cpu': 7.93, 'mem': 10.0, 'io': {9: {'r': 80.0, 'w': 116.0}, 10: {'r': 680.0, 'w': 1000.0}}}, '192.168.0.108': {'bw': 99993.75, 'delay': 0.03, 'cpu': 7.95, 'mem': 3.0, 'io': {17: {'r': 100.0, 'w': 64.0}, 6: {'r': 16.0, 'w': 96.0}, 23: {'r': 84.0, 'w': 132.0}}}}, {'192.168.0.116': {'bw': 99984.47, 'delay': 0.02, 'cpu': 7.93, 'mem': 12.0, 'io': {30: {'r': 628.0, 'w': 616.0}}}, '192.168.0.107': {'bw': 99983.7, 'delay': 0.02, 'cpu': 7.93, 'mem': 12.0, 'io': {7: {'r': 572.0, 'w': 676.0}}}, '192.168.0.104': {'bw': 99977.66, 'delay': 0.02, 'cpu': 7.93, 'mem': 10.0, 'io': {8: {'r': 52.0, 'w': 140.0}, 16: {'r': 800.0, 'w': 964.0}}}, '192.168.0.109': {'bw': 99992.63, 'delay': 0.04, 'cpu': 7.91, 'mem': 5.0, 'io': {4: {'r': 44.0, 'w': 112.0}, 18: {'r': 48.0, 'w': 136.0}, 12: {'r': 40.0, 'w': 48.0}}}, '192.168.0.103': {'bw': 99981.26, 'delay': 0.02, 'cpu': 7.95, 'mem': 10.0, 'io': {9: {'r': 160.0, 'w': 324.0}, 10: {'r': 500.0, 'w': 760.0}}}, '192.168.0.108': {'bw': 99993.31, 'delay': 0.03, 'cpu': 7.96, 'mem': 3.0, 'io': {17: {'r': 80.0, 'w': 144.0}, 6: {'r': 0.0, 'w': 72.0}, 23: {'r': 32.0, 'w': 88.0}}}}, {'192.168.0.116': {'bw': 99979.32, 'delay': 0.02, 'cpu': 7.93, 'mem': 12.0, 'io': {30: {'r': 336.0, 'w': 1008.0}}}, '192.168.0.107': {'bw': 99982.46, 'delay': 0.02, 'cpu': 7.95, 'mem': 12.0, 'io': {7: {'r': 396.0, 'w': 1164.0}}}, '192.168.0.104': {'bw': 99977.38, 'delay': 0.02, 'cpu': 7.89, 'mem': 10.0, 'io': {8: {'r': 12.0, 'w': 120.0}, 16: {'r': 296.0, 'w': 1240.0}}}, '192.168.0.109': {'bw': 99991.69, 'delay': 0.04, 'cpu': 7.89, 'mem': 5.0, 'io': {4: {'r': 40.0, 'w': 356.0}, 18: {'r': 40.0, 'w': 372.0}, 12: {'r': 24.0, 'w': 116.0}}}, '192.168.0.103': {'bw': 99979.78, 'delay': 0.02, 'cpu': 7.92, 'mem': 10.0, 'io': {9: {'r': 40.0, 'w': 168.0}, 10: {'r': 116.0, 'w': 956.0}}}, '192.168.0.108': {'bw': 99992.64, 'delay': 0.03, 'cpu': 7.94, 'mem': 3.0, 'io': {17: {'r': 28.0, 'w': 308.0}, 6: {'r': 4.0, 'w': 60.0}, 23: {'r': 24.0, 'w': 172.0}}}}]
    # 2.HW+HP
    data = [{'192.168.0.107': {'bw': 99892.35, 'delay': 0.02, 'cpu': 7.87, 'mem': 12.0, 'io': {7: {'r': 224.0, 'w': 1424.0}}}, '192.168.0.116': {'bw': 99998.77, 'delay': 0.02, 'cpu': 8.0, 'mem': 12.0, 'io': {30: {'r': 0.0, 'w': 0.0}}}, '192.168.0.104': {'bw': 99895.74, 'delay': 0.02, 'cpu': 7.84, 'mem': 11.0, 'io': {8: {'r': 16.0, 'w': 172.0}, 16: {'r': 120.0, 'w': 600.0}}}, '192.168.0.103': {'bw': 99997.5, 'delay': 0.02, 'cpu': 8.0, 'mem': 11.0, 'io': {9: {'r': 0.0, 'w': 0.0}, 10: {'r': 0.0, 'w': 0.0}}}, '192.168.0.108': {'bw': 99997.68, 'delay': 0.03, 'cpu': 7.99, 'mem': 4.0, 'io': {17: {'r': 0.0, 'w': 0.0}, 6: {'r': 0.0, 'w': 0.0}, 23: {'r': 0.0, 'w': 0.0}}}, '192.168.0.109': {'bw': 99993.23, 'delay': 0.04, 'cpu': 7.92, 'mem': 5.0, 'io': {4: {'r': 0.0, 'w': 244.0}, 18: {'r': 0.0, 'w': 220.0}, 12: {'r': 0.0, 'w': 176.0}}}}, {'192.168.0.107': {'bw': 99900.04, 'delay': 0.02, 'cpu': 7.82, 'mem': 12.0, 'io': {7: {'r': 168.0, 'w': 1108.0}}}, '192.168.0.116': {'bw': 99998.71, 'delay': 0.02, 'cpu': 8.0, 'mem': 12.0, 'io': {30: {'r': 0.0, 'w': 0.0}}}, '192.168.0.104': {'bw': 99903.07, 'delay': 0.02, 'cpu': 7.88, 'mem': 11.0, 'io': {8: {'r': 8.0, 'w': 484.0}, 16: {'r': 216.0, 'w': 1736.0}}}, '192.168.0.103': {'bw': 99998.01, 'delay': 0.02, 'cpu': 8.0, 'mem': 11.0, 'io': {9: {'r': 0.0, 'w': 0.0}, 10: {'r': 0.0, 'w': 0.0}}}, '192.168.0.108': {'bw': 99997.49, 'delay': 0.03, 'cpu': 7.98, 'mem': 4.0, 'io': {17: {'r': 0.0, 'w': 0.0}, 6: {'r': 0.0, 'w': 0.0}, 23: {'r': 0.0, 'w': 0.0}}}, '192.168.0.109': {'bw': 99994.09, 'delay': 0.04, 'cpu': 7.93, 'mem': 5.0, 'io': {4: {'r': 0.0, 'w': 400.0}, 18: {'r': 0.0, 'w': 340.0}, 12: {'r': 0.0, 'w': 284.0}}}}, {'192.168.0.107': {'bw': 99890.54, 'delay': 0.02, 'cpu': 7.83, 'mem': 12.0, 'io': {7: {'r': 252.0, 'w': 1840.0}}}, '192.168.0.116': {'bw': 99998.86, 'delay': 0.02, 'cpu': 7.99, 'mem': 12.0, 'io': {30: {'r': 0.0, 'w': 0.0}}}, '192.168.0.104': {'bw': 99897.05, 'delay': 0.02, 'cpu': 7.78, 'mem': 11.0, 'io': {8: {'r': 4.0, 'w': 260.0}, 16: {'r': 196.0, 'w': 1552.0}}}, '192.168.0.103': {'bw': 99997.63, 'delay': 0.02, 'cpu': 8.0, 'mem': 11.0, 'io': {9: {'r': 0.0, 'w': 0.0}, 10: {'r': 0.0, 'w': 0.0}}}, '192.168.0.108': {'bw': 99998.08, 'delay': 0.03, 'cpu': 7.99, 'mem': 4.0, 'io': {17: {'r': 0.0, 'w': 0.0}, 6: {'r': 0.0, 'w': 0.0}, 23: {'r': 0.0, 'w': 0.0}}}, '192.168.0.109': {'bw': 99994.33, 'delay': 0.02, 'cpu': 7.93, 'mem': 5.0, 'io': {4: {'r': 0.0, 'w': 352.0}, 18: {'r': 0.0, 'w': 292.0}, 12: {'r': 0.0, 'w': 360.0}}}}, {'192.168.0.107': {'bw': 99900.99, 'delay': 0.02, 'cpu': 7.76, 'mem': 12.0, 'io': {7: {'r': 220.0, 'w': 1144.0}}}, '192.168.0.116': {'bw': 99999.19, 'delay': 0.02, 'cpu': 8.0, 'mem': 12.0, 'io': {30: {'r': 0.0, 'w': 0.0}}}, '192.168.0.104': {'bw': 99905.09, 'delay': 0.02, 'cpu': 7.83, 'mem': 11.0, 'io': {8: {'r': 0.0, 'w': 112.0}, 16: {'r': 184.0, 'w': 1136.0}}}, '192.168.0.103': {'bw': 99998.03, 'delay': 0.02, 'cpu': 8.0, 'mem': 11.0, 'io': {9: {'r': 0.0, 'w': 0.0}, 10: {'r': 0.0, 'w': 0.0}}}, '192.168.0.108': {'bw': 99997.89, 'delay': 0.04, 'cpu': 7.98, 'mem': 4.0, 'io': {17: {'r': 0.0, 'w': 0.0}, 6: {'r': 0.0, 'w': 0.0}, 23: {'r': 0.0, 'w': 0.0}}}, '192.168.0.109': {'bw': 99994.27, 'delay': 0.04, 'cpu': 7.94, 'mem': 5.0, 'io': {4: {'r': 4.0, 'w': 268.0}, 18: {'r': 0.0, 'w': 388.0}, 12: {'r': 0.0, 'w': 436.0}}}}, {'192.168.0.107': {'bw': 99872.86, 'delay': 0.02, 'cpu': 7.81, 'mem': 12.0, 'io': {7: {'r': 188.0, 'w': 1704.0}}}, '192.168.0.116': {'bw': 99998.1, 'delay': 0.02, 'cpu': 8.0, 'mem': 12.0, 'io': {30: {'r': 0.0, 'w': 0.0}}}, '192.168.0.104': {'bw': 99880.15, 'delay': 0.02, 'cpu': 7.84, 'mem': 11.0, 'io': {8: {'r': 8.0, 'w': 492.0}, 16: {'r': 104.0, 'w': 828.0}}}, '192.168.0.103': {'bw': 99996.63, 'delay': 0.02, 'cpu': 7.99, 'mem': 11.0, 'io': {9: {'r': 0.0, 'w': 0.0}, 10: {'r': 0.0, 'w': 0.0}}}, '192.168.0.108': {'bw': 99997.26, 'delay': 0.03, 'cpu': 8.0, 'mem': 4.0, 'io': {17: {'r': 0.0, 'w': 0.0}, 6: {'r': 0.0, 'w': 0.0}, 23: {'r': 0.0, 'w': 0.0}}}, '192.168.0.109': {'bw': 99992.31, 'delay': 0.04, 'cpu': 7.92, 'mem': 5.0, 'io': {4: {'r': 0.0, 'w': 276.0}, 18: {'r': 0.0, 'w': 256.0}, 12: {'r': 0.0, 'w': 340.0}}}}]
    pool = redis.ConnectionPool(host='127.0.0.1',port=6379,db=0)
    r = redis.StrictRedis(connection_pool=pool)
    for i in range(len(data)):
        for key in data[i]:
            print("%s:%s"%(key,data[i][key]))
            r.set(key,str(data[i][key]))
        time.sleep(6)
        print("---------------\n")