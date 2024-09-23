Uses [SparkFun Edge Development Board](https://www.sparkfun.com/products/15170)
with [Serial Basic Breakout](https://www.sparkfun.com/products/15096) and
[HM01B0 camera](https://www.sparkfun.com/products/15570) to take pictures.
The image is transferred over the UART, so it is pretty slow.

## How to use

### Flash the board
Upload the sketch file (board/board.ino) to the SparkFun Edge using instructions
from [here](https://learn.sparkfun.com/tutorials/programming-the-sparkfun-edge-with-arduino).
You can skip installing TensorFlowLite library and use the sketch file from this
repository instead of the examples.

### Run python code to take pictures
- Install requirements by running `pip install -r requirements.txt`
- Find which port the board is connected to and run `python3 use-camera.py -p {PORT}`.
By default the images are saved to folder named 'output' using timestamps.