import os
import numpy as np
import tensorflow as tf
from PIL import Image
from stardist.models import StarDist2D
from csbdeep.utils import normalize
from app.utils.starbub import HiddenReco

class ModelService:
    def __init__(self):
        self.modelSD = None
        self.modelRDC = None
        self.models_loaded = False
        
        # GPU Config
        try:
             physical_devices = tf.config.list_physical_devices('GPU')
             for device in physical_devices:
                 tf.config.experimental.set_memory_growth(device, True)
        except:
             os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

    def load_models(self, sd_path, rdc_path):
        """
        Loads StarDist and RDC models.
        """
        try:
            print(f"Loading SD: {sd_path}")
            print(f"Loading RDC: {rdc_path}")
            
            if not os.path.exists(sd_path):
                 return False, f"StarDist path not found: {sd_path}"
            if not os.path.exists(rdc_path):
                 return False, f"RDC path not found: {rdc_path}"

            # Load StarDist
            if os.path.isdir(sd_path):
                sd_name = os.path.basename(sd_path)
                sd_basedir = os.path.dirname(sd_path)
                self.modelSD = StarDist2D(None, name=sd_name, basedir=sd_basedir)
            else:
                return False, "StarDist path must be a directory."
            
            # Load RDC
            self.modelRDC = tf.keras.models.load_model(rdc_path)
            
            self.models_loaded = True
            return True, "Models loaded successfully."
        except Exception as e:
            self.models_loaded = False
            return False, f"Error loading models: {str(e)}"

    def load_img(self, path):
        x = np.array(Image.open(path).convert('L'))
        return x

    def predict(self, img_path, metric):
        """
        Runs prediction on a single image.
        Returns:
             labels: StarDist label array
             details: StarDist details dict
             Bubbles: HiddenReco Bubbles object
             img_name: Basename of image without extension
        """
        if not self.models_loaded:
            raise Exception("Models not loaded")

        img_name = os.path.splitext(os.path.basename(img_path))[0]
        
        # Load & Predict
        x = self.load_img(img_path)
        X = normalize(x if x.ndim == 2 else x[..., 0], 1, 99.8, axis=(0, 1))
        
        labels, details = self.modelSD.predict_instances(X, verbose=False)
        Bubbles = HiddenReco(labels, metric, useRDC=True, model=self.modelRDC, boolPlot=False)
        
        return labels, details, Bubbles, img_name
