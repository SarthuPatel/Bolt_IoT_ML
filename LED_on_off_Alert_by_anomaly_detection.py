from boltiot import Sms, Bolt
import my_Bolt
import json, time, requests

def led_control(pin,intensity):
    """ Intensity should be in between 0 to 255"""
    mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id) #  we are passing api_key and device_id to Bolt class as constructor arguments and it will return an instance
    #response = mybolt.digitalWrite('0', 'HIGH') # to turn on the LED without intensity control
    response = mybolt.analogWrite(f'{pin}', f'{intensity}') #  In Bolt Python library analogWrite function is used as PWM for controlling the Intensity(brightness) of led
    print (response)
    
 def send_telegram_message(message):
    """Sends message via Telegram"""
    url = "https://api.telegram.org/" + my_Bolt.telegram_bot_id + "/sendMessage"
    data = {
        "chat_id": my_Bolt.telegram_chat_id,
        "text": message
    }
    try:
        response = requests.request(
            "POST",
            url,
            params=data
        )
        print("This is the Telegram URL")
        print(url)
        print("This is the Telegram response")
        print(response.text)
        telegram_data = json.loads(response.text)
        return telegram_data["ok"]
    except Exception as e:
        print("An error occurred in sending the alert message via Telegram")
        print(e)
        return False
      
mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id)
print(mybolt.isOnline())  # CHECKING THE STATUS OF THE DEVICE

import my_Bolt, json, time, math, statistics
from boltiot import Sms, Bolt
# You can change frame size which indicate how many past data needs to be consider to detect anomaly
FRAME_SIZE = 10
MUL_FACTOR = 6
state = 'HIGH'

# Computing upper limt and lower limit to create a border value for the live_light detection
def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size] #deleting past datas
        
    Mn=statistics.mean(history_data)  # finding mean of last 'r' data
    Variance=0
    
    for data in history_data :
        Variance += math.pow((data-Mn),2) #only nominator
        
    Zn = factor * math.sqrt(Variance / frame_size) # z-factor
    High_bound = history_data[frame_size-1]+Zn # Upper bound
    Low_bound = history_data[frame_size-1]-Zn # Lower bound
    
    return [High_bound,Low_bound]

# Setting the device
mybolt = Bolt(my_Bolt.API_KEY, my_Bolt.DEVICE_ID)
sms = Sms(my_Bolt.SID, my_Bolt.AUTH_TOKEN, my_Bolt.TO_NUMBER, my_Bolt.FROM_NUMBER)
history_data=[]

while True:
    # Turning on the power supply to the LDR sensor
    response = mybolt.digitalWrite('3', f'{state}') # state = High
    # Reading analog signal
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    # Checking error is there or not
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        break
        #continue

    print ("This is the value "+data['value'])
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,FRAME_SIZE,MUL_FACTOR)
    
    # printing data when enough data for anomaly detection has not generated
    if not bound:
        required_data_count= FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
      # To turn OFF the LED when sudden light increase
        if sensor_value > bound[0] :
            led_control(1,0)
            print ("The light level increased suddenly. Sending an SMS.")
            response = sms.send_sms("Someone turned on the lights and Indicator LED OFF.")
            print("This is the response ",response)
            
        # Turn ON the LED when sudden fall in the light
        elif sensor_value < bound[1]:
            led_control(1,200)
            print ("The light level decreased suddenly. Sending an SMS.")
            response = sms.send_sms("Someone turned off the lights and Indicator LED ON")
            print("This is the response ",response)
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10)
