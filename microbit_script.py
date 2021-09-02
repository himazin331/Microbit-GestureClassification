receivedString = ""
serial.set_baud_rate(BaudRate.BAUD_RATE9600)
basic.show_leds("""
    . # . . .
        . # # . .
        . # # # .
        . # # . .
        . # . . .
""")
while True:
    serial.write_line("" + str(input.acceleration(Dimension.Z))) # 加速度Z送信

    receivedString = serial.read_string() # 判定結果受信
    if receivedString == "maru":
        # 判定結果○
        basic.show_icon(IconNames.DIAMOND)
    elif receivedString == "sankaku":
        # 判定結果△
        basic.show_icon(IconNames.TRIANGLE)
    elif receivedString == "sikaku":
        # 判定結果□
        basic.show_icon(IconNames.SQUARE)
