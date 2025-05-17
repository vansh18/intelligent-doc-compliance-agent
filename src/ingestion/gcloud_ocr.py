import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-credentials.json"

def ocr_image(image_path):
    from google.cloud import vision
    from google.cloud.vision_v1 import types
    import io

    client = vision.ImageAnnotatorClient()
    print("Processing...")

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    image_file.close()

    return response.full_text_annotation.text

