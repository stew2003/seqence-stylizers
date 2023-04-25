import argparse
import cv2

from scripts.extract_features import *

ARGS = None # will contain the command line args

def parse_args():
  """ Perform command-line argument parsing. """

  parser = argparse.ArgumentParser(
    description="Stylize a video based on a style image!",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  
  parser.add_argument(
    '--video',
    required=True,
    help='''A path to the input video to run the stylization algorithm on'''
  )
  
  parser.add_argument(
    '--style',
    required=True,
    help='''A path to the style image you want the video to emulate'''
  )

  return parser.parse_args()

def main():
  print(ARGS.video)
  print(ARGS.style)

  style_image = load_style_image(ARGS.style)
  style_image = prepare_image(style_image)

  style_features = extract_style_features(style_image)

  # vidcap = cv2.VideoCapture(ARGS.video)
  # success, frame = vidcap.read()
  count = 0
  # while success:

  frame = load_style_image(ARGS.video)
  frame = prepare_image(frame)
  content_features = extract_content_features(frame)

  optimized_frame = tf.Variable(frame)
  
  epochs = 10
  steps_per_epoch = 100

  step = 0
  for n in range(epochs):
    for m in range(steps_per_epoch):
      step += 1
      train_step(optimized_frame, style_features, content_features)
      print(".", end='', flush=True)
    print("Train step: {}".format(step))

  tensor_to_image(optimized_frame).save("frame" + str(count) + ".jpg")

    # success, frame = vidcap.read()
    # print('Read a new frame: ', success)
    # break

if __name__ == "__main__":
  ARGS = parse_args()
  main()