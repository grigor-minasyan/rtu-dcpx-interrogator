# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask, render_template, jsonify, request
from json import JSONEncoder
import threading, time, socket, sys, json, pickle
from DCPx_functions import *
from RTU_data import *
import smtplib

class RTU_data_Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Dttimetemphum):
            return [obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second, obj.temp, obj.hum]
        if isinstance(obj, RTU_data):
            return [obj.id, obj.thresholds, obj.alarms_binary, obj.current_data, list(obj.history)]
        return json.JSONEncoder.default(self, obj)



RTU_list = []
RTU_list = pickle.load(open('./master-server/stored_RTUs.pkl', 'rb'))

# RTU_list.append(RTU_data(id=2, ip='192.168.1.102', port=8888))
# RTU_list.append(RTU_data(id=3, ip='192.168.1.103', port=8888))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('192.168.1.101', 10000)
sock.bind(server_address)

def get_RTU_i(id):
    for i in range(len(RTU_list)):
        if RTU_list[i].id == id:
            return i
    return -1

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)

# The route() function of the Flask class is a decorator,
# which tells the application which URL should call
# the associated function.

def get_arlm_message(num):
    if num == 0b1100:
        return 'Subject: {}\n\n{}'.format("Alarm MJ UNDER and MN UNDER", "Alarm MJ UNDER and MN UNDER")
    if num == 0b0100:
        return 'Subject: {}\n\n{}'.format("Alarm MN UNDER", "Alarm MN UNDER")
    if num == 0b0011:
        return 'Subject: {}\n\n{}'.format("Alarm MJ OVER and MN OVER", "Alarm MJ OVER and MN OVER")
    if num == 0b0010:
        return 'Subject: {}\n\n{}'.format("Alarm MN OVER", "Alarm MN OVER")
    if num == 0b0000:
        return 'Subject: {}\n\n{}'.format("Alarms clear, comfortable", "Alarms clear, comfortable")

def listening_thread():
    # function to continuously check for UDP
    while True:
        # print('\nwaiting to receive message')
        data, address = sock.recvfrom(1024)
        data_list = bytearray(data)
        # print('received %s bytes from %s' % (len(data), address))
        # print(':'.join(x.encode('hex') for x in data))
        if len(data_list) > 3:
            # print(' '.join(hex(i)[2:] for i in bytearray(data_list)))
            if DCP_is_valid_response(data_list):
                if get_RTU_i(data_list[2])  == -1:
                    print("No RTU found with an id of %s" % data_list[2])
                else:
                    rtu = RTU_list[get_RTU_i(data_list[2])]
                    DCP_process_response(data_list,rtu)
                    if rtu.alarms_binary != rtu.prev_alarm_state:
                        rtu.set_prev_alarm_state(rtu.alarms_binary)
                        smtplib.SMTP('localhost').sendmail('RTU'+str(rtu.id)+'@master.com', ['master@master.com'], get_arlm_message(rtu.alarms_binary))



# @app.route('/')
# def main():
#     return render_template("home.html")
#
# # responding to JSON request
# @app.route('/_update_cur_temp/<rtu_id>')
# def update_cur_temp(rtu_id):
#     pickle.dump(RTU_list, open('./master-server/stored_RTUs.pkl', 'wb')) #change the location of this line
#     # sending a request to RTU
#     if get_RTU_i(int(rtu_id)) == -1:
#         print("no rtu found with id of %s" % rtu_id)
#         return
#     rtu = RTU_list[get_RTU_i(int(rtu_id))]
#     buff = bytearray(DCP_buildPoll(int(rtu_id), DCP_op_lookup(DCP_op_name.FUDR)))
#     DCP_compress_AA_byte(buff)
#     sent = sock.sendto(buff, (rtu.ip, rtu.port))
#     print("sending data for RTU %s with array size of %i" %(rtu_id, len(rtu.history)))
#     return json.dumps(rtu, indent=4, cls=RTU_data_Encoder)

# @app.route('/_monitor_new_rtu/<ip>/<port>/<rtu_id>')
# def monitor_new_rtu(ip, port, rtu_id):
#     if len([x for x in RTU_list if (x.ip == ip or x.id == rtu_id)]) > 0:
#         return jsonify(success = False, message = 'Failed, an RTU with the same IP or ID exists')
#     RTU_list.append(RTU_data(int(rtu_id), ip, int(port)))
#     pickle.dump(RTU_list, open('./master-server/stored_RTUs.pkl', 'wb'))
#     return jsonify(success = True, message = 'RTU added Successfully')
#
# @app.route('/_remove_device/<rtu_id>')
# def remove_device(rtu_id):
#     if get_RTU_i(int(rtu_id)) == -1:
#         print("no rtu found with id of %s" % rtu_id)
#         return jsonify(success = False, message = 'Failed, no RTU found with an ID of %s' %rtu_id)
#     RTU_list.pop(get_RTU_i(int(rtu_id)))
#     pickle.dump(RTU_list, open('./master-server/stored_RTUs.pkl', 'wb'))
#     return jsonify(success = True, message = 'Successfully removed the RTU with an ID of %s' %rtu_id)
#
# @app.route('/_get_id_list/')
# def get_id_list():
#     temp_arr = []
#     for rtu in RTU_list:
#         temp_arr.append(rtu.id)
#     return json.dumps(temp_arr)

# main driver function
if __name__ == '__main__':
    t1 = threading.Thread(target=app.run)
    listen = threading.Thread(target=listening_thread)
    t1.setDaemon(True)
    listen.setDaemon(True)
    t1.start()
    listen.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting")
        exit(0)
