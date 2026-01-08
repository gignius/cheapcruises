"""AI-powered image generation for blog articles using OpenAI DALL-E"""
import os
import base64
import httpx
from typing import Optional
from loguru import logger
from openai import OpenAI


class BlogImageGenerator:
    """Generate featured images for blog articles using OpenAI DALL-E"""
    
    def __init__(self):
        from config_settings import settings
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in settings")
        self.client = OpenAI(api_key=api_key)
        self.image_dir = "static/images/blog"
        os.makedirs(self.image_dir, exist_ok=True)
    
    def generate_image_prompt(self, article_title: str, category: str) -> str:
        """Generate a DALL-E prompt based on article title and category"""
        base_prompt = f"A high-quality, professional photograph for a cruise blog article titled '{article_title}'. "
        
        if "dining" in category.lower() or "food" in article_title.lower() or "burger" in article_title.lower() or "pizza" in article_title.lower():
            base_prompt += "Show delicious cruise ship dining, gourmet food presentation, elegant restaurant setting. "
        elif "ship" in article_title.lower() or "review" in article_title.lower():
            base_prompt += "Show a modern luxury cruise ship at sea, impressive exterior view, beautiful ocean backdrop. "
        elif "destination" in category.lower() or "port" in article_title.lower():
            base_prompt += "Show a beautiful tropical port destination, cruise ship docked, scenic coastal view. "
        elif "tip" in article_title.lower() or "guide" in article_title.lower():
            base_prompt += "Show happy cruise passengers enjoying activities, vacation atmosphere, cruise ship deck. "
        else:
            base_prompt += "Show a beautiful cruise ship sailing on blue ocean waters, vacation atmosphere. "
        
        base_prompt += "Photorealistic, vibrant colors, professional travel photography style, 16:9 aspect ratio."
        
        return base_prompt
    
    def generate_image(self, article_title: str, category: str, slug: str) -> Optional[str]:
        """Generate an image for a blog article and save it locally"""
        try:
            prompt = self.generate_image_prompt(article_title, category)
            logger.info(f"Generating image for: {article_title}")
            logger.debug(f"Image prompt: {prompt}")
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                n=1,
                response_format="b64_json"
            )
            
            image_filename = f"{slug}.png"
            image_path = os.path.join(self.image_dir, image_filename)
            
            b64_image = response.data[0].b64_json
            image_data = base64.b64decode(b64_image)
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            relative_path = f"/static/images/blog/{image_filename}"
            logger.success(f"Generated and saved image: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Error generating image for '{article_title}': {e}")
            return None


if __name__ == "__main__":
    # Test the generator
    generator = BlogImageGenerator()
    image_url = generator.generate_image(
        "Best Carnival Cruise Tips from a Gold Status Member",
        "Tips & Guides",
        "best-carnival-cruise-tips-from-a-gold-status-member"
    )
    print(f"Generated image: {image_url}")
