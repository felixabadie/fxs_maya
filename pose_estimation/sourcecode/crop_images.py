from PIL import Image
from pathlib import Path


def zoom_and_resize(image_path, output_path, zoom_factor, size=1024):
    """Zoomt ins Zentrum des Bildes und skaliert zurück auf size x size"""
    img = Image.open(image_path)
    w, h = img.size

    # Zuschneidebereich (zentral)
    crop_w, crop_h = w // zoom_factor, h // zoom_factor
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h

    img_cropped = img.crop((left, top, right, bottom))
    img_resized = img_cropped.resize((size, size), Image.LANCZOS)

    # Abspeichern
    img_resized.save(output_path)

def process_directory(input_dir, output_dir, zoom_factor=2, size=1024):
    """Bearbeitet alle Bilder in einem Ordner"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    for img_path in input_dir.iterdir():
        if img_path.suffix.lower() in valid_exts:
            output_path = output_dir / img_path.name
            zoom_and_resize(img_path, output_path, zoom_factor, size)
            print(f"verarbeitet: {img_path.name}")

if __name__ == "__main__":
    # Ordner anpassen
    input_folder = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Abbildungen_für_Bachelorarbeit\neu CNN\images_to_crop"   # Quelle
    output_folder = r"D:\fa026_DONT_TOUCH_OR_I_WILL_FIND_YOU\Abbildungen_für_Bachelorarbeit\neu CNN\cropped_images"  # Ergebnis

    process_directory(input_folder, output_folder, zoom_factor=1.5, size=1024)