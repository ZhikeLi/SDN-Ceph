
#  Author:     lzk(moser)
#  UpdateTime: 2021/8/8

from __future__ import division
import logging
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet
from ryu.controller import ofp_event
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.lib.packet import ether_types
import setting
import time
import binascii

class NetworkMonitor(app_manager.RyuApp):
    """
        NetworkMonitor is a Ryu app for collecting traffic information.
    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkMonitor, self).__init__(*args, **kwargs)
        self.name = 'monitor'

        # init logging
        self.logger = logging.getLogger('monitor')
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(name)s - LINE %(lineno)d - %(levelname)s - %(message)s')
        self.fh = logging.FileHandler("monitor.log", mode="w", encoding="UTF-8")
        self.fh.setLevel(logging.DEBUG)
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)

        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        self.flow_stats = {}
        self.flow_speed = {}
        self.stats = {}
        self.port_features = {}
        self.free_bandwidth = {}
        self.osd_info = {}
        self.mac_to_port = {}
        self.ip_to_port = {}
        self.osd_range = {}
        self.host_info = {}
        self.packet_out_msg = []
        self.flag = 0 #trigger packet_in
        # Start to green thread to monitor traffic and calculating
        # free bandwidth of links respectively.
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Record datapath's info
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                #self.logger.info('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                #self.logger.info('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        """
            Main entry method of monitoring traffic.
        """
        while True:
            self.stats['flow'] = {}
            self.stats['port'] = {}
            #print ("----------free bandwidth----------")
            #print (self.free_bandwidth)
            #print ("----------ip_to_port ----------")
            #print (self.ip_to_port)
            #print ("----------host info ----------")
            #print(self.host_info)
            #print('----------------------\n\n')
            for msg in self.packet_out_msg:
                self._send_packet_out(msg, self.host_info)
                time.sleep(5)
            #print ("----------osd_range----------")
            #print(self.osd_range)
            #cpumem_per_host = {"192.168.0.100":{"mem":48,"cpu":16}, "192.168.0.101":{"mem":8,"cpu":6}, "192.168.0.102":{"mem":8,"cpu":6}, "192.168.0.103":{"mem":16,"cpu":8}, "192.168.0.104":{"mem":16,"cpu":8},
            #            "192.168.0.105":{"mem":8,"cpu":6}, "192.168.0.106":{"mem":8,"cpu":6}, "192.168.0.107":{"mem":16,"cpu":8}, "192.168.0.108":{"mem":8,"cpu":8}, "192.168.0.109":{"mem":8,"cpu":8},
            #            "192.168.0.110":{"mem":8,"cpu":8}, "192.168.0.111":{"mem":126,"cpu":64}, "192.168.0.112":{"mem":4,"cpu":4}, "192.168.0.113":{"mem":16,"cpu":16}, "192.168.0.114":{"mem":4,"cpu":4},
            #            "192.168.0.115":{"mem":8,"cpu":4}, "192.168.0.116":{"mem":16,"cpu":8}, "192.168.0.117":{"mem":8,"cpu":8}, "192.168.0.118":{"mem":8,"cpu":6}, "192.168.0.119":{"mem":8,"cpu":4}}
            #host_info = self.host_info
            #osd_range = self.osd_range
            #for k,v in host_info.items():
            #    if v['io'] == 0:
            #        continue
            #    for m,n in v['io'].items():
            #        print(m,round(99999.99-v['bw'],2),round(v['cpu'] / 100 * cpumem_per_host[k]['cpu'],2),round(cpumem_per_host[k]['mem'] * v['mem'] / 100, 2),osd_range[m]['size'],osd_range[m]['per_host'],osd_range[m]['type'],osd_range[m]['pgs'],n['r'],n['w'])
            #time.sleep(5)
            #print('----------------------\n\n')
            # refresh data.
            #print('self.datapaths.values()', self.datapaths.values())
            for dp in self.datapaths.values():
                self.port_features.setdefault(dp.id, {})
                self._request_stats(dp)

            #show info
            hub.sleep(setting.MONITOR_PERIOD)
            if self.stats['flow'] or self.stats['port']:
                self.show_stat('flow')
                self.show_stat('port')
                hub.sleep(1)

    def _send_packet_out(self, msg, data):        
        print("****data is",data)
        data = str(data)
        data = data.encode("utf-8")
        data = binascii.b2a_hex(data)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        pkt = packet.Packet(msg.data)
        eth_header = pkt.get_protocols(ethernet.ethernet)[0]
        dst_mac = eth_header.src
        #print('dst_mac',dst_mac)
        #arp header
        #arp_header = pkt.get_protocols(arp.arp)
        #dst_ip = arp_header.src_ip
        dst_ip = '192.168.0.100'
        out_port = msg.match['in_port']
        #print('out_port', out_port)
        ether_instance = ethernet.ethernet(dst=dst_mac,
                src='00:0c:29:31:d6:02',
                              ethertype=eth_header.ethertype)
        ipv4_instance = ipv4.ipv4(src='192.168.1.107', dst=dst_ip, proto=17)
        udp_instance = udp.udp(src_port=12346, dst_port=10086)
        pkt = packet.Packet()
        pkt.add_protocol(ether_instance)
        pkt.add_protocol(ipv4_instance)
        pkt.add_protocol(udp_instance)
        pkt.add_protocol(data)
        pkt.serialize()
        actions = [ofp_parser.OFPActionOutput(out_port)]
        req = ofp_parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=pkt.data)
        datapath.send_msg(req)
        print('packet out finish')

    def _request_stats(self, datapath):
        """
            Sending request msg to datapath
        """
        #self.logger.info('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortDescStatsRequest(datapath, 0)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    def _save_freebandwidth(self, dpid, port_no, speed):
        # Calculate free bandwidth of port and save it.
        port_state = self.port_features.get(dpid).get(port_no)
        if port_state:
            #not save Interfaces between switches
            if port_state[2] != 0:
                capacity = port_state[2]
                curr_bw = self._get_free_bw(capacity, speed)
                key = (dpid,port_no)
                if key not in setting.SW_PORT:
                    self.free_bandwidth.setdefault(key, None)
                    self.free_bandwidth[(dpid, port_no)] = curr_bw
        else:
            self.logger.info("Fail in getting port state")

    def _save_stats(self, _dict, key, value, length):
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)

        if len(_dict[key]) > length:
            _dict[key].pop(0)

    def _get_speed(self, now, pre, period):
        if period:
            return (now - pre) / (period)
        else:
            return 0

    def _get_free_bw(self, capacity, speed):
        # capacity:OFPPortDescStatsReply default is kbit/s
        # i change it bit/s to subtract speed(bit/s) then convert into Mbps
        freebw_tmp1 = max((capacity * 10 ** 3) - speed * 8, 0)
        freebw_tmp = float(freebw_tmp1)/10**6
        freebw = round(freebw_tmp, 2)
        return freebw

    def _get_time(self, sec, nsec):
        return sec + nsec / (10 ** 9)

    def _get_period(self, n_sec, n_nsec, p_sec, p_nsec):
        return self._get_time(n_sec, n_nsec) - self._get_time(p_sec, p_nsec)

    def _save_ipfreebw(self, freebw, ip_port, hostinfo):
        for key in freebw.keys():
            if key not in ip_port:
                continue
            hostinfo.setdefault(ip_port[key], {'bw':0, 'delay':0, 'cpu':0, 'mem':0, 'io':0})
            hostinfo[ip_port[key]]['bw']=freebw[key]
    def _save_udp(self, osdinfo, ip_port, hostinfo):
        for key in ip_port.keys():
            if key not in osdinfo:
                continue
            data = eval(osdinfo[key])
            if len(data) > 5:
                self.osd_range = data
            else:
                hostinfo.setdefault(ip_port[key], {'bw':0, 'delay': 0, 'cpu': 0, 'mem': 0, 'io': 0})
                #print('_save_udp:osdinfo[key]',osdinfo[key])
                #delay, cpu, mem, io = eval(osdinfo[key])
                delay, cpu, mem, io = data
                hostinfo[ip_port[key]]['delay']=delay
                hostinfo[ip_port[key]]['cpu'] = cpu
                hostinfo[ip_port[key]]['mem'] = mem
                hostinfo[ip_port[key]]['io'] = io

    def _parse_udp(self, dpid, port, msg_data):
        eth_data = ethernet.ethernet.parser(msg_data)[2]
        ip_data = ipv4.ipv4.parser(eth_data)[2]
        udp_data = udp.udp.parser(ip_data)[2]
        #print('_parse_udp:udp_data',udp_data)
        #delay = self._packet_analyze(udp_data)
        key = (dpid, port)
        self.osd_info[key] = udp_data

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.info("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        if self.flag == 0:
            print('packet_in_trigger')
            self.flag = 1
        msg = ev.msg
        #print('msg.data',msg.data)
        datapath = msg.datapath
        #print('msg.datapath',msg.datapath)
        dpid = datapath.id
        #print('datapath.id',datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        #forbidden in_port == 16 is ip of '192.168.0.200'
        if in_port == 16:
            return
        #if in_port == 4 and self.flag == 1:
        if in_port == 4:
            self.packet_out_msg.clear()
            self.packet_out_msg.append(msg)
            #self.flag = 2
            #print('flag=',self.flag)
        #print('msg.match[in_port]', in_port)
        pkt = packet.Packet(msg.data)
        #print(pkt.protocols)
        #ethernet header
        eth_header = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth_header.dst
        src = eth_header.src
        #print('eth_header.dst',dst,'eth_header.src',src)
        #arp header
        arp_header = pkt.get_protocols(arp.arp)
        #ipv4 and udp header
        ip_header = pkt.get_protocol(ipv4.ipv4)
        udp_header = pkt.get_protocol(udp.udp)
        #print('ip_header',ip_header,'udp_header',udp_header)

        # ignore lldp packet and ipv6
        if eth_header.ethertype == ether_types.ETH_TYPE_LLDP or eth_header.ethertype == ether_types.ETH_TYPE_IPV6:
            return

        #print('eth_header.ethertype',eth_header.ethertype)

        # ignore interfaces between switches
        if self.port_features and (self.port_features.get(dpid).get(in_port)[2] != 0):
            #print('11111111111','self.port_features',self.port_features,'self.port_features.get(dpid).get(in_port)[2]',self.port_features.get(dpid).get(in_port)[2])
            #get ARP header to record ip_to_port
            if arp_header:
                #print('ip_to_port')
                for p in arp_header:
                    key = (dpid, in_port)
                    value = p.src_ip
                    self.ip_to_port.setdefault(key, value)

            # get udp info and host delay
            '''
            if ip_header:
                print('ip_header',ip_header)
                if udp_header:
                    print('udp_header',udp_header)
                    if udp_header.dst_port:
                        print('udp_header.dst_port',udp_header.dst_port)
            '''
            if ip_header and udp_header and (udp_header.dst_port == 12345):
                #print('222222222222','arp_header',arp_header,'ip_header',ip_header,'udp_header',udp_header,'udp_header.dst_port',udp_header.dst_port)
                self._parse_udp(dpid, in_port, msg.data)
                self._save_udp(self.osd_info, self.ip_to_port, self.host_info)
                #print('packet_in:self.osd_info',self.osd_info)
                #self.logger.info(msg)
                #self.logger.info(pkt)

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            #out_port = ofproto.OFPP_CONTROLLER
            out_port = ofproto.OFPP_FLOOD
        # mac of OSD_Client.py (def _send_date():
        #                            HOST = '172.25.1.11')

        #if dst == 'ff:ff:ff:ff:ff:ff':
            #print('out_port = ofproto.OFPP_CONTROLLER')
            #out_port = ofproto.OFPP_CONTROLLER

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        #print('data',data)

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        """
            Save flow stats reply info into self.flow_stats.
            Calculate flow speed and Save it.
        """
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.stats['flow'][dpid] = body
        #print('body++++++++++++++++++')
        #print(body)
        self.flow_stats.setdefault(dpid, {})
        self.flow_speed.setdefault(dpid, {})
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match.get('in_port'),
                                             flow.match.get('eth_dst'))):
            key = (stat.match['in_port'],  stat.match.get('eth_dst'),
                   stat.instructions[0].actions[0].port)
            value = (stat.packet_count, stat.byte_count,
                     stat.duration_sec, stat.duration_nsec)
            self._save_stats(self.flow_stats[dpid], key, value, 5)

            #print('is stats now +++++++++++++++++++')
            #print(stat)

            # Get flow's speed.
            pre = 0
            period = setting.MONITOR_PERIOD
            tmp = self.flow_stats[dpid][key]
            if len(tmp) > 1:
                pre = tmp[-2][1]
                period = self._get_period(tmp[-1][2], tmp[-1][3],
                                          tmp[-2][2], tmp[-2][3])

            speed = self._get_speed(self.flow_stats[dpid][key][-1][1],
                                    pre, period)

            self._save_stats(self.flow_speed[dpid], key, speed, 5)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        """
            Save port's stats info
            Calculate port's speed and save it.
        """
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.stats['port'][dpid] = body

        for stat in sorted(body, key=attrgetter('port_no')):
            port_no = stat.port_no
            if port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (dpid, port_no)
                value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                         stat.duration_sec, stat.duration_nsec)

                self._save_stats(self.port_stats, key, value, 5)

                # Get port speed.
                pre = 0
                period = setting.MONITOR_PERIOD
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(tmp[-1][3], tmp[-1][4],
                                              tmp[-2][3], tmp[-2][4])

                speed = self._get_speed(
                    self.port_stats[key][-1][0] + self.port_stats[key][-1][1],
                    pre, period)

                self._save_stats(self.port_speed, key, speed, 5)
                self._save_freebandwidth(dpid, port_no, speed)
                # save ip free bandwidth
                self._save_ipfreebw(self.free_bandwidth, self.ip_to_port, self.host_info)

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        """
            Save port description info.
        """
        msg = ev.msg
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        config_dict = {ofproto.OFPPC_PORT_DOWN: "Down",
                       ofproto.OFPPC_NO_RECV: "No Recv",
                       ofproto.OFPPC_NO_FWD: "No Farward",
                       ofproto.OFPPC_NO_PACKET_IN: "No Packet-in"}

        state_dict = {ofproto.OFPPS_LINK_DOWN: "Down",
                      ofproto.OFPPS_BLOCKED: "Blocked",
                      ofproto.OFPPS_LIVE: "Live"}

        ports = []
        for p in ev.msg.body:
            ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
                         'state=0x%08x curr=0x%08x advertised=0x%08x '
                         'supported=0x%08x peer=0x%08x curr_speed=%d '
                         'max_speed=%d' %
                         (p.port_no, p.hw_addr,
                          p.name, p.config,
                          p.state, p.curr, p.advertised,
                          p.supported, p.peer, p.curr_speed,
                          p.max_speed))

            if p.config in config_dict:
                config = config_dict[p.config]
            else:
                config = "up"

            if p.state in state_dict:
                state = state_dict[p.state]
            else:
                state = "up"

            port_feature = (config, state, p.curr_speed*100)
            self.port_features[dpid][p.port_no] = port_feature

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        """
            Handle the port status changed event.
        """
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        reason_dict = {ofproto.OFPPR_ADD: "added",
                       ofproto.OFPPR_DELETE: "deleted",
                       ofproto.OFPPR_MODIFY: "modified", }

        if reason in reason_dict:

            print("switch%d: port %s %s" % (dpid, reason_dict[reason], port_no))
        else:
            print("switch%d: Illeagal port state %s %s" % (port_no, reason))

    def show_stat(self, type):
        '''
            Show statistics info according to data type.
            type: 'port' 'flow'
        '''
        if setting.TOSHOW is False:
            return

        bodys = self.stats[type]
        if(type == 'flow'):
            print('datapath         ''   in-port        ip-dst      '
                  'out-port packets  bytes  flow-speed(B/s)')
            print('---------------- ''  -------- ----------------- '
                  '-------- -------- -------- -----------')
            for dpid in bodys.keys():
                for stat in sorted(
                    [flow for flow in bodys[dpid] if flow.priority == 1],
                    key=lambda flow: (flow.match.get('in_port'),
                                      flow.match.get('eth_dst'))):
                    print('%016x %8x %17s %8x %8d %8d %8.1f' % (
                        dpid,
                        stat.match['in_port'], stat.match['eth_dst'],
                        stat.instructions[0].actions[0].port,
                        stat.packet_count, stat.byte_count,
                        abs(self.flow_speed[dpid][
                            (stat.match.get('in_port'),
                            stat.match.get('eth_dst'),
                            stat.instructions[0].actions[0].port)][-1])))
            print('\n')

        if(type == 'port'):
            print('datapath             port   ''rx-pkts  rx-bytes rx-error '
                  'tx-pkts  tx-bytes tx-error  port-speed(B/s)'
                  ' current-capacity(Kbps)  '
                  'port-stat   link-stat')
            print('----------------   -------- ''-------- -------- -------- '
                  '-------- -------- -------- '
                  '----------------  ----------------   '
                  '   -----------    -----------')
            format = '%016x %8x %8d %8d %8d %8d %8d %8d %8.1f %16d %16s %16s'
            for dpid in bodys.keys():
                for stat in sorted(bodys[dpid], key=attrgetter('port_no')):
                    if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                        print(format % (
                            dpid, stat.port_no,
                            stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                            stat.tx_packets, stat.tx_bytes, stat.tx_errors,
                            abs(self.port_speed[(dpid, stat.port_no)][-1]),
                            self.port_features[dpid][stat.port_no][2],
                            self.port_features[dpid][stat.port_no][0],
                            self.port_features[dpid][stat.port_no][1]))
            print('\n')
