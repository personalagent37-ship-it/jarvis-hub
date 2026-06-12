from google import genai
from PIL import Image
import io
import os

def generate_image(prompt: str, output_path: str = "generated_image.png") -> str:
    """
    Generates an image using Gemini 3.1 Flash and saves it to the specified output path.
    Requires GEMINI_API_KEY environment variable.
    """
    try:
        # Initialize the client. It automatically picks up GEMINI_API_KEY from environment variables.
        client = genai.Client()

        # Generate the image
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[prompt],
        )

        # Extract and save the generated image
        for part in response.candidates[0].content.parts:
            # Check for the specific image/png or image/jpeg data in the response
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                image_bytes = part.inline_data.data
                image = Image.open(io.BytesIO(image_bytes))
                image.save(output_path)
                return f"Success! Image saved as '{output_path}'"
        
        return "Failed to find image data in the response."
    except Exception as e:
        return f"Error generating image: {str(e)}"
