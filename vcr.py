import vlc
import time
import board
import digitalio
from adafruit_ht16k33.segments import Seg14x4
import RPi.GPIO as GPIO 
import pwmio
from adafruit_motor import motor
import shlex
import subprocess
import signal
import os
import sys

# set up the motor
PWM_PIN_A = board.D12  # Pick two PWM pins on their own channels
PWM_PIN_B = board.D26
PWM_FREQ = 25  # Custom PWM frequency in Hz; PWMOut min/max 1Hz/50kHz, default is 500Hz
DECAY_MODE = motor.SLOW_DECAY  # Set controller to Slow Decay (braking) mode
THROTTLE_HOLD = 1  # Hold the throttle (seconds)

drv8833 = digitalio.DigitalInOut(board.D16)
drv8833.direction = digitalio.Direction.OUTPUT
drv8833.value = True

# DC motor setup; Set pins to custom PWM frequency
pwm_a = pwmio.PWMOut(PWM_PIN_A, frequency=PWM_FREQ)
pwm_b = pwmio.PWMOut(PWM_PIN_B, frequency=PWM_FREQ)

# TODO figure out why moving motor1 line below anywhere farther down  causes:
# "AttributeError: 'function' object has no attribute 'DCMotor'"
motor1 = motor.DCMotor(pwm_a, pwm_b)
motor1.decay_mode = DECAY_MODE
motor1.throttle = 0

GPIO_REW = 5
GPIO_PLAY = 6
GPIO_FF = 13
GPIO_STOP = 19
GPIO_REC = 20
GPIO_PGM = 21
DEBOUNCE = 600  # switch debounce time in ms
MEDIA_NAME = "output.ogv"

PLAY_THROTTLE = 10
FAST_THROTTLE = 16

counter = 0
show_counter = False
in_program = False
current_program = 0
program_step = 0
in_record = False
cvlc = 0
endable = False

sh = 12
sm = 1
eh = 12
em = 1

rec_command = 'cvlc v4l2:///dev/video0:width=640:height=480 --sub-source="marq{marquee=REC}" :input-slave=alsa://hw:1,0 --x11-display \
:0 --sout="#transcode{vcodec=theo,vb=1024,fps=20,scale=1.0,acodec=vorb,ab=90,channels=1,samplerate=22050}:duplicate{dst=display,dst=standard{access=file,mux=ogg,dst=' + MEDIA_NAME + '}}"'

def btn_go(channel):

    global current_program
    global in_program
    global program_step
    global sh
    global sm
    global eh
    global em
    global show_counter
    global counter
    global in_record
    global cvlc
    global endable
    pid = 0
    pad_str = "  "

    if in_program:
        show_counter = False
        if channel == GPIO_PGM:
            in_program = False
            display.print("STOP")
            current_program = 0

            return

        if channel == GPIO_REW:
            current_program = current_program - 1
            if current_program < 1:
                current_program = 4
            display.print("PGM{}".format(current_program))
            return
        if channel == GPIO_PLAY:
            current_program = current_program + 1
            if current_program > 4:
                current_program = 1
            display.print("PGM{}".format(current_program))
            return

        if channel == GPIO_FF:
            if program_step == 0:
                display.print("SH01")
                program_step = 1
            elif program_step == 1:
                display.print("SM01")
                program_step = 2
            elif program_step == 2:
                display.print("EH01")
                program_step = 3
            elif program_step == 3:
                display.print("EM01")
                program_step = 4
            else:
                display.print("DONE")
                program_step = 0
            return

        if channel == GPIO_STOP:
            if program_step == 1:
                sh = sh - 1
                if sh == 0:
                    sh = 23
                pad_str = f'{sh:02}'
                print("pad sh dn: {}".format(pad_str))
                display.print("SH{}".format(pad_str))
            elif program_step == 2:
                sm = sm - 1
                if sm == 0:
                    sm = 59
                pad_str = f"{sm:02}"
                display.print("SM{}".format(pad_str))
            elif program_step == 3:
                eh = eh - 1
                if eh == 0:
                    eh = 23
                pad_str = f"{eh:02}"
                display.print("EH{}".format(pad_str))
            elif program_step == 4:
                em = em - 1
                if em == 0:
                    em = 59
                pad_str = f"{em:02}"
                display.print("EM{}".format(pad_str))
            return

        if channel == GPIO_REC:
            if program_step == 1:
                sh = sh + 1
                if sh == 24:
                    sh = 0
                pad_str = f'{sh:02}'
                print("pad sh up: {}".format(pad_str))
                display.print("SH{}".format(pad_str))
            elif program_step == 2:
                sm = sm + 1
                if sm == 60:
                    sm = 0
                pad_str = f"{sm:02}"   
                display.print("SM{}".format(pad_str))
            elif program_step == 3:
                eh = eh + 1
                if eh == 24:
                    eh = 0
                pad_str = f"{eh:02}"   
                display.print("EH{}".format(pad_str))
            elif program_step == 4:
                em = em + 1
                if em == 60:
                    em = 0
                pad_str = f"{em:02}"   
                display.print("EM{}".format(pad_str))
            return
    else:       

        if channel == GPIO_PLAY:
            if not in_record:
                if player.is_playing():
                    player.pause()
                    show_counter = False
                    display.print("PAUS")
                    osd("PAUSE")
                    motor("STOP")
                else:
                    player.play()
                    player.set_rate(1)
                    time.sleep(0.5)
                    duration = player.get_length()
                    rate = player.get_rate()
                    show_counter = False
                    osd("PLAY")
                    print("player length: {}; rate: {}".format(duration, rate))
                    display.print("PLAY")
                    motor("PLAY")
            return

        if channel == GPIO_REC:
            if in_record:
                pass
            else:
                in_record = True
                player.stop()
                display.print("REC ")
                motor("PLAY")
                cvlc = subprocess.Popen(rec_command, shell = True)

        if channel == GPIO_FF:
            if not in_record:
                if player.get_rate() == 1:
                    player.set_rate(1.5)
                    show_counter = False
                    display.print("FFWD")
                    osd("FFWD")
                    motor("FAST")
                else:
                    player.set_rate(1)
                    show_counter = False
                    display.print("PLAY")
                    osd("PLAY")
                    motor("PLAY")
            return

        if channel == GPIO_REW:
            if not in_record:
                if player.get_rate() == 1:
                    player.set_rate(-1.5)
                    show_counter = False
                    display.print("REW ")
                    osd("REW")
                    motor("FAST")
                else:
                    player.set_rate(1)
                    show_counter = False
                    display.print("PLAY")
                    osd("PLAY")
                    motor("PLAY")
            return

        if channel == GPIO_STOP:
            if in_record:
                print("stopping recording...")
                display.print("WAIT")
                #os.killpg(os.getpgid(cvlc.pid), signal.SIGTERM)
                motor("STOP")
                #media.release
                print("... killing VLC process...")
                subprocess.call(["pkill", "vlc"])
                print("... waiting...")
                time.sleep(1)
                print("... starting restart script...")
                endable = True
                subprocess.call("./restart.sh")
                print("... script started...")
                #time.sleep(1)
                #sys.exit("Exiting vcr - awaiting restart")
                #print("BYE!")
                #os.kill(os.getpid(), signal.SIGINT)
                #sys.exit(0)
                #print("See me?")
            else:
                player.stop()
            counter = 0
            show_counter = False
            display.print("STOP")
            motor("STOP")

            return

        if channel == GPIO_PGM:
            if (player.get_state() == vlc.State.Stopped or player.get_state() == vlc.State.NothingSpecial):
                in_program = True
                current_program = 1
                display.print("PGM1")
            else:
                in_program = False
                show_counter = True
                display.print(f"{counter:04}")
            return

def motor(mode):

    if mode == "PLAY":
        # get up to speed
        motor1.throttle = 0.20
        time.sleep(0.5)
        throttle = PLAY_THROTTLE/100
    elif mode == "FAST":
        # get up to speed
        motor1.throttle = 0.20
        time.sleep(0.5)
        throttle = FAST_THROTTLE/100
    else:  # stop
        throttle = 0
    print("motor throttling to: {}".format(throttle))
    motor1.throttle = throttle

def osd(txt):

    player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, 1) # enable
    player.video_set_marquee_int(6, 48)  # text size in pixels
    player.video_set_marquee_int(8, 420) # x pos
    player.video_set_marquee_int(9, 15) # y pos
    player.video_set_marquee_int(7, 5000) # timeout, ms
    player.video_set_marquee_string(1, txt) # text


# set up the LED display
i2c = board.I2C()
display = Seg14x4(i2c)
display.brightness = 0.75
display.print("VCR")

#motor1.throttle = 0  # Stop motor1

vlc_instance = vlc.Instance()
player = vlc_instance.media_player_new()
media = vlc_instance.media_new(MEDIA_NAME, "sub-source=marq")
player.set_media(media)
print("startup: vlc-inst:{0}; player:{1}; media:{2}".format(vlc_instance, player, media))
#player=vlc.MediaPlayer(MEDIA_NAME)

# Set button inputs
# rew
GPIO.setup(GPIO_REW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_REW, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE)

# play
GPIO.setup(GPIO_PLAY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_PLAY, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE+200)

# ff
GPIO.setup(GPIO_FF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_FF, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE)

# stop
GPIO.setup(GPIO_STOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_STOP, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE)

# rec
GPIO.setup(GPIO_REC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_REC, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE)

# pgm
GPIO.setup(GPIO_PGM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_PGM, GPIO.RISING, callback=btn_go, bouncetime=DEBOUNCE)

while True:

    time.sleep(1)
    counter = counter + 1
    # Uncomment below for player debugging:
    #print("player... state:{}; position:{}".format(player.get_state(), player.get_position()))
    if player.get_state() == vlc.State.Ended:
        player.stop()
        display.print("STOP")
        motor("STOP")
    if player.is_playing() and show_counter:
        display.print(f"{counter:04}")
    if endable:
        print("endable reached!")
        sys.exit(0)
