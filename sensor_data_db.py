import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import threading
import mysql.connector
from datetime import datetime

# MariaDB 초기 연결 설정 (데이터베이스 이름 제외)
initial_db_config = {
    'host': 'localhost',
    'user': 'jung',
    'password': '1234'
}

# 데이터베이스 포함된 연결 설정
db_config = {
    'host': 'localhost',
    'user': 'jung',
    'password': '1234',
    'database': 'sensor_data'
}

# 데이터베이스 및 테이블 생성
def setup_database():
    try:
        # 초기 연결 (데이터베이스 선택 없이)
        conn = mysql.connector.connect(**initial_db_config)
        cursor = conn.cursor()
        
        # 데이터베이스 생성
        cursor.execute("CREATE DATABASE IF NOT EXISTS sensor_data")
        cursor.execute("USE sensor_data")
        
        # 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dht11_readings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                temperature FLOAT,
                humidity FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database setup completed successfully")
    except Exception as e:
        print(f"Database setup error: {e}")
        exit(1)

# 데이터베이스에 데이터 저장
def save_to_database(temperature, humidity):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        query = """
            INSERT INTO dht11_readings (temperature, humidity)
            VALUES (%s, %s)
        """
        cursor.execute(query, (temperature, humidity))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database insert error: {e}")

# 시리얼 포트 설정
ser = serial.Serial('/dev/ttyACM0', 115200)

# 데이터를 읽어서 그래프에 추가하는 함수
def read_from_stm32():
    while True:
        try:
            if ser.in_waiting:  # 데이터가 있을 때만 읽기
                line = ser.readline().decode('utf-8').strip()
                if line and ',' in line:  # 유효한 데이터인지 확인
                    temperature, humidity = map(int, line.split(','))
                    # 데이터 범위 검증 추가
                    if 0 <= temperature <= 50 and 0 <= humidity <= 100:
                        x.append(x[-1] + 1)
                        y_temp.append(temperature)
                        y_humi.append(humidity)
                        
                        # 데이터 개수 제한 (메모리 관리)
                        if len(x) > 100:  # 최근 100개 데이터만 표시
                            x.pop(0)
                            y_temp.pop(0)
                            y_humi.pop(0)
                            
                        # 온도 그래프 업데이트
                        temp_line.set_xdata(x)
                        temp_line.set_ydata(y_temp)
                        ax1.relim()
                        ax1.autoscale_view()
                        
                        # 습도 그래프 업데이트
                        humi_line.set_xdata(x)
                        humi_line.set_ydata(y_humi)
                        ax2.relim()
                        ax2.autoscale_view()
                        
                        canvas.draw()
                        
                        # DB에 저장
                        save_to_database(temperature, humidity)
        except Exception as e:
            print(f"Error: {e}")
            continue


# GUI 설정
root = tk.Tk()
root.title("STM32 Temperature and Humidity")

# 그래프 설정 - 2개의 서브플롯 생성
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
fig.tight_layout(pad=3.0)  # 서브플롯 간격 조정

# 초기 데이터
x, y_temp, y_humi = [0], [0], [0]

# 온도 그래프 설정
temp_line, = ax1.plot(x, y_temp, label='Temperature', color='red', linewidth=2)
ax1.set_title('Temperature Over Time')
ax1.set_xlabel('Time')
ax1.set_ylabel('Temperature (°C)')
ax1.grid(True)
ax1.legend(loc='upper left')

# 습도 그래프 설정
humi_line, = ax2.plot(x, y_humi, label='Humidity', color='blue', linewidth=2)
ax2.set_title('Humidity Over Time')
ax2.set_xlabel('Time')
ax2.set_ylabel('Humidity (%)')
ax2.grid(True)
ax2.legend(loc='upper left')

# 캔버스 설정
canvas = FigureCanvasTkAgg(fig, master=root)
widget = canvas.get_tk_widget()
widget.pack(fill=tk.BOTH, expand=True)

# 데이터 읽기 스레드 시작
thread = threading.Thread(target=read_from_stm32)
thread.daemon = True
thread.start()

root.mainloop()
