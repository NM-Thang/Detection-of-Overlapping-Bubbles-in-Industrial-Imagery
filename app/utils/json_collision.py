import numpy as np
from matplotlib.path import Path

def analyze_collisions(details, img_shape):
    """
    Analyzes StarDist details to detect ray collisions with borders and other bubbles.
    
    Args:
        details (dict): The dictionary returned by StarDist predict_instances. 
                        Expected keys: 'points' (centers), 'coord' (rays) or 'dist'.
                        StarDist 'details' usually has 'points' and 'dist'.
        img_shape (tuple): (Height, Width) of the image.
        
    Returns:
        np.ndarray: Collision matrix of shape (N, n_rays) where:
                    0=None, 1=Border, 2=Bubble
    """
    
    coords = details.get('coord', [])
    # details['points'] might be useful for reference but coord has the vertices
    
    if coords is None or len(coords) == 0:
        return np.array([])
        
    height, width = img_shape
    n_bubbles = len(coords)
    
    # We need to determine n_rays from the first valid item
    # But usually all have same n_rays.
    # Let's peek at the first one to set standard n_rays for the return matrix
    try:
        first_poly = np.array(coords[0])
        n_rays = max(first_poly.shape) # assuming shape is (2, N) or (N, 2)
    except:
        n_rays = 32 # Fallback
    
    bubbles_polygons = [] 
    bubbles_tips = []     
    
    for i in range(n_bubbles):
        poly = coords[i] # This is a list or array for one bubble
        poly_arr = np.array(poly)
        
        # Standardize shape to (n_rays, 2) -> [[y, x], ...]
        # Logic copied from viewmodel.py for consistency
        tips = None
        
        if poly_arr.shape[0] == 2 and poly_arr.shape[1] > 2:
            # Shape (2, N) -> Transpose to (N, 2)
            tips = poly_arr.T
        elif poly_arr.shape[1] == 2 and poly_arr.shape[0] > 2:
            # Shape (N, 2) -> Already correct
            tips = poly_arr
        else:
            # Unexpected shape
            # Create dummy to avoid crash, but this shouldn't happen with valid stardist output
            tips = np.zeros((n_rays, 2))
            
        # Update n_rays if this bubble implies a different number (though usually constant)
        # The return matrix must be rectangular (N, n_rays). 
        # If n_rays varies per bubble, we have a problem for a simple numpy array return.
        # Assuming fixed rays for now as per standard StarDist.
        
        bubbles_tips.append(tips)
        bubbles_polygons.append(Path(tips))

    # 2. Analyze Collisions
    all_collisions = []
    
    for i in range(n_bubbles):
        tips = bubbles_tips[i]
        collisions = np.zeros(n_rays, dtype=int)
        
        for r_idx in range(n_rays):
            ty, tx = tips[r_idx]
            
            # Check A: Border (Flag = 1)
            # Use a small margin or exact bounds
            if ty <= 0 or ty >= height - 1 or tx <= 0 or tx >= width - 1:
                collisions[r_idx] = 1
                continue # Priority to border
            
            # Check B: Other Bubbles (Flag = 2)
            # We check if this tip is inside any OTHER bubble's polygon
            is_touching_other = False
            for j in range(n_bubbles):
                if i == j: continue
                
                # Expand the polygon slightly? 
                # Ideally, exact touch implies the tip is ON the boundary.
                # However, StarDist output might slightly overlap.
                # We check if point is contained.
                # radius=0 means exact point check.
                if bubbles_polygons[j].contains_point((ty, tx), radius=1.0):
                    is_touching_other = True
                    break
            
            if is_touching_other:
                collisions[r_idx] = 2
        
        all_collisions.append(collisions)
        
    return np.array(all_collisions) # Return (N, n_rays) array

def line_intersection(p1, p2, p3, p4):
    """
    Finds intersection between Line Segment (p1, p2) and Line Segment (p3, p4).
    Returns point (y, x) if intersection exists within strict segment bounds, else None.
    Inputs are (y, x) tuples/arrays.
    """
    y1, x1 = p1
    y2, x2 = p2
    y3, x3 = p3
    y4, x4 = p4
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None # Parallel
        
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    # Check if intersection is within segments
    # t, u in [0, 1]
    if 0 <= t <= 1 and 0 <= u <= 1:
        # Intersection Point
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return np.array([py, px])
        
    return None

def resolve_collisions(details, img_shape):
    """
    Resolves collisions by modifying ray coordinates.
    Logic:
    1. Border: Clip to intersection.
    2. Occlusion: Clip to intersection with higher-prob bubbles.
    
    Returns:
        list: coord_resolved (List of (2, N) or (N, 2) arrays matching input format)
    """
    coords = details.get('coord', [])
    probs = details.get('prob', [])
    centers = details.get('points', [])
    
    coords = details.get('coord', [])
    probs = details.get('prob', [])
    centers = details.get('points', [])
    
    if coords is None or len(coords) == 0:
        return coords
        
    if probs is None or len(probs) == 0:
        # Fallback if probs missing/mismatch
        probs = [1.0] * len(coords)
        
    if centers is None or len(centers) == 0:
        return coords # Cannot resolve without centers
        
    height, width = img_shape
    n_bubbles = len(coords)
    
    # 1. Sort by Probability Descending
    # usage: indices[0] is index of highest prob bubble
    indices = np.argsort(probs)[::-1]
    
    # Store resolved polygons (mapped by original index)
    # Initialize with copies of original to avoid mutating input during calc
    resolved_map = {} 
    
    # Pre-compute bounding boxes for all bubbles
    # Format: idx -> (min_y, min_x, max_y, max_x)
    bboxes = {}
    for i in range(n_bubbles):
        poly = np.array(coords[i])
        # Standardize for bbox calc
        if poly.shape[0] == 2 and poly.shape[1] > 2:
             pts = poly.T
        else:
             pts = poly
        
        # Force scalar float to avoid ambiguous truth value errors with 0-d numpy arrays
        min_vals = np.min(pts, axis=0)
        max_vals = np.max(pts, axis=0)
        
        min_y, min_x = float(min_vals[0]), float(min_vals[1])
        max_y, max_x = float(max_vals[0]), float(max_vals[1])
        bboxes[i] = (min_y, min_x, max_y, max_x)

    # Helper to standardize shape to (N, 2) [y, x]
    def get_poly_Nx2(idx):
        p = np.array(coords[idx])
        if p.shape[0] == 2 and p.shape[1] > 2:
            return p.T
        return p

    def bbox_overlap(b1, b2):
        # b: (min_y, min_x, max_y, max_x)
        y1_min, x1_min, y1_max, x1_max = b1
        y2_min, x2_min, y2_max, x2_max = b2
        
        if x1_max < x2_min or x2_max < x1_min: return False
        if y1_max < y2_min or y2_max < y1_min: return False
        return True
        
    # Process in order of probability (High -> Low)
    for i in indices:
        # Original Polygon (Standardized)
        poly = get_poly_Nx2(i)
        center = np.array(centers[i])
        n_rays = len(poly)
        
        new_poly = poly.copy()
        bbox_curr = bboxes[i]
        
        # Current Bubble: Check rays
        for r in range(n_rays):
            tip = new_poly[r]
            
            # --- Check 1: Border Collision ---
            if not (0 <= tip[0] <= height-1 and 0 <= tip[1] <= width-1):
                border_segs = [
                    ((0, 0), (0, width-1)),      # Top
                    ((height-1, 0), (height-1, width-1)), # Bottom
                    ((0, 0), (height-1, 0)),     # Left
                    ((0, width-1), (height-1, width-1))   # Right
                ]
                
                best_intersect = None
                best_dist = float('inf')
                
                for p_start, p_end in border_segs:
                    inter = line_intersection(center, tip, p_start, p_end)
                    if inter is not None:
                        d = np.linalg.norm(inter - center)
                        if d < best_dist:
                            best_dist = d
                            best_intersect = inter
                
                if best_intersect is not None:
                    new_poly[r] = best_intersect
                    tip = best_intersect # Update tip for next check
            
            # --- Check 2: Occlusion by Higher Prob Bubbles ---
            best_occ_intersect = None
            best_occ_dist = float('inf')
            
            # Ray Bounding Box (Center to Tip)
            ray_min_y = min(center[0], tip[0])
            ray_max_y = max(center[0], tip[0])
            ray_min_x = min(center[1], tip[1])
            ray_max_x = max(center[1], tip[1])
            ray_bbox = (ray_min_y, ray_min_x, ray_max_y, ray_max_x)

            # Check against bubbles ALREADY processed (higher prob)
            for prev_i in indices:
                if prev_i == i: break 
                
                # OPTIMIZATION: Check Bounding Box Overlap first
                # Check 1: Does Current Bubble BBox overlap Blocker BBox? (Coarse check)
                if not bbox_overlap(bbox_curr, bboxes[prev_i]):
                     continue

                # Check 2: Does Ray BBox overlap Blocker BBox? (Finer check)
                if not bbox_overlap(ray_bbox, bboxes[prev_i]):
                    continue
                
                blocker_poly = resolved_map[prev_i] 
                
                # Check intersection of Ray(Center -> Tip) with Polygon Segments
                n_b_rays = len(blocker_poly)
                for b_r in range(n_b_rays):
                    p_start = blocker_poly[b_r]
                    p_end = blocker_poly[(b_r + 1) % n_b_rays]
                    
                    inter = line_intersection(center, tip, p_start, p_end)
                    if inter is not None:
                        d = np.linalg.norm(inter - center)
                        # We want the intersection closest to center (entry point)
                        if d < best_occ_dist:
                            best_occ_dist = d
                            best_occ_intersect = inter
                            
            if best_occ_intersect is not None:
                new_poly[r] = best_occ_intersect
                
        # Store result
        resolved_map[i] = new_poly

    # Reconstruct list string/array in original order
    final_coords = []
    modified_flags = [False] * n_bubbles
    original_coords = details.get('coord', [])
    
    for i in range(n_bubbles):
        res_poly = resolved_map[i]
        
        # Check modification (by comparing with original or using flag tracked during loop)
        # Tracking during loop is cleaner but I need to pass it out.
        # Let's check simply: if any point in res_poly != original poly[i] standardized
        orig_poly_std = get_poly_Nx2(i)
        if not np.array_equal(res_poly, orig_poly_std):
            modified_flags[i] = True
            
        # Restore original shape (N, 2) or (2, N)
        orig_shape = np.array(original_coords[i]).shape
        if orig_shape[0] == 2 and orig_shape[1] > 2:
             final_coords.append(res_poly.T.tolist())
        else:
             final_coords.append(res_poly.tolist())
             
    return final_coords, modified_flags
