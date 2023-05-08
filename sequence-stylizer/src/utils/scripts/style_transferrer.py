import tensorflow as tf
import numpy as np
import PIL
import math
from feature_extractor import *
from optical_flow import *


def prepare_image(image):
  '''takes in a raw image and resizes it so the biggest size is 512'''

  shape = tf.cast(tf.shape(image)[:-1], tf.float32)
  long_dim = max(shape)
  scale = constants.MAX_IMAGE_SIZE / long_dim

  new_shape = tf.cast(shape * scale, tf.int32)

  image = tf.image.resize(image, new_shape)
  image = image[tf.newaxis, :]

  return image

def prepare_frame(frame):
  '''takes in a raw frame from openCV and prepares it for work'''

  return prepare_image(frame / 255.0)

def load_style_image(path):
  '''loads a style image from the path and prepares it for use'''

  image = tf.io.read_file(path)
  image = tf.image.decode_image(image, channels=3)
  image = tf.image.convert_image_dtype(image, tf.float32)

  return prepare_image(image)

def mean_square_loss(target_tensors, current_tensors):
  '''calculate the total loss between target tensors and current tensors using mse'''

  loss = 0
  for target_feature, current_feature in zip(target_tensors, current_tensors):
    mse = tf.reduce_mean((current_feature - target_feature) ** 2)
    loss += mse

  return loss

def clip(image):
  '''clip an image to be between 0 and 1 so there is no overflow'''

  return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)

def bilinear_interpolate(x, y, flow):
  '''given some x, y and a flow interpolate the flows value at that x,y'''

  # use bilinear interpolation to get the new flow
  # https://en.wikipedia.org/wiki/Bilinear_interpolation

  # bounds checking for corner cases
  if y < 0 and x < 0:
    return np.array(flow[0][0])
  elif y >= len(flow) - 1 and x < 0:
    return np.array(flow[-1][0])
  elif y < 0 and x >= len(flow[0]) - 1:
    return np.array(flow[0][-1])
  elif y >= len(flow) - 1 and x >= len(flow[0]) - 1:
    return np.array(flow[-1][-1])
  
  up_y    = math.floor(y)
  down_y  = up_y + 1
  left_x  = math.floor(x)
  right_x = left_x + 1

  # if x out of bounds just interpolate y
  if x < 0 or x >= len(flow[0]) - 1:
    if x < 0:
      left_x = 0
    else:
      left_x = len(flow[0]) - 1
    
    top_flow = np.array(flow[up_y][left_x])
    bottom_flow = np.array(flow[down_y][left_x])

    return top_flow + (y - up_y) * (bottom_flow - top_flow)
  
  # if y is out of bounds just interpolate x
  if y < 0 or y >= len(flow) - 1:
    if y < 0:
      up_y = 0
    else:
      up_y = len(flow) - 1

    left_flow = np.array(flow[up_y][left_x])
    right_flow = np.array(flow[up_y][right_x])

    return left_flow + (x - left_x) * (right_flow - left_flow)

  # now that all bounds are checked, actally do bilinear interpolation
  Q_11 = np.array(flow[up_y][left_x])
  Q_12 = np.array(flow[up_y][right_x])
  Q_21 = np.array(flow[down_y][left_x])
  Q_22 = np.array(flow[down_y][right_x])

  return Q_11 * (right_x - x) * (y - up_y) \
      + Q_21 * (x - left_x) * (y - up_y) \
      + Q_12 * (right_x - x) * (down_y - y) \
      + Q_22 * (x - left_x) * (down_y - y)


class StyleTransferrer:
  def __init__(self, style_image_path):
    self.extractor = FeatureExtractor()

    style_image = load_style_image(style_image_path)
    self.target_style_features = self.extractor.extract(style_image)[1]

    self.current_grey_frame = None
    self.target_content_features = None

    self.optimized_frame = None
    self.first_frame = True

    self.prev_stylized_frame = None
    self.prev_grey_frame = None
    self.prev_warped_to_cur = None

    self.forward_flow = None
    self.backward_flow = None
    self.occlusions = None

  def set_frame(self, frame, is_prepared=False):
    '''sets the style transferrer to optimize for a current frame image'''
    current_frame = None
    if not is_prepared:
      self.current_grey_frame = to_grey(np.array(tf.squeeze(prepare_image(frame)), dtype=np.uint8))
      current_frame = prepare_frame(frame)
    else:
      self.current_grey_frame = to_grey(np.array(tf.squeeze(frame), dtype=np.uint8))
      current_frame = frame
      
    self.target_content_features = self.extractor.extract(current_frame)[0]
    
    if self.first_frame:
      # if its the first frame, start the optimization from the conntent image
      self.optimized_frame = tf.Variable(current_frame)
    else:
      self.backward_flow = calc_flow(self.prev_grey_frame, self.current_grey_frame)
      self.forward_flow = calc_flow(self.current_grey_frame, self.prev_grey_frame)

      self.prev_warped_to_cur = warp(self.prev_stylized_frame, self.forward_flow)
      self.calculate_occlusions()
      
      # if its a later image, then start the optimization at the previous image warped to the new frame
      self.optimized_frame.assign(tf.expand_dims(self.prev_warped_to_cur, 0))
 
  def calculate_occlusions(self):
    '''calculate occlusions between the previous and current frames based on the method in the paper'''
    self.occlusions = np.zeros_like(self.current_grey_frame)

    u_gradient = np.gradient(self.backward_flow[:, :, 0])
    v_gradient = np.gradient(self.backward_flow[:, :, 1])

    for y in range(len(self.forward_flow)):
      for x in range(len(self.forward_flow[y])):
        warped_flow = bilinear_interpolate(x + self.backward_flow[y][x][0], y + self.backward_flow[y][x][1], self.forward_flow)

        # Forward-Backward Consistency
        left_side = np.linalg.norm(warped_flow + self.backward_flow[y][x]) ** 2
        right_side = 0.01 * ((np.linalg.norm(warped_flow) ** 2) + (np.linalg.norm(self.backward_flow[y][x]) ** 2)) + 0.5
        
        if (left_side > right_side):
          self.occlusions[y][x] = 1

        # Motion Boundary
        cur_u_gradient = np.array([u_gradient[0][y][x], u_gradient[1][y][x]])
        cur_v_gradient = np.array([v_gradient[0][y][x], v_gradient[1][y][x]])

        left_side = np.linalg.norm(cur_u_gradient) ** 2 + np.linalg.norm(cur_v_gradient) ** 2
        right_side = 0.01 * (np.linalg.norm(self.backward_flow[y][x]) ** 2) + 0.002

        if (left_side > right_side):
          self.occlusions[y][x] = 1

        

  def temporal_loss(self):
    '''calculate the temporal loss between two frames'''
    if self.first_frame:
      return 0
    
    x = tf.squeeze(self.optimized_frame)
    w = self.prev_warped_to_cur

    sum = 0
    for channel in range(3):
      sum += tf.reduce_mean(self.occlusions * np.square(x[:, :, channel] - w[:, :, channel]))

    return sum / 3

  @tf.function()
  def total_loss(self):
    '''calculate the total loss of the system in the current state'''
    content_features, style_features = self.extractor.extract(self.optimized_frame)

    style_loss = mean_square_loss(self.target_style_features, style_features)
    content_loss = mean_square_loss(self.target_content_features, content_features)
    temporal_loss = self.temporal_loss()

    print("Style: ", constants.STYLE_WEIGHT * style_loss)
    print("Content: ", constants.CONTENT_WEIGHT * content_loss)
    print("Temporal: ", constants.TEMPORAL_WEIGHT * temporal_loss)



    return constants.CONTENT_WEIGHT * content_loss \
        + constants.STYLE_WEIGHT * style_loss \
        + constants.TEMPORAL_WEIGHT * temporal_loss

  @tf.function()
  def __optimize_step(self):
    '''a single optimization step based on the loss'''

    with tf.GradientTape() as tape:
      current_loss = self.total_loss()

    grad = tape.gradient(current_loss, self.optimized_frame)
    constants.OPTIMIZER.apply_gradients([(grad, self.optimized_frame)])
    
    self.optimized_frame.assign(clip(self.optimized_frame))
  
  def optimize(self, as_image=True):
    '''optimize the image many times and then return the result as an array or image'''

    for j in range(15 if self.first_frame else constants.EPOCHS):
      for _ in range(constants.STEPS_PER_EPOCH):
        self.__optimize_step()
      print("Epoch: ", j)
    
    self.prev_grey_frame = self.current_grey_frame
    self.prev_stylized_frame = self.to_array()  

    self.first_frame = False

    return self.to_image() if as_image else self.prev_stylized_frame

  def to_array(self):
    '''returns the optimized image as a numpy array'''
    tensor = np.array(self.optimized_frame, dtype=np.float32)
    if np.ndim(tensor) > 3:
      assert tensor.shape[0] == 1
      tensor = tensor[0]
    
    return tensor


  def to_image(self):
    '''returns the optimized image as a PIL image'''

    tensor = np.array(self.optimized_frame * 255, dtype=np.uint8)
    if np.ndim(tensor) > 3:
      assert tensor.shape[0] == 1
      tensor = tensor[0]

    return PIL.Image.fromarray(tensor)
  