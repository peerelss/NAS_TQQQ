import sys
import pandas as pd
import numpy as np
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
        self.setWindowTitle("SOXL Full Quant Backtest Dashboard")

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
        self.figure = plt.figure(figsize=(10, 8))
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

        # ========= 状态 =========
        cash = 100.0
        position = 0

        entry_price = 0
        entry_date = None
        low_price = None

        logs = []
        equity_curve = []
        position_series = []
        segments = []

        state = 0
        state_start = None

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

                    # segment
                    segments.append({
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

        # ========= Sharpe =========
        equity = pd.Series(equity_curve)
        daily_ret = equity.pct_change().fillna(0)

        sharpe = 0
        if daily_ret.std() != 0:
            sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(252)

        # ========= Portfolio MDD =========
        peak = equity.cummax()
        dd = (equity - peak) / peak
        max_dd = dd.min()

        # ========= CAGR =========
        years = len(equity) / 252
        cagr = (cash / 100) ** (1 / years) - 1 if years > 0 else 0

        # ========= 输出 =========
        self.output.clear()

        self.output.append(f"TOTAL TRADES: {len(logs)}")
        self.output.append(f"CAGR: {cagr:.2%}")
        self.output.append(f"SHARPE: {sharpe:.2f}")
        self.output.append(f"MAX DRAWDOWN: {max_dd:.2%}")
        self.output.append(f"FINAL CAPITAL: {cash:.2f}")

        self.output.append("\n--- TRADES ---")

        for t in logs:
            self.output.append(
                f"{t['entry'].date()} | BUY {t['entry_price']:.2f} → "
                f"{t['exit'].date()} | SELL {t['exit_price']:.2f} | "
                f"HOLD {t['hold']}d | RET {t['ret']:.2f} | "
                f"MDD {t['mdd']:.2%}"
            )

        self.output.append("\n--- POSITION SEGMENTS ---")
        for s in segments:
            self.output.append(f"{s['start']} → {s['end']}")

        # ========= 图表 =========
        self.figure.clear()

        ax1 = self.figure.add_subplot(311)
        ax2 = self.figure.add_subplot(312)
        ax3 = self.figure.add_subplot(313)

        ax3.set_yscale("log")  # ⭐关键：对数坐标

        for t in logs:
            trade_df = soxl[
                (soxl["Date"] >= t["entry"]) &
                (soxl["Date"] <= t["exit"])
                ]

            ax3.plot(trade_df["Date"], trade_df["Close"], alpha=0.6)

            ax3.scatter(t["entry"], t["entry_price"], color="green")
            ax3.scatter(t["exit"], t["exit_price"], color="red")

        ax3.set_title("Trade Path (Log Scale)")

        # 1 equity
        ax1.plot(equity_curve)
        ax1.set_title("Equity Curve")

        # 2 position
        pos_x = [d for d, p in position_series]
        pos_y = [p for d, p in position_series]

        ax2.step(pos_x, pos_y, where="post")
        ax2.set_title("Position")

        # 3 trade path
        for t in logs:
            trade_df = soxl[
                (soxl["Date"] >= t["entry"]) &
                (soxl["Date"] <= t["exit"])
            ]

            ax3.plot(trade_df["Date"], trade_df["Close"], alpha=0.6)
            ax3.scatter(t["entry"], t["entry_price"], color="green")
            ax3.scatter(t["exit"], t["exit_price"], color="red")

        ax3.set_title("Trade Path")

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BacktestApp()
    w.show()
    sys.exit(app.exec_())