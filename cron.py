import time, socket, struct, mysql.connector, config, sys, os
from DCPx_functions import *
from RTU_data import *
recvtimeout = 0.5

"""
To schedule a cron job every minute use this line of code in crontab
* * * * * python3 /home/pi/Documents/dcpx-master-interrogator/cron.py > /dev/null
"""

RTU_list = []

db_cnx = mysql.connector.connect(user=config.username, password=config.password, database='project6db')
db_cursor = db_cnx.cursor(buffered=True)
db_cursor.execute("SELECT rtu_id, rtu_ip, rtu_port, type, display_count FROM rtu_list")

# capturing the state of standing alarms in a list before any operations
db_cursor_before = db_cnx.cursor(buffered=True)
db_cursor_before.execute("SELECT rtu_id, display, point, description, is_set FROM standing_alarms")
list_before = db_cursor_before.fetchall()

# getting the rtu-s to process and putting then in the list
for id, ip, port, rtu_type, display_count in db_cursor:
    RTU_list.append(RTU_data(id=id, ip=ip, port=port, rtu_type=rtu_type, display_count=display_count))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('192.168.1.100', 10000)
try:
    sock.bind(server_address)
except:
    pass

def get_RTU_i(id):
    for i in range(len(RTU_list)):
        if RTU_list[i].id == id:
            return i
    return -1

def listening_thread(rtu):
    timeout = time.time() + recvtimeout
    sock.settimeout(recvtimeout)
    while time.time() < timeout:
        # print('\nwaiting to receive message')
        try:
            data, address = sock.recvfrom(1024)
        except:
            continue
        else:
            data_list = bytearray(data)
            # print('received %s bytes from %s' % (len(data), address))
            # print(' '.join(hex(i)[2:] for i in bytearray(data_list)))
            if (DCP_is_valid_response(data_list) and rtu.rtu_type == 'arduino'):
                if get_RTU_i(data_list[2])  == -1:
                    print("No RTU found with an id of %s" % data_list[2])
                else:
                    rtu = RTU_list[get_RTU_i(data_list[2])]
                    DCP_process_response(data_list,rtu)
            elif (rtu.rtu_type == "temp_def_g2"):
                DCP_process_response(data_list,rtu)
                # print(rtu.display_data)

if __name__ == '__main__':
    # updating the event history database
    for rtu in RTU_list:
        print(rtu)
        buff = []
        if rtu.rtu_type == 'arduino':
            buff = bytearray(DCP_buildPoll(rtu.id, DCP_op_lookup(DCP_op_name.FUDR)))
        elif rtu.rtu_type == 'temp_def_g2':
            buff = bytearray([0xAA, 0xFC, 0x04, 0x03, 0xCE])
        DCP_compress_AA_byte(buff)
        sent = sock.sendto(buff, (rtu.ip, rtu.port))
        print("\nsending for RTU %s with array size of %i" %(rtu.id, len(buff)))
        print(buff)
        listening_thread(rtu)

        # testing some alarm points
        if (len(rtu.display_data) == 22):
            print(rtu.display_data[5])

        if rtu.rtu_type == 'arduino':
            db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('temp', 1, %s, %s, 'c')", (rtu.current_data.temp, rtu.id))
            db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('hum', 2, %s, %s, '%')", (rtu.current_data.hum, rtu.id))

    # updating the standing alarms table
    for rtu in RTU_list:
        # print(rtu.id)
        if rtu.rtu_type == 'arduino':
            alarm_desc = ["mj_und","mn_und","mn_ovr","mj_ovr"]
            for i in range(1, 3): #1 for temp display, 2 for humidity
                for j in range (1, 5): #points 1-4 for temp and humidity
                    db_cursor.execute("SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = %s AND display = %s AND point = %s", (rtu.id, i, j)) #selecting the temp display
                    if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
                        query = """INSERT INTO standing_alarms(rtu_id, display, point, type, description, unit, threshold_value, analog_value)
                                VALUES ({}, {}, {}, {}, {}, {}, {}, {})""".format(rtu.id, i, j, "analog", alarm_desc[j-1], ("c" if i == 1 else "%"), rtu.thresholds[j-1], (rtu.current_data.temp if i == 1 else rtu.current_data.hum))
                        db_cursor.execute(query)
                    else:
                        query = """UPDATE standing_alarms SET analog_value = {} WHERE rtu_id = {} AND display = {} AND point = {}""".format((rtu.current_data.temp if i == 1 else rtu.current_data.hum), rtu.id, i, j)
                        db_cursor.execute(query)
            # updating the link status of arduinos
            db_cursor.execute("SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = %s AND display = 3 AND point = 1", (rtu.id,)) #selecting the link status display
            if db_cursor.fetchone()[0] == 0: # if link alarm does not exist then add one
                query = """INSERT INTO standing_alarms(rtu_id, display, point, type, description, long_desc)
                        VALUES ({}, 3, 1, 'discrete', 'link_failed', 'link_failed')""".format(rtu.id)
                db_cursor.execute(query)
            link_status = os.system("ping -c 1 -w 1 " + rtu.ip)
            db_cursor.execute("UPDATE rtu_list SET link = %s WHERE rtu_id = %s", ((1 if link_status == 0 else 0), rtu.id))
            db_cursor.execute("UPDATE standing_alarms SET is_set = %s WHERE rtu_id = %s AND display = 3 AND point = 1", ((0 if link_status == 0 else 1), rtu.id))


    db_cursor.execute("SELECT alarm_id, rtu_id, display, point, description, is_set, threshold_value, analog_value FROM standing_alarms")
    db_cursor_second = db_cnx.cursor(buffered=True)
    for alarm_id, rtu_id, display, point, description, is_set, threshold_value, analog_value in db_cursor:
        if ((description == "mj_und" or description == "mn_und") and ((analog_value <= threshold_value and is_set == 0) or (analog_value > threshold_value and is_set == 1))):
            db_cursor_second.execute("UPDATE standing_alarms SET is_set = %s WHERE alarm_id = %s", ((0 if is_set else 1),alarm_id))

        if ((description == "mn_ovr" or description == "mj_ovr") and ((analog_value >= threshold_value and is_set == 0) or (analog_value < threshold_value and is_set == 1))):
            db_cursor_second.execute("UPDATE standing_alarms SET is_set = %s WHERE alarm_id = %s", ((0 if is_set else 1),alarm_id))



    # comparing the before and after states of standing alarms and adding  COS in event history if there is a change
    db_cursor.execute("SELECT rtu_id, display, point, description, is_set FROM standing_alarms")
    list_after = db_cursor.fetchall()
    for i in range(len(list_before)):
        if list_before[i] != list_after[i]: # if chere is a change of state
            cos_query = """INSERT INTO event_history(type, description, rtu_id, display, point, value) VALUES ('COS', '{}', {}, {}, {}, {})
                            """.format(list_after[i][3], list_after[i][0], list_after[i][1], list_after[i][2], list_after[i][4])
            db_cursor.execute(cos_query)



    sock.close()
    db_cnx.commit()
    db_cnx.close()
