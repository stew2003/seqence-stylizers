import tensorflow as tf
import numpy as np
import PIL
from feature_extractor import *


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
  return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)


class StyleTransferrer:
  def __init__(self, style_image_path):
    self.extractor = FeatureExtractor()

    style_image = load_style_image(style_image_path)
    self.target_style_features = self.extractor.extract(style_image)[1]

    self.target_content_features = None
    self.content_image = None
    self.initialized = False

  def set_content_features(self, content_image):
    '''sets the style transferrer to optimize for a content image'''
    self.target_content_features = self.extractor.extract(content_image)[0]
  
  def initialize_optimization(self, starting_state):
    if not self.initialized:
      self.content_image = tf.Variable(starting_state)
      self.initialized = True
    else:
      self.content_image.assign(starting_state)

  def total_loss(self):
    content_features, style_features = self.extractor.extract(self.content_image)

    style_loss = mean_square_loss(self.target_style_features, style_features)
    content_loss = mean_square_loss(self.target_content_features, content_features)

    return constants.CONTENT_WEIGHT / constants.NUM_CONTENT_LAYERS * content_loss + constants.STYLE_WEIGHT / constants.NUM_STYLE_LAYERS * style_loss

  @tf.function
  def optimize(self):
    with tf.GradientTape() as tape:
      current_loss = self.total_loss()

    grad = tape.gradient(current_loss, self.content_image)
    constants.OPTIMIZER.apply_gradients([(grad, self.content_image)])
    
    self.content_image.assign(clip(self.content_image))

  def to_image(self):
    tensor = np.array(self.content_image * 255, dtype=np.uint8)
    if np.ndim(tensor) > 3:
      assert tensor.shape[0] == 1
      tensor = tensor[0]

    return PIL.Image.fromarray(tensor)