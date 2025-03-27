import RPi.GPIO as GPIO
import time
from smbus2 import SMBus
from RPLCD.i2c import CharLCD

# GPIO Pin Configuration
SERVO_ENTRY = 18  # Entry Barrier Servo
SERVO_EXIT = 22   # Exit Barrier Servo (Changed to avoid conflict)
TRIG_ENTRY = 23   # Entry Ultrasonic Trigger
ECHO_ENTRY = 24   # Entry Ultrasonic Echo
TRIG_EXIT = 25    # Exit Ultrasonic Trigger
ECHO_EXIT = 8     # Exit Ultrasonic Echo
SLOT_SENSORS = [(5, 6), (13, 19), (26, 21)]  # Ultrasonic sensors for slots

# LCD Configuration
bus = SMBus(1)
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2)

# Parking Configuration
TOTAL_SLOTS = 3 occupied_slots = 0
parking_times = {}  # Dictionary to store vehicle entry times

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_ENTRY, GPIO.OUT)
GPIO.setup(SERVO_EXIT, GPIO.OUT)
GPIO.setup(TRIG_ENTRY, GPIO.OUT)
GPIO.setup(ECHO_ENTRY, GPIO.IN)
GPIO.setup(TRIG_EXIT, GPIO.OUT)
GPIO.setup(ECHO_EXIT, GPIO.IN)

# Setup slot sensors
for trig, echo in SLOT_SENSORS:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)

# Initialize PWM for Servo
pwm_entry = GPIO.PWM(SERVO_ENTRY, 50)
pwm_exit = GPIO.PWM(SERVO_EXIT, 50)occupied_slots = 0
parking_times = {}  # Dictionary to store vehicle entry times

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_ENTRY, GPIO.OUT)
GPIO.setup(SERVO_EXIT, GPIO.OUT)
GPIO.setup(TRIG_ENTRY, GPIO.OUT)
GPIO.setup(ECHO_ENTRY, GPIO.IN)
GPIO.setup(TRIG_EXIT, GPIO.OUT)
GPIO.setup(ECHO_EXIT, GPIO.IN)

# Setup slot sensors
for trig, echo in SLOT_SENSORS:
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)

# Initialize PWM for Servo
pwm_entry = GPIO.PWM(SERVO_ENTRY, 50)
pwm_exit = GPIO.PWM(SERVO_EXIT, 50)  pwm_entry.start(2.5)  # Initial position (Closed)
pwm_exit.start(2.5)

print("[INFO] System initialized.")

# Function to control servo barrier
def set_angle(pwm, angle):
    duty = 2.5 + (angle / 18)
    print(f"[DEBUG] Setting servo angle to {angle}° (Duty Cycle: {duty})")
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)

# Function to measure distance
def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    start_time = time.time()
    stop_time = time.time() pwm_entry.start(2.5)  # Initial position (Closed)
pwm_exit.start(2.5)

print("[INFO] System initialized.")

# Function to control servo barrier
def set_angle(pwm, angle):
    duty = 2.5 + (angle / 18)
    print(f"[DEBUG] Setting servo angle to {angle}° (Duty Cycle: {duty})")
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)

# Function to measure distance
def get_distance(trig, echo):
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    start_time = time.time()
    stop_time = time.time() timeout = time.time() + 1  # 1-second timeout to avoid infinite loops

    while GPIO.input(echo) == 0:
        start_time = time.time()
        if time.time() > timeout:
            print(f"[WARNING] Timeout waiting for ECHO signal from TRIG {trig}")
            return 1000  # Return a high value if timeout occurs

    while GPIO.input(echo) == 1:
        stop_time = time.time()
        if time.time() > timeout:
            print(f"[WARNING] Timeout on ECHO high state for TRIG {trig}")
            return 1000

    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2  # Convert to cm
    print(f"[DEBUG] Distance from TRIG {trig}: {distance:.2f} cm")
    return round(distance, 2)

# Function to count occupied slots  def count_occupied_slots():
    count = 0
    for trig, echo in SLOT_SENSORS:
        distance = get_distance(trig, echo)
        if distance < 10:  # Vehicle detected in slot
            count += 1
    print(f"[INFO] Updated Occupied Slots: {count}/{TOTAL_SLOTS}")
    return count

try:
    while True:
        # Update slot count
        occupied_slots = count_occupied_slots()
        available_slots = TOTAL_SLOTS - occupied_slots

        print(f"[INFO] Available Slots: {available_slots}/{TOTAL_SLOTS}")

        # ENTRY LOGIC
        distance_entry = get_distance(TRIG_ENTRY, ECHO_ENTRY)
        if distance_entry < 10 and available_slots > 0:  # Vehicle detected and>  print("[INFO] Vehicle detected at ENTRY. Updating LCD & opening bar>
            lcd.clear()
            lcd.write_string(f"Slots: {available_slots}")
            time.sleep(2)

            # Open entry barrier
            set_angle(pwm_entry, 90)
            time.sleep(3)
            set_angle(pwm_entry, 0)
            print("[INFO] Entry barrier closed.")

            # Register entry time
            vehicle_id = time.time()  # Using timestamp as a unique ID
            parking_times[vehicle_id] = time.time()

        # EXIT LOGIC
        distance_exit = get_distance(TRIG_EXIT, ECHO_EXIT)
        if distance_exit < 10:
            print("[INFO] Vehicle detected at EXIT. Calculating parking fee.")
            # Find the first parked vehicle (for simplicity)  print("[INFO] Vehicle detected at EXIT. Calculating parking fee.")
            if parking_times:
                vehicle_id, entry_time = parking_times.popitem()
                parked_duration = time.time() - entry_time
                fee = round(parked_duration *10, 2)  # $2 per minute

                print(f"[INFO] Vehicle exited. Duration: {parked_duration:.2f} >
                lcd.clear()
                lcd.write_string(f"Fee: ${fee}")
                time.sleep(2)

                # Open exit barrier
                set_angle(pwm_exit, 90)
                time.sleep(3)
                set_angle(pwm_exit, 0)
                print("[INFO] Exit barrier closed.")

        time.sleep(1)

except KeyboardInterrupt:  except KeyboardInterrupt:
    print("[INFO] Exiting... Cleaning up GPIO.")
    pwm_entry.stop()
    pwm_exit.stop()
    GPIO.cleanup()
    lcd.clear()
