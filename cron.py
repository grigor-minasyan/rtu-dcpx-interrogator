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

# setting the analog_start and analog_end values
for rtu in RTU_list:
    db_cursor.execute(f"SELECT analog_start, analog_end FROM rtu_types WHERE rtu_type_name = '{rtu.rtu_type}'")
    result = db_cursor.fetchone()
    rtu.analog_start = result[0]
    rtu.analog_end = result[1]


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
            # print('rec %s byt frm %s-%s' % (len(data), address, (' '.join(str(i) for i in bytearray(data_list)))))
            if DCP_is_valid_response(data_list):
                if (get_RTU_i(data_list[2])  == -1 and rtu.rtu_type == "arduino"):
                    print("No RTU found with an id of %s" % data_list[2])
                else:
                    DCP_process_response(data_list,rtu)

if __name__ == '__main__':
    # updating the event history database
    for rtu in RTU_list:
        print(rtu)
        buff = []
        buff = bytearray(DCP_buildPoll(rtu.id, DCP_op_lookup(DCP_op_name.FUDR)))
        DCP_compress_AA_byte(buff)
        sent = sock.sendto(buff, (rtu.ip, rtu.port))
        print("\nsending for RTU %s with array size of %i" %(rtu.id, len(buff)))
        print(buff)
        listening_thread(rtu)

        # calculating analog values
        if rtu.rtu_type == "temp_def_g2":
            rtu.process_analogs(rtu.analog_start, rtu.analog_end)
            # for x in rtu.display_data:
            #     print(*x, sep = ' ')
 
        if rtu.rtu_type == 'arduino':
            db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('temp', 1, %s, %s, 'c')", (rtu.current_data.temp, rtu.id))
            db_cursor.execute("INSERT INTO event_history(type, display, value, rtu_id, unit) VALUES ('hum', 2, %s, %s, '%')", (rtu.current_data.hum, rtu.id))

    # updating the standing alarms table
    for rtu in RTU_list:
        # print(rtu.id)
        if rtu.rtu_type == 'arduino':
            alarm_desc = ["major under","minor under","minor over","major over"]
            for i in range(1, 3): #1 for temp display, 2 for humidity
                for j in range (1, 5): #points 1-4 for temp and humidity
                    db_cursor.execute("SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = %s AND display = %s AND point = %s", (rtu.id, i, j)) #selecting the temp display
                    if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
                        query = f"""INSERT INTO standing_alarms(rtu_id, display, point, type, description, unit, threshold_value, analog_value)
                                VALUES ({rtu.id}, {i}, {j}, 'analog', '{alarm_desc[j-1]}', '{("c" if i == 1 else "%")}', {rtu.thresholds[j-1]}, {rtu.current_data.temp if i == 1 else rtu.current_data.hum})"""
                        db_cursor.execute(query)
                    else:
                        query = """UPDATE standing_alarms SET analog_value = {} WHERE rtu_id = {} AND display = {} AND point = {}""".format((rtu.current_data.temp if i == 1 else rtu.current_data.hum), rtu.id, i, j)
                        db_cursor.execute(query)

        if rtu.rtu_type == "temp_def_g2":

            # processing discrete alarms
            for i in range (1, rtu.analog_start):
                for j in range(1, 65):
                    select_query = f"SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = {rtu.id} AND display = {i} AND point = {j}"
                    db_cursor.execute(select_query) 
                    if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
                        insert_query = f"""INSERT INTO standing_alarms(rtu_id, display, point, type, description, is_set)
                                VALUES ({rtu.id}, {i}, {j}, 'discrete', '{get_point_description(rtu.rtu_type, i, j)}', {rtu.display_data[i-1][j-1]})"""
                        db_cursor.execute(insert_query)
                    else:
                        query = f"""UPDATE standing_alarms SET is_set = {rtu.display_data[i-1][j-1]} WHERE rtu_id = {rtu.id} AND display = {i} AND point = {j}"""
                        db_cursor.execute(query)


            # proccessing the analogs
            for i in range (rtu.analog_start, rtu.analog_end+1):
                # this for loop for left and right parts of the display
                for k in range(0, 33, 32):
                    value = rtu.display_data[i-1][9+k]
                    enable = rtu.display_data[i-1][8+k]
                    if enable:
                        insert_query = f"""INSERT INTO event_history(type, description, display, point, value, rtu_id, unit)
                                        VALUES ('{'analog' if i < 7 else 'digital'}', '{get_point_description(rtu.rtu_type, i, 17+k)}', {i}, {k+1}, {value}, {rtu.id}, '{'v' if i < 7 else 'c'}')"""
                        db_cursor.execute(insert_query)

                    for j in range(1+k, 5+k):
                        select_query = f"SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = {rtu.id} AND display = {i} AND point = {j}"
                        db_cursor.execute(select_query) 
                        if db_cursor.fetchone()[0] == 0: # insert the alarm into the table if doesnt exist
                            insert_query = f"""INSERT INTO standing_alarms(rtu_id, display, point, type, description, is_enabled, threshold_value, analog_value, unit)
                                    VALUES ({rtu.id}, {i}, {j}, 'analog', '{get_point_description(rtu.rtu_type, i, j)}', {enable}, {j}, {value}, '{'v' if i < 7 else 'c'}')"""
                            db_cursor.execute(insert_query)
                        else:
                            update_query = f"""UPDATE standing_alarms SET analog_value = {value}, is_enabled = {enable} WHERE rtu_id = {rtu.id} AND display = {i} AND point = {j}"""
                            db_cursor.execute(update_query)


        # updating the link status of arduinos
        db_cursor.execute("SELECT COUNT(alarm_id) FROM standing_alarms WHERE rtu_id = %s AND display = 0 AND point = 1", (rtu.id,)) #selecting the link status display
        if db_cursor.fetchone()[0] == 0: # if link alarm does not exist then add one
            query = """INSERT INTO standing_alarms(rtu_id, display, point, type, description, long_desc)
                    VALUES ({}, 0, 1, 'discrete', 'link_failed', 'link_failed')""".format(rtu.id)
            db_cursor.execute(query)
        link_status = os.system("ping -c 1 -w 1 " + rtu.ip)
        db_cursor.execute("UPDATE rtu_list SET link = %s WHERE rtu_id = %s", ((1 if link_status == 0 else 0), rtu.id))
        db_cursor.execute("UPDATE standing_alarms SET is_set = %s WHERE rtu_id = %s AND display = 0 AND point = 1", ((0 if link_status == 0 else 1), rtu.id))



    # setting flags for major and minor analogs
    db_cursor.execute("SELECT alarm_id, display, point, description, is_set, threshold_value, analog_value FROM standing_alarms WHERE type = 'analog'")
    db_cursor_second = db_cnx.cursor(buffered=True)
    for alarm_id, display, point, description, is_set, threshold_value, analog_value in db_cursor:
        under = ["minor under", "major under"]
        if (any(x in description for x in under) and ((analog_value <= threshold_value and is_set == 0) or (analog_value > threshold_value and is_set == 1))):
            db_cursor_second.execute("UPDATE standing_alarms SET is_set = %s WHERE alarm_id = %s", ((0 if is_set else 1),alarm_id))

        over = ["minor over", "major over"]
        if (any(x in description for x in over) and ((analog_value >= threshold_value and is_set == 0) or (analog_value < threshold_value and is_set == 1))):
            db_cursor_second.execute("UPDATE standing_alarms SET is_set = %s WHERE alarm_id = %s", ((0 if is_set else 1),alarm_id))



    # comparing the before and after states of standing alarms and adding  COS in event history if there is a change
    db_cursor.execute("SELECT rtu_id, display, point, description, is_set FROM standing_alarms")
    list_after = db_cursor.fetchall()
    for i in range(len(list_before)):
        if list_before[i] != list_after[i]: # if chere is a change of state
            cos_query = f"""INSERT INTO event_history(type, description, rtu_id, display, point, value)
                        VALUES ('COS', '{list_after[i][3]}', {list_after[i][0]}, {list_after[i][1]}, {list_after[i][2]}, {list_after[i][4]})"""
            db_cursor.execute(cos_query)



    sock.close()
    db_cnx.commit()
    db_cnx.close()
