from boltiot import Sms, Bolt, Email
import my_Bolt
import json, time, requests

def led_control(pin,intensity):
    
    """ Intensity should be in between 0 to 255"""
    mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id) #  we are passing api_key and device_id to Bolt class as constructor arguments and it will return an instance
    #response = mybolt.digitalWrite('0', 'HIGH') # to turn on the LED without intensity control
    response = mybolt.analogWrite(f'{pin}', f'{intensity}') # In Bolt Python library analogWrite function is used as PWM for controlling the Intensity(brightness) of led
    print (response)

def buzzer_control(pin,noise_level):
    """ Intensity should be in between 0 to 255"""
    mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id)
    response = mybolt.analogWrite(f'{pin}', f'{noise_level}')
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
        ) # HTTP request to telegram server which includes BOT id, channel id and message to be deliverd
       
        print("This is the Telegram URL")
        print(url)
        print("This is the Telegram response")
        print(response.text)
        telegram_data = json.loads(response.text) # Converting telegram respose to the JSON to understand the response
        return telegram_data["ok"]
    except Exception as e:
        print("An error occurred in sending the alert message via Telegram")
        print(e)
        return False

mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id)
print(mybolt.isOnline()) # CHECKING THE STATUS OF THE DEVICE

# Temperatur_Alert_Function

def temp_alert(min_temp,max_temp):
    
    # setting the temperature limit
    minimum_limit = min_temp
    maximum_limit = max_temp
    #print(minimum_limit,maximum_limit)
    
    # loading required data
    mybolt = Bolt(my_Bolt.api_key, my_Bolt.device_id)
    
    # Required data taking from the file my_Bolt to send SMS
    sms = Sms(my_Bolt.SID,my_Bolt.AUTH_TOKEN, my_Bolt.TO_NUMBER,my_Bolt.FROM_NUMBER)
   
    # Required data taking from the file my_Bolt to send Email
    mailer = Email(my_Bolt.MAILGUN_API_KEY, my_Bolt.SANDBOX_URL, my_Bolt.SENDER_EMAIL, my_Bolt.RECIPIENT_EMAIL)
    break_cond = True
    
    while break_cond: 
        print("Reading sensor value")
        response = mybolt.analogRead('A0') 
        data = json.loads(response)  # response from the Bolt Cloud using the analogRead() function is in a JSON format
        
        if data["success"] != 1:
            print("Request not successfull")
            print("This is the response->", data)
            return -999
        print(data)
        print("Sensor value is: " + str((100*int(data['value']))/1024))
        
        try: 
            sensor_value = int(data['value']) 
            Live_Temp_C = (100*sensor_value)/1024 
            if Live_Temp_C> maximum_limit or Live_Temp_C < minimum_limit:
                
                # Turn On the LED
                led_control(1,200)
               
                # Turn on the buzzer
                buzzer_control(2,50)
                print("Making request to Twilio to send a SMS")
                response = sms.send_sms("The Current temperature sensor value is " +str(Live_Temp_C))
                print("Response received from Twilio is: " + str(response))
                print("Status of SMS at Twilio is :" + str(response.status))
                
                # To Send the mail
                print("Making request to Mailgun to send an email")
                response = mailer.send_email("Alert", "The Current temperature sensor value is " +str(Live_Temp_C))
                response_text = json.loads(response.text)
                print("Response received from Mailgun is: " + str(response_text['message']))
                
                # To send the telegram message
                print("Sensor value has exceeded threshold")
                message = "Alert! Sensor value has exceeded " + str(minimum_limit)+ \
                  ". The current value is " + str(Live_Temp_C)
                telegram_status = send_telegram_message(message)
                print("This is the Telegram status:", telegram_status)
                
                # Breaking Condition to stop the While loop
                break_cond = False
                
                # Time up to which buzzzer and LED will turn on
                time.sleep(5)
                led_control(1,0)
                buzzer_control(2,0)
        except Exception as e: 
            print ("Error occured: Below are the details")
            print (e)
        
        time.sleep(10) # It will control data geathering rate.

# Now, Just Try with this to get Output
temp_alert(20,25)
