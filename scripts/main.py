import argparse
import cv2
import ffmpeg

from style_transferrer import *
from optical_flow import *

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

  st = StyleTransferrer(ARGS.style)
  vidcap = cv2.VideoCapture(ARGS.video)
  count = 0
  prev = None

  while vidcap.isOpened():
    success, frame = vidcap.read()

    st.set_frame(frame)
    st.optimize().save(f"frames/frame{count:04d}.png")
    mask = np.zeros_like(frame)

    frame = to_grey(frame)

    if (count > 0):
      mask[..., 1] = 255

      flow = calc_flow(prev, frame)
      print("Full Prev Grey: ", prev)
      print("Full Cur Grey: ", frame)
      print("Full Flow: ", flow)
      draw_flow(mask, flow)

    count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
      break

    prev = frame

    # if (count == 3):
    #   break

  vidcap.release()
  cv2.destroyAllWindows()

  # ffmpeg -framerate 30 -pattern_type glob -i "frames/*.png" -c:v libx264 -crf 10 -pix_fmt yuv420p output/video.mp4 -y
  ffmpeg.input('frames/*.png', pattern_type='glob', framerate=30).filter('deflicker', mode='pm', size=10).filter('scale', size='hd1080', force_original_aspect_ratio='increase').output('output/movie.mp4', crf=20, preset='slower', movflags='faststart', pix_fmt='yuv420p').run()

if __name__ == "__main__":
  ARGS = parse_args()
  main()