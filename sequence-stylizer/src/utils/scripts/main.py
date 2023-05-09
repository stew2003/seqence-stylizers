import argparse
import cv2
import ffmpeg
import time
import PIL
import os
import shutil


from style_transferrer import *
from optical_flow import *

from scipy.ndimage.filters import gaussian_filter

ARGS = None # will contain the command line args

def parse_args():
  """ Perform command-line argument parsing. """

  parser = argparse.ArgumentParser(
    description="Stylize a video based on a style image!",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  
  parser.add_argument(
    '--video',
    required=False,
    help='''A path to the input video to run the stylization algorithm on'''
  )

  parser.add_argument(
    '--image',
    required=False,
    help='''A path to the input video to run the stylization algorithm on'''
  )
  
  parser.add_argument(
    '--style',
    required=True,
    help='''A path to the style image you want the video to emulate'''
  )

  return parser.parse_args()

def main():
  print(ARGS.style)

  dir_path = "public/frames"
  output_path = "public/output"
  if os.path.exists(dir_path):
    shutil.rmtree(dir_path)
  if os.path.exists(output_path):
    shutil.rmtree(output_path)
  
  os.mkdir(dir_path)
  os.mkdir(output_path)

  st = StyleTransferrer(ARGS.style)

  if (ARGS.video != None):
    print(ARGS.video)

    vidcap = cv2.VideoCapture(ARGS.video)
    count = 0

    while vidcap.isOpened():
      success, frame = vidcap.read()

      if not success:
        break

      st.set_frame(frame)
      st.optimize().save(f"public/frames/frame{count:04d}.png")
      print(f"Frame {count:d} completed")
      count += 1

    vidcap.release()
    cv2.destroyAllWindows()

    # ffmpeg -framerate 30 -pattern_type glob -i "frames/*.png" -c:v libx264 -crf 10 -pix_fmt yuv420p output/video.mp4 -y
    ffmpeg.input('public/frames/*.png', pattern_type='glob', framerate=30).filter('deflicker', mode='pm', size=10).filter('scale', size='hd1080', force_original_aspect_ratio='increase').output('public/output/movie.mp4', crf=20, preset='slower', movflags='faststart', pix_fmt='yuv420p').run()
  else:
    print(ARGS.image)

    image = load_style_image(ARGS.image)
    st.set_frame(image, True)
    st.optimize().save(f"public/output/image.png")

if __name__ == "__main__":
  ARGS = parse_args()
  main()
