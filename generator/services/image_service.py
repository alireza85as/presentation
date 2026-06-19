from googleapiclient.discovery import build
from django.conf import settings
import requests
import os
from pathlib import Path
import imagehash
from PIL import Image as PILImage


class ImageService:
    """Service class for searching and downloading images using Google Custom Search API"""
    
    def __init__(self):
        """Initialize Google Custom Search API"""
        if not settings.GOOGLE_SEARCH_API_KEY or not settings.GOOGLE_SEARCH_ENGINE_ID:
            raise ValueError("Google Search API credentials are not configured")
        
        self.api_key = settings.GOOGLE_SEARCH_API_KEY
        self.search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        self.service = build("customsearch", "v1", developerKey=self.api_key)
    
    def search_images(self, query: str, num_images: int = 5, start_index: int = 1) -> list:
        """
        Search for images related to the query
        
        Args:
            query: Search query
            num_images: Number of images to retrieve (max 10 per request)
            start_index: The index of the first result to return
            
        Returns:
            list: List of image URLs
        """
        try:
            # Perform the search
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                searchType='image',
                num=min(num_images, 10),  # API limit is 10 per request
                start=start_index,
                imgSize='LARGE',  # Request large images (must be uppercase)
                safe='active',  # Safe search
            ).execute()
            
            # Extract image URLs
            image_urls = []
            
            # List of video sites to exclude
            blocked_domains = [
                'youtube.com', 'aparat.com', 'dideo.ir', 'namasha.com', 
                'tamasha.com', 'mp4.ir', 'vid.ir', 'namayish.com', 
                'telewebion.com', 'jalebter.com', 'wisgoon.com'
            ]
            
            if 'items' in result:
                for item in result['items']:
                    if 'link' in item:
                        link = item['link'].lower()
                        display_link = item.get('displayLink', '').lower()
                        
                        # Check if link comes from a blocked domain
                        is_blocked = False
                        for domain in blocked_domains:
                            if domain in link or domain in display_link:
                                is_blocked = True
                                break
                        
                        if not is_blocked:
                            image_urls.append(item['link'])
            
            return image_urls
            
        except Exception as e:
            # If we went past the last result, Google API might return 400 or similar
            print(f"Warning: Search failed (might be out of results): {str(e)}")
            return []
    
    def download_images(self, image_urls: list, save_dir: str, topic: str, start_file_index: int = 0, existing_hashes: set = None) -> list:
        # Note: save_dir is now expected to be the full path including sub_folder

        """
        Download images from URLs and save them locally
        
        Args:
            image_urls: List of image URLs to download
            save_dir: Directory to save images
            topic: Topic name for file naming
            start_file_index: Starting index for file naming to avoid overwrites
            
        Returns:
            list: List of saved file paths
        """
        # Create directory if it doesn't exist
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        if existing_hashes is None:
            existing_hashes = set()
        
        saved_files = []
        
        for idx, url in enumerate(image_urls):
            try:
                # Download image
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = 'jpg'
                elif 'png' in content_type:
                    ext = 'png'
                elif 'webp' in content_type:
                    ext = 'webp'
                else:
                    ext = 'jpg'  # Default to jpg
                
                # Create safe filename
                safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_topic = safe_topic.replace(' ', '_')[:50]  # Limit length
                
                # Use start_file_index to ensure unique names across batches
                current_idx = start_file_index + idx
                filename = f"{safe_topic}_image_{current_idx + 1}.{ext}"
                filepath = os.path.join(save_dir, filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Validate the image by trying to open it
                try:
                    # PILImage is imported at top level now, but leaving the local import check if needed or just use global
                    img = PILImage.open(filepath)
                    img.verify()  # Verify it's a valid image
                    
                    # Re-open for hashing because verify() can close the file or consume it
                    img = PILImage.open(filepath)
                    
                    # Compute perceptual hash
                    current_hash = imagehash.phash(img)
                    
                    # Check for duplicates
                    is_duplicate = False
                    if existing_hashes:
                        # Check against existing hashes with a tolerance
                        # Hamming distance of 5 or less usually means duplicate/near-duplicate
                        for h in existing_hashes:
                            if current_hash - h < 5:
                                is_duplicate = True
                                break
                    
                    if is_duplicate:
                        print(f"Skipping duplicate image: {url}")
                        img.close()
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        continue
                        
                    # If unique, add to set and saved_files
                    existing_hashes.add(current_hash)
                    saved_files.append(filepath)
                    # Don't forget to close the image
                    img.close()
                except Exception as img_error:
                    print(f"Invalid image file {filepath}: {str(img_error)}")
                    # Delete invalid image
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    continue
                
            except Exception as e:
                print(f"Failed to download image {url}: {str(e)}")
                continue
        
        return saved_files
    
    def get_images_for_topic(self, topic: str, num_images: int = 5, sub_folder: str = None) -> list:
        """
        Complete workflow: search and download images for a topic with retry logic
        
        Args:
            topic: Topic to search images for
            num_images: Number of images to download
            sub_folder: Optional sub-folder within MEDIA_ROOT/images (e.g. 'presentations/user_1/uuid/')
            
        Returns:
            list: List of saved image file paths
        """
        import time
        from django.conf import settings
        
        if sub_folder:
             # sub_folder is expected to be relative to MEDIA_ROOT
             save_dir = os.path.join(settings.MEDIA_ROOT, sub_folder)
        else:
             # Fallback to old behavior
             save_dir = os.path.join(settings.MEDIA_ROOT, 'images')

        start_time = time.time()
        
        all_saved_files = []
        all_hashes = set()
        current_start_index = 1
        
        print(f"Starting image search for '{topic}' (Target: {num_images})")
        
        while True:
            elapsed_time = time.time() - start_time
            
            # Check if we have enough images
            if len(all_saved_files) >= num_images:
                print(f"Found enough images ({len(all_saved_files)}). Stopping.")
                break
            
            # Check timeout condition: Only enforce if we have fewer than 3 images
            if len(all_saved_files) < 3:
                if elapsed_time > 60:
                    print(f"Timeout reached (60s) with {len(all_saved_files)} images. Proceeding with what we have.")
                    break
            else:
                # If we have at least 3 images, we don't need to wait for 60s, 
                # but we can stop if we've tried enough or if it's taking too long (e.g. 10s extra)
                if elapsed_time > 60: 
                    break
            
            try:
                print(f"Searching batch starting at index {current_start_index}...")
                # Fetch more results to increase chances
                image_urls = self.search_images(topic, num_images=10, start_index=current_start_index)
                
                if not image_urls:
                    print("No more images found from API.")
                    break
                
                # Download images
                new_files = self.download_images(
                    image_urls, 
                    save_dir, 
                    topic, 
                    start_file_index=len(all_saved_files),
                    existing_hashes=all_hashes
                )
                
                all_saved_files.extend(new_files)
                print(f"Downloaded {len(new_files)} valid images in this batch. Total: {len(all_saved_files)}")
                
                # Move to next page
                current_start_index += 10
                
                # Safety break
                if current_start_index > 50:
                    print("Reached search limit depth.")
                    break
                    
                # Small delay to be nice to API
                if len(all_saved_files) < num_images:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error in search loop: {str(e)}")
                # If we have critical error and no images, retry a bit
                if len(all_saved_files) < 3 and elapsed_time < 60:
                    time.sleep(2)
                    continue
                else:
                    break
        
        if not all_saved_files:
            # If we really have zero images, that's a problem, but we shouldn't crash the whole flow if possible.
            # But the caller expects a list.
            print("Warning: No images downloaded at all.")
            # We can return empty list and let the caller handle it (PDF service should handle empty images)
        
        return all_saved_files[:num_images]
