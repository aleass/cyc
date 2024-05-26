import argparse

import fitparse
import folium
from matplotlib import pyplot as plt
import numpy as np


class FitObj:
    def get_group(self):
        return {
            'max': 0,  # 最大
            'min': 0,  # 最小
            'sum': 0,  # 合计
            'count': 0,  # 数量
        }
    # file_name 文件名
    # start 步进,用于指定区域数据
    # end  步进
    # strip 间隔,防止太多页面卡顿
    # save 是否存储
    # heart_rate_filter 心率过滤
    def __init__(self, file_name, start, end, strip, save, heart_rate_filter) -> None:
        self.set_config(file_name, start, end, strip, save, heart_rate_filter)

    def set_config(self, name, start, end, strip, save,heart_rate_filter):
        self.heart_rate_filter = heart_rate_filter
        self.name = name
        self.file_name = "data/" + self.name
        self.fitfile = fitparse.FitFile(self.file_name + '.fit')
        self.start = start
        self.end = end
        self.save = save
        self.strip = strip
        self.data_group = {
            'heart_rate': self.get_group(),
            'cadence': self.get_group(),
            'speed': self.get_group(),
        }
        self.center_lat_min = 0
        self.center_lat_max = 0
        self.center_lon_min = 0
        self.center_lon_max = 0
        self.x = []
        self.speed_list = []
        self.rpm_list = []
        self.hpm_list = []
        self.dis_list = []
        self.alt_list = []
        self.altitude_jpg_file = "image/" + self.name + '.altitude.jpg'
        self.jpg_file = "image/" + self.name + '.jpg'
        self.html_file = self.file_name + '.html'
        self.first_time = None
        self.end_time = None

    def parse(self):
        # incidents = folium.map.FeatureGroup()
        self.Markers = []
        # 计数
        count = 0
        first = 0
        distance = 0

        # 迭代
        for record in self.fitfile.get_messages("record"):
            count += 1
            if self.start > 0 and self.end > 0 and (count < self.start or count > self.end):
                continue

            # 坐标
            lat = record.get('position_lat').value
            long = record.get('position_long').value
            if lat is None or long is None:
                continue

            if distance == 0:
                distance = record.get('distance').value

            if record.get('heart_rate').value <= self.heart_rate_filter:
                continue
            if record.get('altitude').value != None and record.get('distance').value != None:
                self.dis_list.append((record.get('distance').value - distance) / 1000)
                self.alt_list.append(record.get('altitude').value)

            # 转换坐标
            lat, long = self.semicircles_to_degrees(lat), self.semicircles_to_degrees(long)

            # 记录最大最小坐标
            if self.center_lat_min > lat or self.center_lat_min == 0:
                self.center_lat_min = lat
            if self.center_lat_max < lat or self.center_lat_max == 0:
                self.center_lat_max = lat

            if self.center_lon_min > long or self.center_lon_min == 0:
                self.center_lon_min = long
            if self.center_lon_max < long or self.center_lon_max == 0:
                self.center_lon_max = long

            # 当没有筛选区间,则跳过10个的数据,防止过大
            if self.start == 0 and self.end == 0:
                self.strip = 15
            if self.strip != 0 and count % self.strip != 0:
                continue

            # 记录折线图数据
            rpm, hpm, speed = 0, 0, 0

            time = record.get('timestamp').value
            if first == 0:
                first = int(time.timestamp())
                self.first_time = time
            self.x.append(int(time.timestamp()) - first)
            self.end_time = time

            # 获取数据
            for key, data in self.data_group.items():
                res = record.get(key).value
                if res is None:
                    res = 0
                data['count'] += 1
                data['sum'] += res
                if data['max'] < res or data['max'] == 0:
                    data['max'] = res
                if data['min'] > res or data['min'] == 0:
                    data['min'] = res
                if key == 'heart_rate':
                    hpm = res
                    self.hpm_list.append(res)
                elif key == 'cadence':
                    rpm = res
                    self.rpm_list.append(res)

                elif key == 'speed':
                    speed = res * 3.6
                    self.speed_list.append(res * 3.6)

                times = time.strftime("%H:%M:%S")
                self.Markers.append(
                    folium.Marker([lat, long],
                                  popup='心率:{}\n踏频:{}\n速度:{} km/h\n时间:{}'.format(hpm, rpm, round(speed, 2),
                                                                                         times)))

    def altitude(self):
        fig, ax = plt.subplots()
        ax.set_ylabel('m')
        ax.set_xlabel('km')
        # 最高
        max_y = max(self.alt_list)
        max_x = self.dis_list[self.alt_list.index(max_y)]
        plt.text(max_x, max_y, f'dis:{round(max_y, 2)} m \nhigh:{round(max_x, 2)} km')
        # 最低
        min_y = min(self.alt_list)
        min_x = self.dis_list[self.alt_list.index(min_y)]
        plt.text(min_x, min_y, f'{round(min_y, 2)}')
        ax.plot(self.dis_list, self.alt_list)
        # 展示图形
        plt.savefig(self.altitude_jpg_file)

    def table(self):
        # 创建第一条折线图
        fig = plt.figure(figsize=(10, 4))
        ax1 = fig.add_subplot(111)
        color = 'tab:red'
        ax1.set_ylabel('hpm', color=color)
        ax1.plot(self.x, self.hpm_list, color=color, alpha=0.8)
        ax1.tick_params(axis='y', labelcolor=color, color=color)
        plt.locator_params(axis='y', nbins=15)

        # 创建第二个y轴
        box = ax1.get_position()
        ax2 = ax1.twinx()

        color = 'tab:blue'
        ax2.set_ylabel('km/s', color=color)
        ax2.plot(self.x, self.speed_list, color=color, alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=color, color=color)
        ax2.spines['right'].set_position(('axes', 1.1))
        plt.locator_params(axis='y', nbins=10)

        # 创建第三个y轴
        ax3 = ax1.twinx()
        color = 'tab:green'
        ax3.spines['left'].set_position(('axes', 0))  # 调整第三个y轴的位置
        ax3.set_ylabel('rpm', color=color)
        ax3.plot(self.x, self.rpm_list, color=color, alpha=0.8)
        ax3.tick_params(axis='y', labelcolor=color)
        plt.locator_params(axis='y', nbins=10)

        ax1.set_position([box.x0 - 0.05, box.y0, box.width, box.height])
        ax1.set_xlabel('second')
        # plt.xticks([])  # 禁用 x 轴坐标
        plt.locator_params(axis='x', nbins=25)
        plt.gcf().set_size_inches(15, 5)  # 长宽
        # 添加标题
        plt.title(self.name)
        # 展示图形
        plt.savefig(self.jpg_file)

    def finish(self):
        coordinate = [(self.center_lat_min + self.center_lat_max) / 2,
                      (self.center_lon_min + self.center_lon_max) / 2]
        world_map = folium.Map(zoom_start=16, location=coordinate)

        layer2 = folium.FeatureGroup(name='描点数据')
        folium.Marker(coordinate,
                      icon=folium.Icon(color='red'),
                      popup="""平均心率:{}
                            最大心率:{}
                            最小心率:{}
                            平均踏频:{}
                            最大踏频:{}
                            最小踏频:{}
                            平均速度:{}km/h
                            最大速度:{}km/h
                            最小速度:{}km/h
                            距离:{}km
                            高度:{}m
                            时间:{}""".
                      format(
                          round(self.data_group['heart_rate']['sum'] / self.data_group['heart_rate']['count'], 2),
                          self.data_group['heart_rate']['max'], self.data_group['heart_rate']['min'],

                          int(self.data_group['cadence']['sum'] / self.data_group['cadence']['count']),
                          self.data_group['cadence']['max'], self.data_group['cadence']['min'],

                          round(self.data_group['speed']['sum'] / self.data_group['speed']['count'] * 3.6, 2),
                          round(self.data_group['speed']['max'] * 3.6, 2),
                          round(self.data_group['speed']['min'] * 3.6, 2),
                          self.dis_list[-1],
                          self.alt_list[-1],
                          self.date2str(),
                      )).add_to(world_map)
        for m in self.Markers:
            layer2.add_child(m)
        world_map.add_child(layer2)

        # 数据图片1
        layer1 = folium.FeatureGroup(name='rpm,rbm,km数据图',show=False)
        layer1.add_child(folium.Marker(
            location=[self.center_lat_max + 0.019, self.center_lon_max + 0.019],
            draggable=True,
            icon=folium.CustomIcon(self.jpg_file, icon_size=(1000, 400)),  # 指定图片大小
        ))
        world_map.add_child(layer1)

        # 数据图片2
        layer2 = folium.FeatureGroup(name='海拔图',show=False)
        layer2.add_child(folium.Marker(
            location=[self.center_lat_max + 0.019, self.center_lon_max + 0.019],
            draggable=True,
            icon=folium.CustomIcon(self.altitude_jpg_file),  # 指定图片大小
        ))
        world_map.add_child(layer2)

        folium.LayerControl().add_to(world_map)

        if self.save:
            world_map.save(self.html_file)
        else:
            world_map.show_in_browser()

    def date2str(self):
        delta = self.end_time - self.first_time
        total_seconds = delta.total_seconds()
        if total_seconds < 60:
            return f"{total_seconds} 秒"
        elif total_seconds < 3600:
            minutes = total_seconds / 60
            return f"{minutes:.2f} 分钟"
        elif total_seconds < 86400:
            hours = total_seconds / 3600
            return f"{hours:.2f} 小时"
        else:
            days = total_seconds / 86400
            return f"{days:.2f} 天"

    # semicircles
    def semicircles_to_degrees(self, semicircles):
        return semicircles / (2 ** 31) * 180


if __name__ == '__main__':
    # file_name = input('fit文件名')
    # if file_name == '':
    #     print("错误:fit文件名空")
    # start = input('步进开始,用于指定区域数据,默认全部')
    # if start == '' :
    #     start = 0

    # end = int(input('步进结束'))
    # strip = int(input('间隔,防止太多页面卡顿,默认10'))
    # if strip == 0:
    #     strip = 10
    # # save = input('是否存储,默认是')
    # # if save == '':
    # save = True
    #
    # heart_rate_filter = int(input('心率过滤.默认0'))

    # c = FitObj('pp', -1, -1, 5, True,170)
    # c = FitObj('baga', 4200, 5406, 5, True,0)
    c = FitObj('baga', -1, 5406, 10, True,160)
    c.parse()
    c.table()
    c.altitude()
    c.finish()
