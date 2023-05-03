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
  success, cur_frame = vidcap.read()
  cur_frame_grey = to_grey(cur_frame)
  cur_initialization = prepare_frame(cur_frame)

  # For drawing flow
  # mask = np.zeros_like(cur_frame)
  # mask[..., 1] = 255

  count = 0
  while True:
    # set up this frame
    prepped_cur_frame = prepare_frame(cur_frame)
    st.set_content_features(prepped_cur_frame)
    st.initialize_optimization(cur_initialization)

    # optimize this frame
    for j in range(constants.EPOCHS):
      for i in range(constants.STEPS_PER_EPOCH):
        st.optimize()
      print(j)
    st.to_image().save(f"frames/frame{count:04d}.png")

    # find flow to optimize start of next frame
    success, next_frame = vidcap.read()
    if not success:
      break

    next_frame_grey = to_grey(next_frame)
    flow = calc_flow(cur_frame_grey, next_frame_grey)
    
    cur_initialization = prepare_frame(warp(cur_frame, flow))
    cur_frame_grey = next_frame_grey
    cur_frame = next_frame
    count += 1

    if (count == 3):
      break
    
    # Again for drawing!
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #   break
  
  # cv2.destroyAllWindows()
  vidcap.release()

  # ffmpeg -framerate 30 -pattern_type glob -i "frames/*.png" -c:v libx264 -crf 10 -pix_fmt yuv420p output/video.mp4 -y
  ffmpeg.input('frames/*.png', pattern_type='glob', framerate=30).filter('deflicker', mode='pm', size=10).filter('scale', size='hd1080', force_original_aspect_ratio='increase').output('output/movie.mp4', crf=20, preset='slower', movflags='faststart', pix_fmt='yuv420p').run()

if __name__ == "__main__":
  ARGS = parse_args()
  main()