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
    all_features = self.vgg(image)

    content_features = all_features[:constants.NUM_CONTENT_LAYERS]
    style_features = all_features[constants.NUM_CONTENT_LAYERS:]

    gram_style_features = [tensor_to_gram(feature_tensor) for feature_tensor in style_features]

    return (content_features, gram_style_features)





# import tensorflow as tf
# import PIL.Image
# import numpy as np

# MAX_DIM = 512

# CONTENT_LAYERS = ['block5_conv2'] 

# STYLE_LAYERS = ['block1_conv1',
#                 'block2_conv1',
#                 'block3_conv1', 
#                 'block4_conv1', 
#                 'block5_conv1']

# NUM_CONTENT_LAYERS = len(CONTENT_LAYERS)
# NUM_STYLE_LAYERS = len(STYLE_LAYERS)

# STYLE_WEIGHT = 1e-2
# CONTENT_WEIGHT = 1e4

# OPTIMIZER = tf.keras.optimizers.Adam(learning_rate=0.02, beta_1=0.99, epsilon=1e-1)

# def tensor_to_image(tensor):
#   print(tensor)
#   tensor = tensor*255
#   tensor = np.array(tensor, dtype=np.uint8)

#   if np.ndim(tensor)>3:
#     assert tensor.shape[0] == 1
#     tensor = tensor[0]

#   return PIL.Image.fromarray(tensor)

# def load_style_image(path):
#   '''loads a style image from the path and returns a raw 3 channel version'''
#   image = tf.io.read_file(path)
#   image = tf.image.decode_image(image, channels=3)
#   image = tf.image.convert_image_dtype(image, tf.float32)

#   return image

# def prepare_image(image):
#   '''takes in a raw image and resizes it so the biggest size is 512'''

#   shape = tf.cast(tf.shape(image)[:-1], tf.float32)
#   long_dim = max(shape)
#   scale = MAX_DIM / long_dim

#   new_shape = tf.cast(shape * scale, tf.int32)

#   image = tf.image.resize(image, new_shape)
#   image = image[tf.newaxis, :]

#   return image

# def vgg_layers(layer_names):
#   """ Creates a VGG model that returns a list of intermediate output values."""
  
#   # Load pretrained VGG19, trained on ImageNet data
#   vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')
#   vgg.trainable = False

#   outputs = [vgg.get_layer(name).output for name in layer_names]

#   model = tf.keras.Model([vgg.input], outputs)
#   return model

# def extract_style_features(style_image):
#   '''take in a Nx512 float style image and extracts it into some feature tensors to be optimized'''
#   style_extractor = vgg_layers(STYLE_LAYERS)
#   style_features = style_extractor(style_image*255.0)

#   style_features = [gram_matrix(style_feature) for style_feature in style_features]

#   style_dict = {style_name: value
#                 for style_name, value
#                 in zip(STYLE_LAYERS, style_features)}


#   return style_dict

# def extract_content_features(frame):
#   content_extractor = vgg_layers(CONTENT_LAYERS)
#   content_features = content_extractor(frame*255.0)
  
#   content_dict = {content_name: value
#                 for content_name, value
#                 in zip(CONTENT_LAYERS, [content_features])}

#   return content_dict

# def gram_matrix(input_tensor):
#   result = tf.linalg.einsum('bijc,bijd->bcd', input_tensor, input_tensor)
#   input_shape = tf.shape(input_tensor)
#   num_locations = tf.cast(input_shape[1] * input_shape[2], tf.float32)
#   return result/ ( num_locations)

# def clip_0_1(image):
#   return tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0)

# def style_content_loss(current_style_features, current_content_features, target_style_features, target_content_features):
#   style_loss = tf.add_n([tf.reduce_mean((current_style_features[name] - target_style_features[name])**2) 
#                           for name in target_style_features.keys()])
#   style_loss *= STYLE_WEIGHT / NUM_STYLE_LAYERS

#   content_loss = tf.add_n([tf.reduce_mean((current_content_features[name]- target_content_features[name])**2) 
#                             for name in target_content_features.keys()])
#   content_loss *= CONTENT_WEIGHT / NUM_CONTENT_LAYERS

#   loss = style_loss + content_loss
#   return loss

# def train_step(optimized_frame, target_style_features, target_content_features):
#   with tf.GradientTape() as tape:
#     current_content_features = extract_content_features(optimized_frame)
#     current_style_features = extract_style_features(optimized_frame)
  
#     loss = style_content_loss(
#       current_style_features,
#       current_content_features,
#       target_style_features, 
#       target_content_features)

#   grad = tape.gradient(loss, optimized_frame)
#   OPTIMIZER.apply_gradients([(grad, optimized_frame)])
#   optimized_frame.assign(clip_0_1(optimized_frame))