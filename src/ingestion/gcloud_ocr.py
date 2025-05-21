import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
credentials_path = os.path.join(root_dir, 'gcloud-credentials.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

def ocr_image(image_path):
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    import io

    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    image_file.close()

    return response.full_text_annotation.text

