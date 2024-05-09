import fitparse
import matplotlib.pyplot as plt


def semicircles_to_degrees(semicircles):
    return semicircles / (2 ** 31) * 180


fitfile = fitparse.FitFile('huanglongdai.fit')
count = 0
x = []
y = []
isin = False
distance = 0
for record in fitfile.get_messages("record"):
    y.append(record.get('altitude').value)
    x.append((record.get('distance').value - distance)/1000)

plt.title('高度-距离')
plt.ylabel('高度')
plt.xlabel('距离')
plt.plot(x, y)
plt.show()
