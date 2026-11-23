import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class ImageManager:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / 'generated_images'
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_images(self, prompt: str, image_data_list: List[bytes], ext: str = 'png') -> List[Dict]:
        date_dir = self.base_path / datetime.now().strftime('%Y-%m-%d')
        date_dir.mkdir(parents=True, exist_ok=True)
        
        existing = list(date_dir.glob('image_*.png'))
        start_num = len(existing) + 1
        
        saved = []
        for i, img_data in enumerate(image_data_list):
            filename = f'image_{start_num + i:03d}.{ext}'
            filepath = date_dir / filename
            with open(filepath, 'wb') as f:
                f.write(img_data)
            saved.append({
                'filename': filename,
                'path': str(filepath),
                'url': f'/generated/{date_dir.name}/{filename}',
                'size': len(img_data)
            })
        return saved
    
    def get_storage_info(self) -> Dict:
        total_size = 0
        file_count = 0
        for f in self.base_path.rglob('*'):
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'base_path': str(self.base_path)
        }
    
    def cleanup_old_images(self, days: int) -> int:
        cutoff = datetime.now().timestamp() - (days * 86400)
        deleted = 0
        for f in self.base_path.rglob('*'):
            if f.is_file() and f.stat().st_mtime < cutoff:
                try:
                    f.unlink()
                    deleted += 1
                except OSError:
                    pass
        for d in self.base_path.iterdir():
            if d.is_dir() and not any(d.iterdir()):
                try:
                    d.rmdir()
                except OSError:
                    pass
        return deleted
    
    def get_generation_images(self, gen_id: int) -> List[Dict]:
        # This would need a mapping from generation ID to images
        # For now, return empty - can be enhanced with a DB link
        return []