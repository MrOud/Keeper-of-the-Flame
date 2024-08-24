import machine
from machine import Pin, PWM
import time
import math
import random

#Takes ADC reading
def get_sensor_reading():
    reading = light_value.read_u16()
    return reading

#Samples the ADC 20 times and returns the average 
def calibrate_sensor():
    avg_open = 0
    avg_count = 0
    while avg_count < 20:
        avg_open += get_sensor_reading()
        avg_count += 1
        
    avg_open = avg_open / avg_count
    return avg_open

def lights_off():
    rain_led.off()
    fire_led.duty_u16(0)
    
def blink_rain(n_times, duration):
    count = 0
    while count < n_times:
        rain_led.on()
        time.sleep(duration / 2)
        rain_led.off()
        time.sleep(duration / 2)
        count += 1  
        
def blink_fire(n_times, duration):
    count = 0
    while count < n_times:
        fire_led.duty_u16(pwm_max)
        time.sleep(duration / 2)
        fire_led.duty_u16(0)
        time.sleep(duration / 2)
def clamp(n, min_val, max_val):
    return max(min_val, min(n, max_val))

def map(val, val_low, val_high, out_low, out_high):
    return (val - val_low)/(val_high - val_low)*(out_high - out_low) + out_low

#Give pico a moment to wake
time.sleep(1)
random.seed()

#Pin Values
light_value = machine.ADC(28)
fire_led = PWM(Pin(16))
rain_led = Pin(17, Pin.OUT)
fire_led.freq(1000)

#Setup variables
fire_life = 1000                  #Hitpoints for the fire
clock_timer = time.ticks_ms()     #Used to track the passage of time
pwm_max = 65025                   #Highest possible pwm signal
pwm_cur = 65025                   #Current strenght of pwm signal
is_raining = False                
seconds_running = 0               #How many seconds game has been running
game_length = 0                   #Total length of game
next_phase = random.randint(1,5)  #How long to weather shift

#Mode selection phase
lights_off()
#Get a reading
avg_start = calibrate_sensor()
#Signal user to select
rain_led.on()
time.sleep(3)
#take a second reading
rain_led.off()
avg_open = calibrate_sensor()
time.sleep(0.25)

if avg_open / avg_start < 0.8: #Sensor was covered
    rain_led.on()
    game_length = 180
else:                          #Sensor not covered
    fire_led.duty_u16(pwm_cur)
    game_length = 60

#Signal selected mode
time.sleep(2)
lights_off()

#print("Avg Start: ", avg_start, "Avg Open: ", avg_open)
#print("Ratio: ", avg_open / avg_start)

#Signal start of game
blink_rain(3, 0.25)
lights_off()
while seconds_running <= game_length and fire_life > 0:    
    sensor_read = get_sensor_reading()
    current_ratio = sensor_read / avg_open
        
    if time.ticks_diff(time.ticks_ms(), clock_timer) >= 1000:
        clock_timer = time.ticks_ms()
        seconds_running += 1
        print("Time:", seconds_running, "/", game_length, " Next:", next_phase, "Is Raining:", is_raining, "Hp:", fire_life, " ", pwm_cur )

    if seconds_running == next_phase:
        rain_led.toggle()
        is_raining = not is_raining
        next_phase += random.randint(1, 5)
    
    if current_ratio < 0.8 and not is_raining or current_ratio > 0.8 and is_raining:
            fire_life -= 10
    
    pwm_cur = math.floor(map(fire_life, 0, 1000, 0, 40000)) + random.randint(-4000, 4000)
    pwm_cur = clamp(pwm_cur, 0, pwm_max)
    fire_led.duty_u16(pwm_cur)
    
    time.sleep(0.1)

lights_off()

if fire_life > 0:
    fire_led.duty_u16(pwm_max)
else:
    rain_led.on()

time.sleep(5)
while True:
    if fire_life > 0:
        if game_length == 60:
            blink_fire(3, 1)
        else:
            blink_fire(3, 0.5)
    else:
        blink_rain(3, 1)
    
