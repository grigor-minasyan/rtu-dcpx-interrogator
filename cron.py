import time, socket, struct, mysql.connector, config, sys
from DCPx_functions import *
from RTU_data import *
recvtimeout = 1

"""
To schedule a cron job every minute use this line of code in crontab
* * * * * python3 /home/pi/Documents/dcpx-master-interrogator/cron.py > /dev/null
"""

RTU_list = []

db_cnx = mysql.connector.connect(user=config.username, password=config.password, database='project6db')
db_cursor = db_cnx.cursor(buffered=True)
db_cursor.execute("SELECT * FROM rtu_list")

# getting the rtu-s to process and putting then in the list
for id, ip, port, type in db_cursor:
    RTU_list.append(RTU_data(id=id, ip=ip, port=port))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('192.168.1.100', 10000)
sock.bind(server_address)

def get_RTU_i(id):
    for i in range(len(RTU_list)):
        if RTU_list[i].id == id:
            return i
    return -1

def listening_thread():
    timeout = time.time() + recvtimeout
    sock.settimeout(recvtimeout)
    while time.time() < timeout:
        print('\nwaiting to receive message')
        try:
            data, address = sock.recvfrom(1024)
        except:
            continue
        else:
            data_list = bytearray(data)
            print('received %s bytes from %s' % (len(data), address))
            print(' '.join(hex(i)[2:] for i in bytearray(data_list)))
            if DCP_is_valid_response(data_list):
                if get_RTU_i(data_list[2])  == -1:
                    print("No RTU found with an id of %s" % data_list[2])
                else:
                    rtu = RTU_list[get_RTU_i(data_list[2])]
                    DCP_process_response(data_list,rtu)

if __name__ == '__main__':
    # updating the event history database
    for rtu in RTU_list:
        buff = bytearray(DCP_buildPoll(rtu.id, DCP_op_lookup(DCP_op_name.FUDR)))
        DCP_compress_AA_byte(buff)
        sent = sock.sendto(buff, (rtu.ip, rtu.port))
        print("\nsending for RTU %s with array size of %i" %(rtu.id, len(buff)))
        print(buff)
        listening_thread()
        db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('temp', 1, %s, %s, 'c')", (rtu.current_data.temp, rtu.id))
        db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('hum', 2, %s, %s, '%')", (rtu.current_data.hum, rtu.id))

        # db_cursor.execute("INSERT INTO event_history(type, value, rtu_id) VALUES ('alm', %s, %s)", (rtu.alarms_binary, rtu.id))

        # db_cursor.execute("INSERT INTO standing_alarms(type, value, rtu_ip, rtu_id) VALUES ('alm', %s, INET_ATON(%s), %s)", (rtu.alarms_binary, rtu.ip, rtu.id))

    # updating the standing alarms table
    for rtu in RTU_list:
        print(rtu.id)
        db_cursor.execute("SELECT COUNT(rtu_id_display) FROM standing_alarms WHERE rtu_id_display = %s", (str(rtu.id) + "_1", )) #selecting the temp display
        if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
            db_cursor.execute("INSERT INTO standing_alarms(rtu_id_display, rtu_id, display, value, mj_und_val, mn_und_val, mn_ovr_val, mj_ovr_val) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (str(rtu.id) + "_1", rtu.id, 1, rtu.current_data.temp, rtu.thresholds[0], rtu.thresholds[1], rtu.thresholds[2], rtu.thresholds[3]))
        else:
            db_cursor.execute("UPDATE standing_alarms SET value = %s WHERE rtu_id_display = %s", (rtu.current_data.temp, str(rtu.id) + "_1"))


        db_cursor.execute("SELECT COUNT(rtu_id_display) FROM standing_alarms WHERE rtu_id_display = %s", (str(rtu.id) + "_2", )) #selecting the hum display
        if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
            db_cursor.execute("INSERT INTO standing_alarms(rtu_id_display,rtu_id,display,value,mj_und_val,mn_und_val,mn_ovr_val,mj_ovr_val) VALUES (%s, %s, %s, %s, 5, 10, 20, 50)", (str(rtu.id) + "_2", rtu.id, 2, rtu.current_data.hum))
        else:
            db_cursor.execute("UPDATE standing_alarms SET value = %s WHERE rtu_id_display = %s", (rtu.current_data.hum, str(rtu.id) + "_2"))

    db_cursor.execute("UPDATE standing_alarms SET mj_und_set = 0, mn_und_set = 0, mn_ovr_set = 0, mj_ovr_set = 0")
    db_cursor.execute("UPDATE standing_alarms SET mj_und_set = 1 WHERE value < mj_und_val")
    db_cursor.execute("UPDATE standing_alarms SET mn_und_set = 1 WHERE value < mn_und_val")
    db_cursor.execute("UPDATE standing_alarms SET mn_ovr_set = 1 WHERE value > mn_ovr_val")
    db_cursor.execute("UPDATE standing_alarms SET mj_ovr_set = 1 WHERE value > mj_ovr_val")

        # list = []
        # list.append(db_cursor.fetchone())
        # print(list)

    db_cnx.commit()
    db_cnx.close()
