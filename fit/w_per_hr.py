import fitparse


class WPerHr:
    def __init__(self, file_name) -> None:
        self.fitfile = fitparse.FitFile('data/'+file_name + '.fit')
        self.diff = []

    def parse(self):
        # incidents = folium.map.FeatureGroup()
        self.Markers = []
        self.hr = []
        self.w = []
        # 计数
        first = 0
        hr = 0
        w = 0

        # 迭代
        for record in self.fitfile.get_messages("record"):
            time = record.get('timestamp').value
            second = int(time.timestamp())
            if first == 0:
                first = second

            if second-first > 0 and (second-first) % 3600 == 0:
                self.diff.append(round(w/hr,2))
                hr = 0
                w = 0

            if record.get('power').value <= 0:
                continue
            hr += record.get('power').value
            self.hr.append(record.get('power').value)
            self.w .append(record.get('heart_rate').value)
            w += record.get('heart_rate').value
        self.diff.append(round(w/hr,2))

    def count(self):
        for i in range(1,len(self.diff)):
            print('{} hour:{}%'.format(i,round(100-self.diff[i-1]/self.diff[i]*100,2)))
        half = int(len(self.hr)/2)
        head_half = sum(self.w[:half])/sum(self.hr[:half])
        front_half = sum(self.w[half:])/sum(self.hr[half:])
        print('前后时间:{}%'.format(round(100-head_half/front_half*100,2)))


if __name__ == '__main__':
    obj = WPerHr('lsd0525')
    obj.parse()
    obj.count()

    obj = WPerHr('lsd0526')
    obj.parse()
    obj.count()