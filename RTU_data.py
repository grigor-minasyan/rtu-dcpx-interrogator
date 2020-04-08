from json import JSONEncoder
# import functools


"""
def compare_Dttimetemphum(item1, item2):
    if item1.year != item2.year:
        return item1.year - item2.year
    elif item1.month != item2.month:
        return item1.month - item2.month
    elif item1.day != item2.day:
        return item1.day - item2.day
    elif item1.hour != item2.hour:
        return item1.hour - item2.hour
    elif item1.minute != item2.minute:
        return item1.minute - item2.minute
    elif item1.second != item2.second:
        return item1.second - item2.second
    else:
        return 0
"""

class Dttimetemphum:
    year = 0
    month = 0
    day = 0
    hour = 0
    minute = 0
    second = 0
    temp = 0
    hum = 0
    def __init__(self,year = 0, month = 0, day = 0, hour = 0, minute = 0, second = 0, temp = 0, hum = 0):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.temp = temp
        self.hum = hum
    def __str__(self):
        ret = ""
        ret += str(self.year) + "/" +str(self.month) + "/" +str(self.day) + " "
        ret += str(self.hour) + ":" +str(self.minute) + ":" +str(self.second) + " "
        ret += str(self.temp) + 'C ' + str(self.hum) + '%'
        return ret
    def __eq__(self, other):
        if isinstance(other, Dttimetemphum):
            return (self.year == other.year and self.month == other.month and self.day == other.day and self.hour == other.hour and self.minute == other.minute and self.second == other.second and self.temp == other.temp and self.hum == other.hum)
        return False
    def __hash__(self):
        return hash(tuple([self.year, self.month, self.day, self.hour, self.minute, self.second, self.temp, self.hum]))


class RTU_data:
    def __init__(self, id, ip, port):
        self.id = id
        self.thresholds = [0,0,0,0]
        self.alarms_binary = 0
        self.prev_alarm_state = 0
        self.current_data = Dttimetemphum()
        self.history = set()
        self.ip = ip
        self.port = port
    def set_id(self, id):
        self.id = id
    def set_thresholds(self, list):
        for i in range(4):
                self.thresholds[i] = list[i]
    def set_alarms_binary(self, a):
        self.alarms_binary = a
    def add_hist(self, new_data):
        self.history.add(new_data)
        # sorted(self.history, key=functools.cmp_to_key(compare_Dttimetemphum))
    def set_current_data(self, dttimetemphum):
        self.current_data = dttimetemphum
    def set_prev_alarm_state(self, a):
        self.prev_alarm_state = a
    def __str__(self):
        ret = ""
        ret += 'ID: '+str(self.id) + '\n'
        ret += 'Thresholds ' + str(self.thresholds) + '\n'
        ret += 'Current_data ' + str(self.current_data) + '\n'
        ret += 'NUmber of data points ' + str(len(self.history))
        return ret
