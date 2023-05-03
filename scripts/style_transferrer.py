import tensorflow as tf
import numpy as np
import PIL
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
    mse = tf.reduce_mean(tf.square(current_feature - target_feature))
    loss += mse

  return loss

def clip(image):
  '''clip an image to be between 0 and 1 so there is no overflow'''

  return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)


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

  def set_frame(self, current_frame):
    '''sets the style transferrer to optimize for a current frame image'''

    current_frame = prepare_frame(current_frame)

    self.current_grey_frame = to_grey(np.array(tf.squeeze(current_frame)))
    self.target_content_features = self.extractor.extract(current_frame)[0]
    
    if self.first_frame:
      # if its the first frame, start the optimization from the conntent image
      self.optimized_frame = tf.Variable(current_frame)
    else:
      self.forward_flow = calc_flow(prev_frame=self.prev_grey_frame, cur_frame=self.current_grey_frame)
      self.backward_flow = calc_flow(prev_frame=self.current_grey_frame, cur_frame=self.prev_grey_frame)
      self.prev_warped_to_cur = warp(self.prev_stylized_frame, self.forward_flow)
      self.calculate_occlusions()
      
      # if its a later image, then start the optimization at the previous image warped to the new frame
      self.optimized_frame.assign(tf.expand_dims(self.prev_warped_to_cur, 0))

  def calculate_occlusions(self):
    '''calculate occlusions between the previous and current frames based on the method in the paper'''
    warped_flow = [[[0, 0] for _ in range(len(self.forward_flow[i]))] for i in range(len(self.forward_flow))]
    
    for y in range(len(self.forward_flow)):
      for x in range(len(self.forward_flow[y])):
        new_y = y + int(self.backward_flow[y][x][0])
        if new_y >= len(self.forward_flow):
          new_y = len(self.forward_flow) - 1

        new_x = x + int(self.backward_flow[y][x][1])
        if new_x >= len(self.forward_flow[y]):
          new_x = len(self.forward_flow[y]) - 1

        warped_flow[y][x] = self.forward_flow[new_y][new_x]


    print(self.forward_flow[0 + int(self.backward_flow[0][0][0])][0 + int(self.forward_flow[0][0][0])])

    print(self.backward_flow[0][0])

  def temporal_loss(self):
    if self.first_frame:
      return 0
    
    x = tf.squeeze(self.optimized_frame)
    w = self.prev_warped_to_cur



  def total_loss(self):
    '''calculate the total loss of the system in the current state'''
    content_features, style_features = self.extractor.extract(self.optimized_frame)

    style_loss = mean_square_loss(self.target_style_features, style_features)
    content_loss = mean_square_loss(self.target_content_features, content_features)

    return constants.CONTENT_WEIGHT * content_loss + constants.STYLE_WEIGHT * style_loss

  @tf.function
  def __optimize_step(self):
    '''a single optimization step based on the loss'''

    with tf.GradientTape() as tape:
      current_loss = self.total_loss()

    grad = tape.gradient(current_loss, self.optimized_frame)
    constants.OPTIMIZER.apply_gradients([(grad, self.optimized_frame)])
    
    self.optimized_frame.assign(clip(self.optimized_frame))
  
  def optimize(self, as_image=True):
    '''optimize the image many times and then return the result as an array or image'''

    for j in range(constants.EPOCHS):
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
  