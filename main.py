import base64
import io
import logging
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse
from PIL import Image

app = FastAPI()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def validate_base64_image(image_base64: str) -> Image.Image:
    try:
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))

        image.verify()
        image = Image.open(io.BytesIO(image_data))
        return image
    except (base64.binascii.Error, IOError) as e:
        raise HTTPException(status_code=400, detail="Invalid Base64 image or image format")


@app.post("/transform-image")
async def transform_image(
    image_base64: str = Form(...),
    grayscale: bool = Form(False),
    rotate: int = Form(0),
    resize_width: int = Form(None),
    resize_height: int = Form(None)
):
    try:
        image = validate_base64_image(image_base64)

        if grayscale:
            image = image.convert("L")

        if rotate:
            image = image.rotate(rotate, expand=True)

        if resize_width and resize_height:
            image = image.resize((resize_width, resize_height))

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        buffered.seek(0)

        encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        logging.info(f"Image transformed with grayscale={grayscale}, rotate={rotate}, resize=({resize_width}, {resize_height})")

        return JSONResponse(content={"image_base64": encoded_image})

    except Exception as e:
        logging.error(f"Error in image transformation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
