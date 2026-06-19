import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
from pathlib import Path
from PIL import Image
import io
import imagehash
from generator.services.image_service import ImageService

class TestImageDeduplication(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_images_dedup'
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        self.service = ImageService()
        # Mock API key check to avoid init error if credentials missing in env
        self.service.api_key = "dummy"
        self.service.search_engine_id = "dummy"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('generator.services.image_service.requests.get')
    def test_duplicate_images(self, mock_get):
        # Create a dummy image
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        # Mock response to return this image
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = img_bytes
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_get.return_value = mock_response

        # Call download_images with 2 URLs (simulating duplicates)
        urls = ['http://example.com/1.jpg', 'http://example.com/2.jpg']
        
        saved_files = self.service.download_images(urls, self.test_dir, 'test_topic')

        # Should only save 1 file
        self.assertEqual(len(saved_files), 1)
        print(f"Saved {len(saved_files)} files from 2 duplicate URLs")
        
        # Verify hash set in service (if we were testing larger scope, but here checking result is enough)
        
    @patch('generator.services.image_service.requests.get')
    def test_near_duplicate_images(self, mock_get):
        # Create image A
        img1 = Image.new('RGB', (100, 100), color='blue')
        img1_byte_arr = io.BytesIO()
        img1.save(img1_byte_arr, format='JPEG')
        
        # Create image B (very similar, just one pixel different)
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.putpixel((50, 50), (0, 0, 250)) # Slight change
        img2_byte_arr = io.BytesIO()
        img2.save(img2_byte_arr, format='JPEG')

        # Setup mock to return different images for different calls
        mock_response1 = MagicMock()
        mock_response1.content = img1_byte_arr.getvalue()
        mock_response1.headers = {'content-type': 'image/jpeg'}
        
        mock_response2 = MagicMock()
        mock_response2.content = img2_byte_arr.getvalue()
        mock_response2.headers = {'content-type': 'image/jpeg'}

        mock_get.side_effect = [mock_response1, mock_response2]

        urls = ['http://example.com/1.jpg', 'http://example.com/2.jpg']
        saved_files = self.service.download_images(urls, self.test_dir, 'test_topic')
        
        # Hashes should be identical or very close for these images
        # Red and slightly different Red might be close. Blue and slightly different Blue.
        # Let's hope ImageHash captures this.
        
        self.assertEqual(len(saved_files), 1)
        print(f"Saved {len(saved_files)} files from 2 near-duplicate URLs")

if __name__ == '__main__':
    unittest.main()
