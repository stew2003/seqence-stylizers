from PIL import Image
import sys
import time

def parse_file_path(file_path):
    last_slash_index = file_path.rfind('\\')
    if last_slash_index != -1:
        return file_path[:last_slash_index]
    return file_path

if __name__ == '__main__':
    image_path = sys.argv[1]
    with Image.open(image_path) as image:
        grayscale_image = image.convert('L')
        time.sleep(10)


        # send path to stdout
        grayscale_image.save(parse_file_path(image_path) + '//new_image.png')
        sys.stdout.write(parse_file_path(image_path) + '\\new_image.png')
