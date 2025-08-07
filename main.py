import io
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
BASE_URL = "https://u-nft.etnecosystem.org/api"
BACKGROUND_IMAGE_PATH = "assets/background.png"
FONT_PATH = "assets/font.ttf"
FONT_SIZE = 110
TEXT_COLOR = (0, 0, 0) # Black
SHADOW_COLOR = (255, 255, 255) # White
SHADOW_OFFSET = (5, 7)

app = FastAPI(
    title="ETN Username Metadata API",
    description="API for generating metadata and images for ETN Usernames.",
)

# --- Pydantic Models for Metadata Structure (TEP-64) ---
class Attribute(BaseModel):
    trait_type: str
    value: str | int

class NftMetadata(BaseModel):
    name: str
    description: str
    image: str
    attributes: list[Attribute]

# --- API Endpoints ---
@app.get(
    "/api/{username}.json",
    response_model=NftMetadata,
    summary="Get NFT JSON Metadata",
    tags=["Metadata"],
)
async def get_username_json(username: str):
    """
    Generates TEP-64 compliant JSON metadata for a given ETN Username.
    """
    display_name = f"@{username}"
    metadata = NftMetadata(
        name=display_name,
        description="An ETN Ecosystem Username.",
        image=f"{BASE_URL}/{username}.png",
        attributes=[],
    )
    return JSONResponse(content=metadata.dict())

@app.get(
    "/api/{username}.png",
    responses={200: {"content": {"image/png": {}}}},
    summary="Get NFT Image",
    tags=["Image"],
)
async def get_username_image(username: str):
    """
    Dynamically generates a PNG image for a given ETN Username.
    """
    try:
        # Load the base image and font
        background = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        # Create a drawing context
        draw = ImageDraw.Draw(background)
        img_width, img_height = background.size

        # Add @ symbol to username
        display_text = f"@{username}"

        # Calculate text size and position to center it
        text_bbox = draw.textbbox((0, 0), display_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Adjust position to be slightly higher than center
        position = ((img_width - text_width) / 2, (img_height - text_height) / 2.1)
        shadow_position = (position[0] + SHADOW_OFFSET[0], position[1] + SHADOW_OFFSET[1])

        # Draw the shadow
        draw.text(shadow_position, display_text, font=font, fill=SHADOW_COLOR)
        
        # Draw the text onto the image
        draw.text(position, display_text, font=font, fill=TEXT_COLOR)

        # Save the image to a bytes buffer
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        return Response(content=img_byte_arr.getvalue(), media_type="image/png")

    except FileNotFoundError:
        return JSONResponse(
            status_code=500,
            content={"error": "Server asset file not found (background or font)."},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
