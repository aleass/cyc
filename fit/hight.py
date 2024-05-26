import fitparse
import matplotlib.pyplot as plt

def semicircles_to_degrees(semicircles):
    return semicircles / (2 ** 31) * 180

def readFit(file):
    fitfile = fitparse.FitFile(f'data/{file}.fit')
    count = 0
    x = []
    y = []
    isin = False
    distance = 0
    for record in fitfile.get_messages("record"):
        y.append(record.get('altitude').value)
        x.append((record.get('distance').value - distance)/1000)
    max_y = max(y)
    max_x = x[y.index(max_y)]
    plt.text(max_x, max_y, f'{round(max_y,2)}')
    plt.text(x[-1], y[-1], f'dis:{round(x[-1],2)}  \nhigh:{round(y[-1],2)}')
    plt.text(x[0], y[0], f'dis:{round(x[0],2)}  \nhigh:{round(y[0],2)}')
    plt.ylabel('high')
    plt.xlabel('dis')
    plt.plot(x, y)
    plt.show()


if __name__ == '__main__':
    readFit('pp')