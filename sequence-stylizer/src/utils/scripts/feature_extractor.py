import tensorflow as tf
import constants

def vgg_layers(layer_names):
  '''creates a VGG model that returns a list of intermediate output values.'''
  
  # Load pretrained VGG19, trained on ImageNet data
  vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')
  vgg.trainable = False

  outputs = [vgg.get_layer(name).output for name in layer_names]

  model = tf.keras.Model([vgg.input], outputs)
  return model

def tensor_to_gram(input_tensor):
  '''takes in an input tensor (output of VGG) and converts it to a gram matrix'''

  # vectorize each output into one matrix
  num_filters = int(input_tensor.shape[-1])
  vectorized_tensor = tf.reshape(input_tensor, [-1, num_filters])

  # calculate gram as X^T * X
  gram = tf.matmul(vectorized_tensor, vectorized_tensor, transpose_a=True)
  
  return gram

class FeatureExtractor:
  def __init__(self):
    '''creates a model that given an image, extracts the style and content features'''

    # create a subset of the vgg that outputs the correct layers
    self.vgg = vgg_layers(constants.CONTENT_LAYERS + constants.STYLE_LAYERS)

  def extract(self, image):
    '''returns a tuple of first the content features then the style features as gram matrices'''
    int_image = image * 255.0
    all_features = self.vgg(int_image)

    content_features = all_features[:constants.NUM_CONTENT_LAYERS]
    style_features = all_features[constants.NUM_CONTENT_LAYERS:]

    gram_style_features = [tensor_to_gram(feature_tensor) for feature_tensor in style_features]

    return (content_features, gram_style_features)