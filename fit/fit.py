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

    def __init__(self, name, start, end, strip, save) -> None:
        self.set_config(name, start, end, strip, save)

    def set_config(self, name, start, end, strip, save):
        self.name = "data/"+name
        self.fitfile = fitparse.FitFile(self.name + '.fit')
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
        self.jpg_file = self.name + '.jpg'
        self.html_file = self.name + '.html'

    def parse(self):
        # incidents = folium.map.FeatureGroup()
        self.Markers = []
        # 计数
        count = 0
        first = 0
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
                self.strip = 10
            if self.strip != 0 and count % self.strip != 0:
                continue

            # 记录折线图数据
            rpm, hpm, speed = 0, 0, 0

            time = record.get('timestamp').value
            if first == 0:
                first = int(time.timestamp())
            self.x.append(int(time.timestamp()) - first)


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

                self.Markers.append(
                    folium.Marker([lat, long], popup='心率:{}\n踏频:{}\n速度:{} km/h'.format(hpm, rpm, round(speed,2))))

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
        # plt.gcf().set_size_inches(15, 5) #长宽
        # 添加标题
        plt.title(self.name)
        # 展示图形
        plt.savefig(self.jpg_file)

    def finish(self):
        coordinate = [(self.center_lat_min + self.center_lat_max) / 2,
                      (self.center_lon_min + self.center_lon_max) / 2]
        world_map = folium.Map(zoom_start=16, location=coordinate)
        folium.Marker(coordinate,
                      icon=folium.Icon(color='red'),
                      popup='平均心率:{}\r'
                            '最大心率:{}\r'
                            '最小心率:{}\r'
                            '平均踏频:{}\r'
                            '最大踏频:{}\r'
                            '最小踏频:{}\r'
                            '平均速度:{}km/h\r'
                            '最大速度:{}km/h\r'
                            '最小速度:{}km/h'.
                      format(
                          round(self.data_group['heart_rate']['sum'] / self.data_group['heart_rate']['count'], 2),
                          self.data_group['heart_rate']['max'], self.data_group['heart_rate']['min'],

                          int(self.data_group['cadence']['sum'] / self.data_group['cadence']['count']),
                          self.data_group['cadence']['max'], self.data_group['cadence']['min'],

                          round(self.data_group['speed']['sum'] / self.data_group['speed']['count'] * 3.6, 2),
                          self.data_group['speed']['max'] * 3.6, self.data_group['speed']['min'] * 3.6,
                      )).add_to(world_map)

        layer2 = folium.FeatureGroup(name='描点数据')
        for m in self.Markers:
            layer2.add_child(m)
        world_map.add_child(layer2)

        # 数据图片1
        layer1 = folium.FeatureGroup(name='rpm,rbm,km数据图')
        layer1.add_child(folium.Marker(
            location=[self.center_lat_max + 0.019, self.center_lon_max + 0.019],
            icon=folium.CustomIcon(self.jpg_file, icon_size=(1000, 400)),  # 指定图片大小
            popup='Marker',
        ))
        world_map.add_child(layer1)

        folium.LayerControl().add_to(world_map)

        if self.save:
            world_map.save(self.html_file)
        else:
            world_map.show_in_browser()

    # semicircles
    def semicircles_to_degrees(self, semicircles):
        return semicircles / (2 ** 31) * 180


if __name__ == '__main__':
    c = FitObj('huanglongdai', 0, 0, 0, save=True)
    c.parse()
    c.table()
    c.finish()
