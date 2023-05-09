import tensorflow as tf

MAX_IMAGE_SIZE = 512

CONTENT_LAYERS = ['block5_conv2'] 
NUM_CONTENT_LAYERS = len(CONTENT_LAYERS)

STYLE_LAYERS = ['block1_conv1',
                'block2_conv1',
                'block3_conv1', 
                'block4_conv1', 
                'block5_conv1']
NUM_STYLE_LAYERS = len(STYLE_LAYERS)

STYLE_WEIGHT = 10
CONTENT_WEIGHT = 100
TEMPORAL_WEIGHT = 400

OPTIMIZER = tf.keras.optimizers.Adam(learning_rate=0.02, beta_1=0.99, epsilon=1e-1)

EPOCHS = 2
STEPS_PER_EPOCH = 5
