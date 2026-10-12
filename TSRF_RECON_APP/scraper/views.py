import os
import re
import json
import time  # Added for rate-limit throttling

from django.shortcuts import render
from django.http import FileResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .image_scraper import source_and_save_product_image

@csrf_exempt
def automated_planogram_upload(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            product_id = data.get("product_id")
            barcode = data.get("barcode")
            product_name = data.get("product_name") 
            
            # 1. Grab raw string input from the user box (fallback to default)
            raw_folder = data.get("target_folder", "planogram_products").strip()
            
            # 2. SANITIZATION LAYER: Replace spaces with underscores and remove special characters
            clean_folder = raw_folder.replace(" ", "_")
            clean_folder = re.sub(r'[^a-zA-Z0-9_-]', '', clean_folder)
            
            # If the input matches the base folder name or becomes empty, use an empty string
            # This stops the scraper from creating a nested /planogram_products/planogram_products/ folder
            if not clean_folder or clean_folder == "planogram_products":
                sub_folder_arg = ""
            else:
                sub_folder_arg = clean_folder
            
            if not barcode or not product_name:
                return JsonResponse({"error": "Missing 'barcode' or 'product_name' in payload."}, status=400)
            
            time.sleep(2)
            
            # 3. Pass clean folder down to scraper pipeline
            relative_path = source_and_save_product_image(
                product_id=product_id, 
                barcode=barcode, 
                product_name=product_name,
                sub_folder=sub_folder_arg  # <-- Now passing the smart structural path arg
            )
            
            if relative_path:
                return JsonResponse({
                    "status": "success",
                    "barcode": barcode,
                    "saved_location": relative_path
                })
            else:
                return JsonResponse({
                    "status": "failed",
                    "barcode": barcode,
                    "error": f"Could not source image into targeted storage node."
                }, status=200)
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data provided."}, status=400)
            
    return JsonResponse({"error": "Only POST requests are permitted on this endpoint."}, status=405)


# Render the Home Page dashboard
def home_view(request):
    return render(request, 'home.html')


# Render the Bulk Image Source entry field
def source_view(request):
    return render(request, 'source.html')


def media_directory_explorer(request, subfolder=""):
    """
    Safely navigates, audits, and surfaces directory elements inside MEDIA_ROOT.
    Prevents directory lookup index errors by compiling assets into a clean UI dashboard grid.
    """
    clean_subfolder = subfolder.strip('/')
    
    # 🌟 CRITICAL FIX: If the requested path is a file, let Django serve it directly!
    # This ensures your <img> tags can actually load and display the pictures.
    lower_path = clean_subfolder.lower()
    if lower_path.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg')):
        file_disk_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, clean_subfolder))
        if os.path.exists(file_disk_path):
            return FileResponse(open(file_disk_path, 'rb'))
        raise Http404("Targeted media asset file does not exist on disk.")

    # =========================================================================
    # THE REST OF YOUR DIRECTORY EXPLORER LOGIC REMAINS EXACTLY THE SAME BELOW:
    # =========================================================================
    base_target_dir = settings.MEDIA_ROOT
    
    if clean_subfolder:
        target_abs_path = os.path.normpath(os.path.join(base_target_dir, clean_subfolder))
    else:
        target_abs_path = base_target_dir
        
    if not os.path.abspath(target_abs_path).startswith(os.path.abspath(base_target_dir)):
        raise Http404("Directory Security Invalidation Failure.")
        
    if not os.path.exists(target_abs_path):
        os.makedirs(target_abs_path, exist_ok=True)
        
    directories = []
    files = []
    
    try:
        with os.scandir(target_abs_path) as entries:
            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                    
                item_relative_route = os.path.relpath(entry.path, base_target_dir).replace('\\', '/')
                    
                if entry.is_dir():
                    directories.append({
                        'name': entry.name,
                        'relative_path': item_relative_route
                    })
                elif entry.is_file():
                    try:
                        stat = entry.stat()
                        size_kb = round(stat.st_size / 1024, 1)
                        size_str = f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb/1024, 2)} MB"
                    except (OSError, OverflowError):
                        size_str = "—"
                        
                    # Build clean absolute web accessible URL mappings
                    file_url = f"{settings.MEDIA_URL}{item_relative_route}"
                        
                    files.append({
                        'name': entry.name,
                        'url': file_url.replace('\\', '/'),
                        'size': size_str
                    })
    except Exception as e:
        print(f"FileSystem Scan Interrupted: {e}")

    parent_path = ""
    if clean_subfolder:
        parent_dir = os.path.dirname(clean_subfolder)
        parent_path = parent_dir.replace('\\', '/') if parent_dir else ""

    context = {
        'current_folder_name': os.path.basename(target_abs_path) or "Core Media Root",
        'current_relative_path': clean_subfolder,
        'parent_path': parent_path,
        'directories': sorted(directories, key=lambda x: x['name']),
        'files': sorted(files, key=lambda x: x['name']),
    }
    
    return render(request, 'media_explorer.html', context)


def games_view(request):
    return render(request, 'games.html')


def mario_view(request):
    return render(request, 'supermario.html')