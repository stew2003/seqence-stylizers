from PIL import Image
import sys

if __name__ == '__main__':
    image_path = sys.argv[1]
    with Image.open(image_path) as image:
        grayscale_image = image.convert('L')
        grayscale_image.save(image_path)
