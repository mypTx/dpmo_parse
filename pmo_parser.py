# coding=utf-8

import csv, time
import telegram
from netmiko import ConnectHandler
from pysnmp.entity.rfc3413.oneliner import cmdgen

bot = telegram.Bot("1548561322:AAE3dOMk3i_OP0HXFxbMHKDCurJBLFRQfRc")

f = open("connections.csv")
rc = csv.reader(f)
hosts = []
for row in rc:
    if row[0] == "ssh":
        hosts.append({"type": "ssh", "ip": row[1], "user": row[2], "pass": row[3]})
    elif row[0] == "snmp":
        hosts.append({"type": "snmp", "ip": row[1], "cmnty": row[2], "oids": row[3]})
    else:
        print(f'unexpected host type "{row[0]}"')
        print(f'unexpected host type "{row[0]}"')
        continue

print("Loaded", len(hosts), "hosts")

#config
ssh_comnds = [
    'display transceiver interface gigabitEthernet 0/0/1 verbose',
    'display transceiver interface gigabitEthernet 0/0/0 verbose'
]

nR, mR = 2, 5

#main block
while True:
    for host in hosts:
        try:
            print(f'Connecting to {host["type"]}://{host["ip"]}')
            infolist = None
            if host["type"] == "ssh":
                # идёт опрос железки через CLI напрямую
                ssh_c = ConnectHandler(**{"device_type": "huawei",
                                          "ip": host["ip"],
                                          "username": host["user"],
                                          "password": host["pass"]})
                output = ssh_c.send_config_set(ssh_comnds, delay_factor=.5, exit_config_mode=False)
                promt = ssh_c.find_prompt()
                infolist = output.replace("--", ""). \
                    replace("-\n", ""). \
                    replace(":", " = "). \
                    replace("  ", ""). \
                    replace("(dBM)", ""). \
                    splitlines()
                ssh_c.disconnect()
                infolist = list(filter(lambda str: str.find("Current") == 0, infolist))
                print("\n".join(infolist))

            elif host["type"] == "snmp":
                # опрос железки по SNMP с помощью getbulk
                err, errs, erri, vbt = cmdgen.CommandGenerator().bulkCmd(
                cmdgen.CommunityData(host["cmnty"]),
                cmdgen.UdpTransportTarget(host["ip"], 161),
                nR, mR,
                host["oids"])
                row = []
                if errorIndication:
                    raise Exception("snmp engine error")
                if errorStatus:
                    raise Exception("snmp pdu error: %s at %s\n" % (errorStatus.prettyPrint(),
                              errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
                    ))
                non_Rep = vbt.pop(0)
                for name, val in non_Rep:
                    row.append((name.prettyPrint(), val.prettyPrint()))
                for r in vbt:
                    r = r[nR:]
                    for name, val in r:
                        row.append((name.prettyPrint(), val.prettyPrint()))
                print("\n".join(row))
                infolist = row
            else:
                raise Exception("unexpected host type")
#
            # отпрвка конечной информации боту в telegram
            if (infolist is not None):
                bot.send_message("-447590381", "\n".join(infolist))
                print("sending to tg")
        except Exception as e:
            print("---exception---")
            print(type(e))
            print(e)
            print("---exception end---")
            pass
    time.sleep(15)
