import cv2
import numpy as np

def to_grey(frame):
  '''takes in a cv frame and converts it to greyscale'''

  return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

def calc_flow(prev_frame, cur_frame):
  '''takes in 2 grayscale frames and returns the '''

  return cv2.calcOpticalFlowFarneback(
    prev_frame, 
    cur_frame, 
    None,
    0.5, 
    3, 
    15, 
    3, 
    5, 
    1.2, 
    0)

def warp(image, flow):
  '''warp an image to its next frame based on predicted flow between frames'''

  h, w = flow.shape[:2]
  flow[:, :, 0] += np.arange(w)
  flow[:, :, 1] += np.arange(h)[:, np.newaxis]

  return cv2.remap(image, flow, None, cv2.INTER_LINEAR)

# From tutorial to draw flow nicely!
def draw_flow(mask, flow):
  '''takes in an optical flow and draws it using a mask'''

  # Computes the magnitude and angle of the 2D vectors
  magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    
  # Sets image hue according to the optical flow 
  # direction
  mask[..., 0] = angle * 180 / np.pi / 2
    
  # Sets image value according to the optical flow
  # magnitude (normalized)
  mask[..., 2] = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX)
    
  # Converts HSV to RGB (BGR) color representation
  rgb = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
    
  # Opens a new window and displays the output frame
  cv2.imshow("dense optical flow", rgb)
    