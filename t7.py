import sys
import pandas as pd
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QDoubleSpinBox
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class BacktestApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOXL Fear/VIX Full Backtest Dashboard")

        layout = QVBoxLayout()

        # ========= 参数 =========
        self.fear_a = QDoubleSpinBox()
        self.fear_a.setValue(10)

        self.fear_b = QDoubleSpinBox()
        self.fear_b.setValue(15)

        self.vix_th = QDoubleSpinBox()
        self.vix_th.setValue(30)

        self.tp = QDoubleSpinBox()
        self.tp.setValue(2.0)
        self.tp.setSingleStep(0.1)

        layout.addWidget(QLabel("Fear < A"))
        layout.addWidget(self.fear_a)

        layout.addWidget(QLabel("OR (Fear < B AND VIX > C)"))
        layout.addWidget(self.fear_b)
        layout.addWidget(self.vix_th)

        layout.addWidget(QLabel("Take Profit Multiplier"))
        layout.addWidget(self.tp)

        # ========= 按钮 =========
        self.btn = QPushButton("Run Backtest")
        self.btn.clicked.connect(self.run_backtest)
        layout.addWidget(self.btn)

        # ========= 输出 =========
        self.output = QTextEdit()
        layout.addWidget(self.output)

        # ========= 图表 =========
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # =========================
    # 回测核心
    # =========================
    def run_backtest(self):

        fear_a = self.fear_a.value()
        fear_b = self.fear_b.value()
        vix_c = self.vix_th.value()
        tp_mult = self.tp.value()

        # ========= 数据 =========
        fear = pd.read_csv("fear.csv")
        fear["date"] = pd.to_datetime(fear["date"])
        fear["fear"] = fear["fear"].astype(float)

        vix = pd.read_csv("vix.csv")
        vix["date"] = pd.to_datetime(vix["Price"])
        vix["High"] = vix["High"].astype(float)

        vix_daily = vix.groupby("date")["High"].max().reset_index()

        signal = pd.merge(fear, vix_daily, on="date")

        signal_dates = set(
            signal[
                (signal["fear"] < fear_a) |
                ((signal["fear"] < fear_b) & (signal["High"] > vix_c))
            ]["date"]
        )

        # ========= SOXL =========
        soxl = pd.read_csv(
            "SOXL_2011-01-06__2026-04-18_stock_data.csv",
            skiprows=[1, 2]
        )

        soxl["Date"] = pd.to_datetime(soxl["Price"])
        soxl = soxl.sort_values("Date").reset_index(drop=True)

        # ========= 状态变量 =========
        cash = 100.0
        position = 0

        entry_price = 0
        entry_date = None
        low_price = None

        logs = []
        equity_curve = []
        position_series = []
        segments = []

        state_start = None
        state = 0  # 0 flat, 1 long

        # ========= 回测 =========
        for i in range(len(soxl)):

            row = soxl.iloc[i]
            date = row["Date"]

            position_series.append((date, position))

            # ========= 开仓 =========
            if position == 0:
                if date in signal_dates:
                    entry_price = row["Open"]
                    entry_date = date
                    low_price = row["Low"]
                    position = 1

                    if state == 0:
                        state_start = date
                        state = 1

            # ========= 持仓 =========
            if position == 1:

                low_price = min(low_price, row["Low"])

                if row["Close"] >= entry_price * tp_mult:

                    exit_price = row["Close"]
                    exit_date = date

                    ret = exit_price / entry_price
                    cash *= ret

                    hold_days = (exit_date - entry_date).days
                    max_dd = (entry_price - low_price) / entry_price

                    logs.append({
                        "entry": entry_date,
                        "entry_price": entry_price,
                        "exit": exit_date,
                        "exit_price": exit_price,
                        "hold": hold_days,
                        "ret": ret,
                        "cash": cash,
                        "mdd": max_dd
                    })

                    # segment close
                    segments.append({
                        "type": "LONG",
                        "start": state_start,
                        "end": exit_date
                    })

                    state = 0
                    state_start = exit_date

                    position = 0
                    entry_price = 0
                    entry_date = None
                    low_price = None

            equity_curve.append(cash)

        # ========= 统计 =========
        trade_count = len(logs)
        avg_hold = sum([t["hold"] for t in logs]) / trade_count if trade_count else 0
        avg_mdd = sum([t["mdd"] for t in logs]) / trade_count if trade_count else 0

        # ========= 输出 =========
        self.output.clear()

        self.output.append(f"TOTAL TRADES: {trade_count}")
        self.output.append(f"AVG HOLD DAYS: {avg_hold:.2f}")
        self.output.append(f"AVG MDD: {avg_mdd:.2%}")
        self.output.append(f"FINAL CAPITAL: {cash:.2f}")

        self.output.append("\n--- TRADES ---")

        for t in logs:
            self.output.append(
                f"{t['entry'].date()} | BUY {t['entry_price']:.2f} → "
                f"{t['exit'].date()} | SELL {t['exit_price']:.2f} | "
                f"HOLD {t['hold']}d | RET {t['ret']:.2f} | "
                f"MDD {t['mdd']:.2%} | CAP {t['cash']:.2f}"
            )

        self.output.append("\n--- POSITION SEGMENTS ---")

        for s in segments:
            self.output.append(
                f"{s['type']} | {s['start']} → {s['end']}"
            )

        # ========= 图表 =========
        self.figure.clear()

        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)

        ax1.plot(equity_curve)
        ax1.set_title("Equity Curve")

        pos_x = [d for d, p in position_series]
        pos_y = [p for d, p in position_series]

        ax2.step(pos_x, pos_y, where="post")
        ax2.set_title("Position (1=Long, 0=Flat)")
        ax2.set_ylim(-0.1, 1.1)

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BacktestApp()
    w.show()
    sys.exit(app.exec_())