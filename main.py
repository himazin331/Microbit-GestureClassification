import serial
import time
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# microbitから加速度Zを取得し保存
class readAcc():
    def __init__(self, options):
        self.hardware_port = options["hardware_port"]
        self.write_dir_path = options["write_dir_path"]
        self.filename_list = options["filename_list"]
        self.label_list = options["label_list"]
        self.timeout = options["timeout"]
        self.readnum = options["readnum"]

        self._running_symbol = ["/", "-", "\\", "|", "/", "-", "\\", "|"]

    def run(self):
        print("== Run Create Acceleration-Z File ==")
        try:
            with serial.Serial(self.hardware_port, timeout=self.timeout) as self.ser:
                time.sleep(3.0)
                for fn in self.filename_list:
                    self.mbAccZread_write(fn) # 取得&保存
        except serial.SerialException:
            print("Error: Could not open port '" + self.hardware_port + "'.\nCheck the port to which the Microbit is connected.")

        # グラフ描写
        self.create_graph()

    # 取得&保存
    def mbAccZread_write(self, filename):
        with open(os.path.join(self.write_dir_path, filename), 'w') as f:
            print("Saving file: " + filename)

            # 準備時間の確保
            for i in range(5, -1, -1):
                print("\r{} seconds to load...".format(i), end="")
                time.sleep(1)
            print("")

            for i in range(self.readnum):
                print("\rRead acceleration..." + self._running_symbol[i%8] + "     ", end="")
                time.sleep(0.02)

                # 取得
                line = self.ser.readline()
                line = line.strip().decode('utf-8')
                if line == "":
                    continue

                # 保存
                f.write(line+'\n')
        print("\rRead acceleration...Done!")

    # 加速度Zグラフ、箱ひげ図、移動平均グラフ描写
    def create_graph(self):
        csv_datas = self.accZ_read() # 加速度Z読み込み

        plt.rcParams["font.family"] = "Meiryo"
        colors = ["red", "green", "blue"]

        # 加速度Zグラフ描画
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        for i, data in enumerate(csv_datas):
            ax.plot(data, color=colors[i], label=self.label_list[i]+"の加速度Z")
        ax.set_ylabel("加速度センサーの値")
        ax.set_title("加速度Z")
        ax.legend()
        plt.show() 
        fig.savefig(os.path.join(self.write_dir_path, "accZ.png")) # 保存

        # 箱ひげ図描画
        points = []
        for i, data in enumerate(csv_datas):
            points.append(data[0].values.tolist())
        points = tuple(points)

        fig, ax = plt.subplots()
        bp = ax.boxplot(points)
        ax.set_xticklabels(self.label_list)

        plt.title("箱ひげ図")
        plt.xlabel("軌跡の形")
        plt.ylabel("加速度センサーの値")
        plt.grid()
        plt.show()
        fig.savefig(os.path.join(self.write_dir_path, "boxPlot.png")) # 保存

        # 移動平均グラフ描画
        v5 = np.ones(5) / 5.0  # 窓サイズ5
        v10 = np.ones(10) / 10.0  # 窓サイズ10
        v20 = np.ones(20) / 20.0  # 窓サイズ20
        for i, data in enumerate(points):
            accave5 = np.convolve(data, v5, mode='same')
            accave10 = np.convolve(data, v10, mode='same')
            accave20 = np.convolve(data, v20, mode='same')

            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1)
            ax.plot(data, color="blue", label="加速度")
            ax.plot(accave5, color="yellow", label="移動平均(窓サイズ5)")
            ax.plot(accave10, color="red", label="移動平均(窓サイズ10)")
            ax.plot(accave20, color="orange", label="移動平均(窓サイズ20)")
            ax.set_ylabel("value")
            ax.set_title(self.label_list[i]+"の加速度Z")
            ax.legend()
            fig.savefig(os.path.join(self.write_dir_path, self.label_list[i]+"convolve.png")) # 保存
            plt.show()

        # 要約統計量
        for i, data in enumerate(csv_datas):
            print(self.label_list[i]+"の要約統計量")
            print(data[0].describe())

    # 加速度Z読み込み
    def accZ_read(self):
        csv_datas = []
        for fn in self.filename_list:
            csv_datas.append(pd.read_csv(os.path.join(self.write_dir_path, fn), sep=" ", header=None).astype(np.int64))
        return csv_datas

# ジェスチャー分類
class gestureClassification():
    def __init__(self, options):
        self.hardware_port = options["hardware_port"]
        self.write_dir_path = options["write_dir_path"]
        self.filename_list = options["filename_list"]
        self.timeout = options["timeout"]
        self.readnum = options["readnum"]

        self._running_symbol = ["/", "-", "\\", "|", "/", "-", "\\", "|"]

        self.acc_data = []

    def run(self):
        print("== Run Gesture Classification ==")
        try:
            with serial.Serial(self.hardware_port, timeout=self.timeout) as self.ser:
                time.sleep(3.0)
                r = self.correlate() # 相関計算
            self.sendResult(r)
        except serial.SerialException:
            print("Error: Could not open port '" + self.hardware_port + "'.\nCheck the port to which the Microbit is connected.")

    # 相関計算
    def correlate(self):
        for i in range(self.readnum):
            print("\rRead acceleration..." + self._running_symbol[i%8] + "     ", end="")
            time.sleep(0.02)

            # 取得
            line = self.ser.readline()
            line = line.rstrip().decode('utf-8')
            try:
                line = int(line)
            except ValueError:
                continue

            self.acc_data.append(line) # 加速度Z

        # 比較用加速度Zデータの読み込み
        hikaku_acc = []
        hikaku_acc_std = []
        for i, data in enumerate(self.filename_list):
            hikaku_acc.append(pd.read_csv(os.path.join(self.write_dir_path, data), sep=" ", header=None))
            hikaku_acc[i] = hikaku_acc[i][0].values.tolist()
            hikaku_acc_std.append((hikaku_acc[i] - np.mean(hikaku_acc[i])) / (np.std(hikaku_acc[i]))) # 標準化

        # Microbit加速度Zデータの標準化
        acc_std = (self.acc_data - np.mean(self.acc_data)) / (np.std(self.acc_data))

        # 相関計算
        cor_maru = np.correlate(acc_std, hikaku_acc_std[0]) # X - ○
        cor_sankaku = np.correlate(acc_std, hikaku_acc_std[1]) # X - △
        cor_sikaku = np.correlate(acc_std, hikaku_acc_std[2]) # X - □

        print("")
        print("○の相関：", max(cor_maru))
        print("△の相関：", max(cor_sankaku))
        print("□の相関：", max(cor_sikaku))

        if max(cor_maru) > max(cor_sankaku) and max(cor_maru) > max(cor_sikaku):
            return "maru"
        elif max(cor_sankaku) > max(cor_maru) and max(cor_sankaku) > max(cor_sikaku):
            return "sankaku"
        elif  max(cor_sikaku) > max(cor_sankaku) and max(cor_sikaku) > max(cor_maru):
            return "sikaku"

    # 判定結果送信
    def sendResult(self, result):
        with serial.Serial(self.hardware_port, timeout=self.timeout) as self.ser:
            self.ser.write(bytes(result, encoding='utf-8'))

def main():
    options = {
        "hardware_port" : "COM5",                                       # Microbit接続ポート
        "write_dir_path" : "",                                          # 加速度データ保存先
        "filename_list" : ["maru.txt", "sankaku.txt", "sikaku.txt"],    # 加速度データファイル名
        "label_list" : ["○", "△", "□"],
        "timeout" : 0.5,    # タイムアウト時間
        "readnum" : 400     # 取得データ件数
    }

    # 推論時、下の２行をコメントアウト
    # 比較用加速度Z取得&保存
    """ 
    racc = readAcc(options)
    racc.run()
    """

    # ジェスチャー分類
    gc = gestureClassification(options)
    gc.run()

if __name__ == '__main__':
    main()