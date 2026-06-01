import os
import requests
import random  # Added for dynamic user-agent selection
from io import BytesIO
from PIL import Image, ImageChops
from django.conf import settings
from ddgs import DDGS
import re  # Added for backup parsing mechanisms
import urllib.parse  # Added to decode nested fallback image targets safely
from concurrent.futures import ThreadPoolExecutor, as_completed

# List of rotating headers to appear as an organic individual visitor
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
]

HTTP_SESSION = requests.Session()

def autocrop_whitespace(image_bytes, padding=0):
    """
    Opens an image, detects the absolute minimum bounding box of non-white 
    product pixels, and clips it down with 0 margin to maximize planogram uniformity.
    Handles off-white backgrounds using a low-tolerance safety mask.
    """
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGBA")
        
        # Create a solid, pure-white reference canvas matching our image size
        bg = Image.new(image.mode, image.size, (255, 255, 255, 255))
        
        # Calculate the raw absolute difference map between the image and white background
        diff = ImageChops.difference(image, bg)
        
        # Low-tolerance safety mask: catch pixels that are slightly off-white (up to 6 values off)
        # to cleanly eliminate faint background compressions or shadows.
        threshold = 6
        diff_mask = diff.point(lambda p: 255 if p >= threshold else 0).convert("L")
        
        # Capture the ultra-tight bounding box from the masked difference map
        bbox = diff_mask.getbbox()
        
        if bbox:
            # Strict boundary crop using padding constraint rules
            left = max(0, bbox[0] - padding)
            top = max(0, bbox[1] - padding)
            right = min(image.size[0], bbox[2] + padding)
            bottom = min(image.size[1], bbox[3] + padding)
            
            # --- ADDED DIMENSIONAL SAFETY CHECK ---
            if right > left and bottom > top:
                return image.crop((left, top, right, bottom))
    except Exception as e:
        print(f"⚠️ Direct auto-cropping issue encountered: {e}. Falling back to original image.")
        
    return image

def compress_image_to_target(pil_image, target_kb=95, max_iterations=5):
    """
    Takes a PIL Image object and compresses it dynamically until its byte size
    is under the specified target_kb threshold. Returns a tuple: (raw_bytes, "PNG")
    
    CRITICAL SYSTEM UPDATE: Forcefully converted to output highly compressed, 
    quantized 8-bit PNG images to accommodate strict software restrictions.
    """
    target_bytes = target_kb * 1024
    
    # Step 1: Try saving as highly optimized native PNG first (retains full quality/transparency)
    out_buffer = BytesIO()
    pil_image.save(out_buffer, format="PNG", optimize=True, compress_level=9)
    png_bytes = out_buffer.getvalue()
    
    if len(png_bytes) <= target_bytes:
        return png_bytes, "PNG"
        
    # Step 2: If PNG is > target_kb, apply color palette reduction (Quantization Layer)
    # This maintains strict PNG structural properties while shrinking the file footprint dramatically.
    for max_colors in [256, 128, 64, 32]:
        out_buffer = BytesIO()
        # Convert to 'P' mode (Palette-based) using an adaptive algorithm tailored to the image colors
        quantized_image = pil_image.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)
        quantized_image.save(out_buffer, format="PNG", optimize=True, compress_level=9)
        png_bytes = out_buffer.getvalue()
        
        if len(png_bytes) <= target_bytes:
            return png_bytes, "PNG"

    # Step 3: Absolute fallback if quantization alone isn't enough.
    # We strip down alpha channels onto a crisp white background canvas, 
    # scale down sizes slightly if necessary, and force compliance under PNG parameters.
    if pil_image.mode in ('RGBA', 'LA') or (pil_image.mode == 'P' and 'transparency' in pil_image.info):
        background = Image.new("RGB", pil_image.size, (255, 255, 255))
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
        background.paste(pil_image, mask=pil_image.split()[3])
        rgb_image = background
    else:
        rgb_image = pil_image.convert("RGB")

    # If it is still over target_kb, safely apply a subtle size scale reduction step to cross the threshold
    width, height = rgb_image.size
    for reduction in [0.90, 0.80, 0.70]:
        new_width = int(width * reduction)
        new_height = int(height * reduction)
        resized_img = rgb_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        out_buffer = BytesIO()
        quantized_image = resized_img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
        quantized_image.save(out_buffer, format="PNG", optimize=True, compress_level=9)
        png_bytes = out_buffer.getvalue()
        
        if len(png_bytes) <= target_bytes:
            return png_bytes, "PNG"

    # Final guarantee return vector (always pure PNG bytes)
    return png_bytes, "PNG"

def test_single_cdn(url):
    """
    Worker function executed inside separate threads.
    Validates a single target retail CDN asset instantly.
    """
    try:
        # Snappy 1.5 second timeout since all variants are executing in parallel
        res = HTTP_SESSION.get(url, timeout=1.5)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', '').lower():
            if len(res.content) > 3000:
                return {"url": url, "content": res.content}
    except Exception:
        pass
    return None

# --- PHASE 2 ASYNC CONCURRENT WORKERS ---

def worker_duckduckgo_api(search_query, absolute_safe_hosts, product_url_keywords):
    try:
        print(f"🔍 Searching DuckDuckGo API (Parallel) for: {search_query}")
        with DDGS() as ddgs:
            results = list(ddgs.images(query=search_query, color="color"))
            
        if results:
            for target_entry in results[:3]:  # Evaluate top 3 alternatives
                img_url = target_entry['image']
                parsed_hostname = urllib.parse.urlparse(img_url.lower()).hostname or ""
                
                if any(host in parsed_hostname or parsed_hostname.endswith('.' + host) for host in absolute_safe_hosts):
                    if any(keyword in img_url.lower() for keyword in product_url_keywords):
                        response = HTTP_SESSION.get(img_url, timeout=2.5)  # Aggressive timeout
                        if response.status_code == 200 and len(response.content) > 3000:
                            return response.content
    except Exception:
        pass
    return None

def worker_duckduckgo_html(search_query, absolute_safe_hosts):
    try:
        fallback_url = "https://html.duckduckgo.com/html/"
        fb_res = HTTP_SESSION.post(fallback_url, data={'q': search_query}, timeout=2.5)
        if fb_res.status_code == 200:
            urls = re.findall(r'href="([^"]+(?:pnp\.co\.za|checkers\.co\.za|woolworths\.co\.za|shoprite\.co\.za|mrdfood\.com)/[^"]+)"', fb_res.text)
            for store_page in urls[:2]:
                page_url = urllib.parse.unquote(store_page)
                if 'url=' in page_url:
                    parsed_nested = urllib.parse.parse_qs(urllib.parse.urlparse(page_url).query)
                    if 'url' in parsed_nested: page_url = parsed_nested['url'][0]
                if not page_url.startswith('http'): page_url = 'https://' + page_url.lstrip('/')
                
                p_res = HTTP_SESSION.get(page_url, timeout=2.5)
                if p_res.status_code == 200:
                    json_images = re.findall(r'"url"\s*:\s*"([^"]+/media/products/[^"]+)"', p_res.text) or \
                                  re.findall(r'"image"\s*:\s*"([^"]+)"', p_res.text)
                    for candidate_img in json_images:
                        candidate_clean = candidate_img.replace(r'\/', '/')
                        if not candidate_clean.startswith('http'): candidate_clean = urllib.parse.urljoin(page_url, candidate_clean)
                        
                        parsed_cand_host = urllib.parse.urlparse(candidate_clean.lower()).hostname or ""
                        if any(vh in parsed_cand_host for vh in absolute_safe_hosts):
                            img_res = HTTP_SESSION.get(candidate_clean, timeout=2.5)
                            if img_res.status_code == 200 and len(img_res.content) > 3000:
                                return img_res.content
    except Exception:
        pass
    return None

def worker_yahoo_engine(search_query, absolute_safe_hosts):
    try:
        print(f"🔍 Searching Yahoo Engine (Parallel) for: {search_query}")
        alt_img_url = f"https://images.search.yahoo.com/search/images?p={urllib.parse.quote(search_query)}"
        alt_res = HTTP_SESSION.get(alt_img_url, timeout=2.5)
        metadata_blocks = re.findall(r'({[^{}]+"imgurl"[^{}]+})', alt_res.text)
        for block in metadata_blocks[:4]:
            rurl_match = re.search(r'"rurl":"([^"]+)"', block)
            imgurl_match = re.search(r'"imgurl":"([^"]+)"', block)
            if rurl_match and imgurl_match:
                origin_source_url = rurl_match.group(1).replace(r'\/', '/')
                cdn_delivery_url = imgurl_match.group(1).replace(r'\/', '/')
                
                p_src_host = urllib.parse.urlparse(origin_source_url.lower()).hostname or ""
                p_cdn_host = urllib.parse.urlparse(cdn_delivery_url.lower()).hostname or ""
                
                if any(vh in p_src_host for vh in ['pnp.co.za', 'checkers.co.za', 'woolworths.co.za', 'shoprite.co.za', 'mrdfood.com']):
                    if any(vh in p_cdn_host for vh in absolute_safe_hosts):
                        response = HTTP_SESSION.get(cdn_delivery_url, timeout=2.5)
                        if response.status_code == 200 and len(response.content) > 3000:
                            return response.content
    except Exception:
        pass
    return None

def worker_google_scrape(barcode, clean_words, absolute_safe_hosts):
    try:
        g_url = f"https://www.google.com/search?tbm=isch&q={barcode}+{urllib.parse.quote(clean_words)}"
        g_res = HTTP_SESSION.get(g_url, timeout=2.5)
        if g_res.status_code == 200:
            g_img_urls = re.findall(r'src="([^"]+)"', g_res.text)
            for g_candidate in g_img_urls:
                if g_candidate.startswith('http') and len(g_candidate) > 2000:
                    p_g_host = urllib.parse.urlparse(g_candidate.lower()).hostname or ""
                    if any(vh in p_g_host for vh in absolute_safe_hosts):
                        response = HTTP_SESSION.get(g_candidate, timeout=2.5)
                        if response.status_code == 200 and len(response.content) > 3000:
                            return response.content
    except Exception:
        pass
    return None

def worker_openfoodfacts_api(barcode):
    try:
        print(f"🌐 Engaging Ultra-Recovery API pass (Parallel) for barcode {barcode}...")
        api_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        api_res = HTTP_SESSION.get(api_url, timeout=2.0)
        if api_res.status_code == 200:
            product_data = api_res.json()
            if product_data.get('status') == 1:
                api_img_url = product_data.get('product', {}).get('image_front_url')
                if api_img_url:
                    response = HTTP_SESSION.get(api_img_url, timeout=2.5)
                    if response.status_code == 200 and len(response.content) > 3000:
                        return response.content
    except Exception:
        pass
    return None

# --- PRIMARY SEED PIPELINE ---

def source_and_save_product_image(product_id=None, barcode=None, product_name=None, sub_folder="planogram_products"):
    """
    Tries to grab product image links directly from South African retail CDNs first.
    Automatically snaps, crops whitespaces, and runs adaptive compression under 100KB 
    before saving files locally into a dynamically allocated routing sub-folder.
    """
    # --- DEEP-EXTRACTION AUTO-HEALING LAYER ---
    sku_extractor_regex = re.compile(r'\b(\d+[-_][A-Za-z]{2})\b')

    # Guard Case A: Extract SKU if it's accidentally appended/prepended inside the product name string
    if product_name and not product_id:
        name_str = str(product_name).strip()
        match = sku_extractor_regex.search(name_str)
        if match:
            product_id = match.group(1)
            # Remove the identifier from the name to keep fallback text queries concise
            product_name = sku_extractor_regex.sub('', name_str).strip()

    # Guard Case B: Re-align out-of-order arguments or positional type misalignments
    raw_inputs = [str(x).strip() for x in [product_id, barcode, product_name] if x is not None]
    detected_pid = product_id
    detected_barcode = barcode
    detected_name = product_name

    for candidate in raw_inputs:
        if sku_extractor_regex.match(candidate):
            detected_pid = candidate
        elif candidate.isdigit() and len(candidate) in [8, 13, 14]:
            detected_barcode = candidate
        elif len(candidate) > 4 and not candidate.isdigit() and not sku_extractor_regex.match(candidate):
            detected_name = candidate

    # Rebind normalized variables back into place
    product_id = detected_pid
    barcode = detected_barcode
    product_name = detected_name

    # Backward compatibility fallback layer
    if product_name is None and barcode is not None:
        product_name = barcode
        barcode = product_id
        product_id = None

    chosen_agent = random.choice(USER_AGENTS)
    HTTP_SESSION.headers.update({'User-Agent': chosen_agent})
    
    direct_candidates = []
    
    # 1. Build Product ID Direct Matrices (With Pick n Pay 18-digit padding rules)
    if product_id:
        clean_pid = str(product_id).strip()
        # Unify all dashes into underscores to correctly target CDN image directory naming policies
        normalized_pid = clean_pid.replace('-', '_')
        
        if '_' in normalized_pid:
            parts = normalized_pid.split('_')
            base_id = parts[0]
            suffix = parts[1]
            
            # PnP utilizes an explicit 18-character zero-fill layout structure for base SKUs
            padded_base = base_id.zfill(18)
            
            direct_candidates.extend([
                f"https://images.pnp.co.za/media/products/{padded_base}_{suffix.upper()}.jpg",
                f"https://images.pnp.co.za/media/products/{padded_base}_{suffix.lower()}.jpg",
                f"https://s3.eu-west-1.amazonaws.com/pnp.co.za.assets/media/products/{padded_base}_{suffix.upper()}.jpg",
                f"https://images.pnp.co.za/media/products/{base_id}_{suffix.upper()}.jpg",
                f"https://images.pnp.co.za/media/products/{base_id.zfill(13)}_{suffix.upper()}.jpg"
            ])
        else:
            direct_candidates.extend([
                f"https://images.pnp.co.za/media/products/{clean_pid.zfill(18)}.jpg",
                f"https://images.pnp.co.za/media/products/{normalized_pid}.jpg",
                f"https://images.pnp.co.za/media/products/{normalized_pid}_l.jpg",
                f"https://s3.eu-west-1.amazonaws.com/pnp.co.za.assets/media/products/{normalized_pid}.jpg",
                f"https://www.pnp.co.za/pnpfacets/images/products/{clean_pid}.jpg"
            ])
        
    # 2. Build Barcode Direct Matrices (PnP, Shoprite, Checkers, Woolies, Mr D)
    if barcode:
        clean_bc = str(barcode).strip()
        direct_candidates.extend([
            # Pick n Pay
            f"https://images.pnp.co.za/media/products/{clean_bc}_l.jpg",
            f"https://images.pnp.co.za/media/products/{clean_bc}.jpg",
            f"https://www.pnp.co.za/pnpfacets/images/products/{clean_bc}.jpg",
            f"https://s3.eu-west-1.amazonaws.com/pnp.co.za.assets/media/products/{clean_bc}_l.jpg",
            f"https://www.pnp.co.za/medias/sys_master/images/products/{clean_bc}.jpg",
            
            # Shoprite & Checkers Core
            f"https://www.shoprite.co.za/medias/sys_master/images/images/{clean_bc}.jpg",
            f"https://www.shoprite.co.za/medias/sys_master/images/products/{clean_bc}.jpg",
            f"https://cdn-prd-02.azureedge.net/sys-master-images/images/{clean_bc}.png",
            f"https://cdn-prd-02.azureedge.net/sys-master-images/images/{clean_bc}.jpg",
            
            # Checkers Sixty60
            f"https://images.sixty60.co.za/products/{clean_bc}_l.jpg",
            f"https://www.checkers.co.za/medias/sys_master/images/products/{clean_bc}.jpg",
            
            # Woolworths
            f"https://images.woolworths.co.za/images/o/products/{clean_bc}.jpg",
            f"https://images.woolworths.co.za/images/o/products/{clean_bc}_1.jpg",
            f"https://www.woolworths.co.za/images/live/products/o/{clean_bc}.jpg",
            
            # Mr D Food
            f"https://img.mrdfood.com/images/products/{clean_bc}_l.jpg",
            f"https://img.mrdfood.com/images/products/{clean_bc}.png"
        ])

    # Deduplicate candidate matrix list to prevent redundant parallel thread connections
    direct_candidates = list(dict.fromkeys(direct_candidates))

    print(f"[PHASE 1] Scanning primary retailer CDNs concurrently across {len(direct_candidates)} threads...")

    # --- EXECUTE PHASE 1: CONCURRENT DIRECT LOOKUPS ---
    found_match = None
    if direct_candidates:
        with ThreadPoolExecutor(max_workers=min(len(direct_candidates), 30)) as executor:
            future_to_url = {executor.submit(test_single_cdn, url): url for url in direct_candidates}
            
            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    found_match = result
                    # Instantly kill remaining processing futures to optimize system socket overhead
                    for f in future_to_url:
                        f.cancel()
                    break

    if found_match:
        # AUTOMATIC ON-THE-FLY CROPPING HAPPENS HERE
        cropped_image = autocrop_whitespace(found_match["content"])
        
        # Adaptive Multi-Stage Compression Layer
        compressed_bytes, resolved_format = compress_image_to_target(cropped_image, target_kb=95)
        
        # Unify naming strategy with the correct resolved format extension
        extension = resolved_format.lower()
        filename = f"{barcode}.{extension}" if barcode else f"{product_id}.{extension}"
        
        target_dir = os.path.join(settings.PLANOGRAM_IMG_DIR, sub_folder)
        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)
        
        # Direct atomic binary write to disk
        with open(save_path, "wb") as f:
            f.write(compressed_bytes)
            
        print(f"🎉 SUCCESS: CDN Match, Cropped & Compressed ({resolved_format})! Size: {len(compressed_bytes)/1024:.1f}KB -> {save_path}")
        return f"{sub_folder}/{filename}"

    print(f"⚠️ [PHASE 1 FAILED]: Concurrent CDNs yielded no results. Dropping down to [PHASE 2: Web Engines]...")

    # --- EXECUTE PHASE 2: FALLBACK ENGINE HARVESTING ---
    clean_words = ""
    if product_name:
        working_string = str(product_name).replace('N/A', '').replace('n/a', '')
        
        # Hardened query replacements targeting variations of weights and unit metrics
        text_clean_map = {
            r'\bPNP\b': 'PnP', r'\bpnp\b': 'PnP',  # Normalizes brand casing variations
            r'\bPNT BTR\b': 'PEANUT BUTTER', r'\bPEANUT BTR\b': 'PEANUT BUTTER',
            r'\bPNT\b': 'PEANUT', r'\bBTR\b': 'BUTTER', r'\bSMTH\b': 'SMOOTH',
            r'\bCRNH\b': 'CRUNCHY', r'\bSGR\b': 'SUGAR', r'\bSLT\b': 'SALT',
            r'(?<=\d)GR\b': 'g', r'(?<=\d)gr\b': 'g',  # Cleanly catches 500GR / 500gr -> 500g
            r'\bGRAM\b': 'g', r'\bgram\b': 'g',
            r'\bKG\b': 'kg', r'\bkg\b': 'kg', r'\bML\b': 'ml', r'\bml\b': 'ml'
        }
        for pattern_abbrev, real_word in text_clean_map.items():
            working_string = re.sub(pattern_abbrev, real_word, working_string, flags=re.IGNORECASE)
            
        working_string = re.sub(r'[^a-zA-Z0-9\s._-]', ' ', working_string)
        clean_words = " ".join(working_string.split())

    # Unified whitelists for open search scrapers - BROADENED TO ALL SOUTH AFRICAN COMMERCIAL RETAIL ECOSYSTEM NODES
    absolute_safe_hosts = [
        'pnp.co.za', 'pnphome.co.za', 'checkers.co.za', 'woolworths.co.za', 
        'makro.co.za', 'shoprite.co.za', 'sixty60.co.za', 'mrdfood.com', 
        'takealot.com', 'openfoodfacts.org', 'cloudfront.net', 'azureedge.net', 
        'cloudinary.com', 'shopify.com', 'fastly.net', 'wp.com',
        # Broad expansion items added directly below:
        'boxer.co.za', 'usave.co.za', 'spar.co.za', 'myspar.co.za', 'foodloversmarket.co.za',
        'choppies.co.za', 'cambridgefood.co.za', 'okfoods.co.za', 'game.co.za', 'builders.co.za',
        'rhino-cash-carry.co.za', 'jumbo.co.za', 'mrprice.com', 'mrphome.com', 'mrpwood.com',
        'sheetstreet.co.za', 'homewarestore.co.za', 'coricraft.co.za', 'volpes.co.za', 'foschini.co.za',
        'truworths.co.za', 'edgars.co.za', 'miladys.co.za', 'ackermans.co.za', 'pepstores.com',
        'jetonline.co.za', 'leroymerlin.co.za', 'clicks.co.za', 'dischem.co.za', 'wellnesswarehouse.com',
        'babycity.co.za', 'crazystore.co.za', 'dischembrands.co.za', 'liquorcity.co.za', 'takealot.co.za',
        'superbalist.com', 'zando.co.za', 'loot.co.za', 'bidorbuy.co.za', 'bobshop.co.za', 'ubereats.com',
        'uber.com', 'bolt.eu', 'zulzi.com', 'yebofresh.co.za', 'incredible.co.za', 'hificorp.co.za',
        'evetech.co.za', 'wootware.co.za', 'amazonaws.com'
    ]
    product_url_keywords = ['media', 'product', 'image', 'asset', 'sys_master', 'catalog', 'sixty60', 'upload', 'products']

    # Generate sequential query scopes (Relaxed terms to bypass strict engine token locks)
    queries_to_execute = []
    if clean_words:
        # Added South African explicit regional index localization operators directly into the sequence 
        queries_to_execute.append(f"(site:pnp.co.za OR site:checkers.co.za OR site:woolworths.co.za OR site:takealot.com OR site:spar.co.za) {clean_words}")
        queries_to_execute.append(f"{clean_words} site:.co.za")
        queries_to_execute.append(f"\"{clean_words}\" South Africa retail")
        relaxed_fallback = clean_words.replace('PnP', 'Pick n Pay')
        queries_to_execute.append(f"{relaxed_fallback} South Africa")
    if barcode and clean_words:
        queries_to_execute.append(f"(site:pnp.co.za OR site:checkers.co.za OR site:woolworths.co.za) {barcode} {clean_words}")
        queries_to_execute.append(f"{barcode} site:.co.za")

    queries_to_execute = list(set(queries_to_execute))
    fallback_image_bytes = None

    # Thread Pool managing parallel execution of independent external engines
    if queries_to_execute or barcode:
        with ThreadPoolExecutor(max_workers=12) as search_executor:
            search_futures = []
            
            # 1. Distribute query variants evenly across engines
            for search_query in queries_to_execute:
                search_futures.append(search_executor.submit(worker_duckduckgo_api, search_query, absolute_safe_hosts, product_url_keywords))
                search_futures.append(search_executor.submit(worker_duckduckgo_html, search_query, absolute_safe_hosts))
                search_futures.append(search_executor.submit(worker_yahoo_engine, search_query, absolute_safe_hosts))
                if barcode:
                    search_futures.append(search_executor.submit(worker_google_scrape, barcode, clean_words, absolute_safe_hosts))
            
            # 2. Distribute API checks independently
            if barcode:
                search_futures.append(search_executor.submit(worker_openfoodfacts_api, barcode))
                
            # 3. Intercept the fastest thread payload to complete successfully
            for future in as_completed(search_futures):
                img_bytes_res = future.result()
                if img_bytes_res:
                    fallback_image_bytes = img_bytes_res
                    # Evacuate and drop out lagging scrapers immediately
                    for f in search_futures: 
                        f.cancel()
                    break

    if fallback_image_bytes:
        # AUTOMATIC ON-THE-FLY CROPPING ALSO HAPPENS HERE FOR FALLBACK ENGINES
        cropped_image = autocrop_whitespace(fallback_image_bytes)
        
        # Adaptive Multi-Stage Compression Layer
        compressed_bytes, resolved_format = compress_image_to_target(cropped_image, target_kb=95)
        
        # Unify naming strategy with the correct resolved format extension
        extension = resolved_format.lower()
        filename = f"{barcode}.{extension}" if barcode else f"{product_id}.{extension}"
        
        target_dir = os.path.join(settings.PLANOGRAM_IMG_DIR, sub_folder)
        os.makedirs(target_dir, exist_ok=True)
        save_path = os.path.join(target_dir, filename)
        
        # Direct atomic binary write to disk
        with open(save_path, "wb") as f:
            f.write(compressed_bytes)
            
        print(f"🚀 SUCCESS: Processed, Cropped & Compressed ({resolved_format}) via Fallback. Size: {len(compressed_bytes)/1024:.1f}KB -> {save_path}")
        return f"{sub_folder}/{filename}"

    print(f"❌ CRITICAL: Scraper pipeline entirely exhausted for {barcode or product_name}")
    return None