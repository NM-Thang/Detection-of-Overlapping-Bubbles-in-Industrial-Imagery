import numpy as np

class StatsCalculator:
    @staticmethod
    def calc_img_stats(img, bubble_list_rdc):
        """Calculates image size and basic breakdown stats"""
        if img is None:
            return {'size': "N/A", 'area_px': 0}
            
        h, w = img.shape
        img_area_px = h * w
        
        total_bub_mm = 0.0
        total_bub_px = 0.0
        
        for b in bubble_list_rdc:
            try:
                total_bub_mm += float(b.get('area_mm', 0))
                apx = b.get('area_px', 0)
                if apx != 'N/A':
                    total_bub_px += float(apx)
            except:
                pass
                
        ratio_factor = 0.0
        img_area_mm = 0.0
        ratio_mm = 0.0
        
        if total_bub_px > 0:
            ratio_factor = total_bub_mm / total_bub_px
            img_area_mm = img_area_px * ratio_factor
            ratio_mm = (total_bub_mm / img_area_mm) * 100
        
        return {
            'size': f"{w} x {h}",
            'count': str(len(bubble_list_rdc)),
            'total_bub_mm': f"{total_bub_mm:.2f}",
            'total_bub_px': f"{total_bub_px:.0f}",
            'img_area_mm': f"{img_area_mm:.2f}" if img_area_mm > 0 else "N/A",
            'ratio_mm': f"{ratio_mm:.2f} %",
            'ratio_factor': ratio_factor,
            'img_area_px': img_area_px
        }

    @staticmethod
    def calc_stardist_stats(json_details, ratio_factor, img_area_px):
        """Calculates stats based on StarDist JSON"""
        stats = {
            'count': "0",
            'prob': "0.0",
            'area_px': "0",
            'area_mm': "0.0",
            'ratio': "0.00 %",
            'list': []
        }
        
        if not json_details:
            return stats
            
        points = json_details.get('points', [])
        coords = json_details.get('coord', [])
        probs = json_details.get('prob', [])
        
        stats['count'] = str(len(points)) if points else "0"
        
        if probs:
            avg_prob = np.mean(probs)
            stats['prob'] = f"{avg_prob:.4f}"
        else:
            stats['prob'] = "N/A"
            
        total_sd_px = 0.0
        
        n_items = max(len(points) if points is not None else 0, len(coords) if coords is not None else 0)
        bubble_list = []
        
        for i in range(n_items):
            # Center
            cx, cy = 0, 0
            if points is not None and i < len(points):
                pt = points[i]
                if pt is not None:
                    cy, cx = pt[0], pt[1]
                    
            # Area Px
            area_px = 0.0
            if coords is not None and i < len(coords):
                c = coords[i]
                arr = np.array(c)
                poly = None
                if arr.ndim == 2:
                    if arr.shape[0] == 2 and arr.shape[1] > 2:
                        poly = arr.T
                    elif arr.shape[1] == 2:
                        poly = arr
                
                if poly is not None:
                    # poly is (y, x) -> (poly[:, 1], poly[:, 0]) for (x, y)
                    area_px = StatsCalculator._polygon_area(poly[:, 1], poly[:, 0])
            
            total_sd_px += area_px
            area_mm = area_px * ratio_factor
            
            bubble_list.append({
                'stt': i + 1,
                'cx': cx,
                'cy': cy,
                'area_px': area_px,
                'area_mm': area_mm
            })
            
        stats['list'] = bubble_list
        stats['area_px'] = f"{total_sd_px:.0f}"
        
        if ratio_factor > 0:
            total_sd_mm = total_sd_px * ratio_factor
            stats['area_mm'] = f"{total_sd_mm:.2f}"
            sd_r_mm = (total_sd_mm / (img_area_px * ratio_factor)) * 100
            stats['ratio'] = f"{sd_r_mm:.2f} %"
            
        return stats

    @staticmethod
    def _polygon_area(x, y):
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
