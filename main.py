from machine import Pin
from drivers import ServoSG90, ESCBrushed1625
from parts.communication import NRF24L01Communication
from parts.car import Move, Turn
from controller import Controller

turn_servo = ServoSG90(Pin(29), 90)
motor = ESCBrushed1625(Pin(26))

communication = NRF24L01Communication(1, Pin(10), Pin(11), Pin(12), Pin(8), Pin(9))
turn = Turn(turn_servo)
move = Move(motor)


car = Controller(
    communication,
    turn,
    move,
)

car.start()
