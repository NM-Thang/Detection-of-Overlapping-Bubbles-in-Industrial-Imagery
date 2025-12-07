# Detection of Overlapping Bubbles in Industrial Imagery

This project investigates the application of **StarDist** for identifying overlapping objects in **industrial bubble images** and employing **Radial Distance Correction (RDC)** for shape reconstruction.

## Project Description

In industrial multiphase flow imaging, bubbles often overlap, making accurate segmentation and property analysis (size, volume) challenging. This research proposes a two-stage approach:
1.  **Detection & Segmentation:** Using the **StarDist** (Star-convex Object Detection) CNN model to detect and segment individual bubble instances, effectively handling dense and overlapping conditions.
2.  **Shape Reconstruction:** Applying the **Radial Distance Correction (RDC)** method to reconstruct the complete shapes of occluded bubbles based on their visible segments predicted by StarDist.

## Project Structure

### Core Notebooks
- **`startdist-data-preprocess.ipynb`**: **Step 1.** Preprocesses raw frame images (Flatfield correction, DoG, Lanczos upscaling) to prepare training data for StarDist.
- **`stardist-train.ipynb`**: **Step 2.** Trains the StarDist model to detect overlapping bubbles using the preprocessed data.
- **`rdc-data-gen.ipynb`**: **Step 3.** Generates **synthetic training data** for the RDC model.
  - Simulates overlapping bubble scenarios.
  - Converts ground truth masks to Radial Distance (RD) objects.
  - Output: `X_train.npy`, `Y_train.npy` (Inputs for RDC training).
- **`rdc-train.ipynb`**: **Step 4.** Trains the RDC Neural Network.
  - Input: Occluded radial distances.
  - Output: Corrected "ground truth" radial distances.
- **`prediction-demo.ipynb`**: **Step 5.** Interactive notebook demonstrating the full pipeline (StarDist prediction + RDC reconstruction) on sample images.

### Data
- **`data/`**: Directory containing industrial and synthetic datasets. (Excluded from version control).
- **`Examples/`**: Sample images for testing the demo scripts.
- **`Models/`**: Directory where trained StarDist and RDC models are saved.

## Prerequisites & Compatibility

*   **Python Version:** Python 3.7+
*   **Hardware:** CUDA-compatible GPU recommended for training and faster inference.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd CodeRepo
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Key libraries: `stardist`, `tensorflow`, `numpy`, `pandas`, `scikit-image`, `matplotlib`, `opencv-python`.*

## Usage Workflow

Follow these steps to reproduce the full pipeline:

### 1. Data Preprocessing
Run **`startdist-data-preprocess.ipynb`** to apply image enhancement techniques (Flatfield, DoG) to your raw dataset.

### 2. Train StarDist
Run **`stardist-train.ipynb`** to train the detection model on the preprocessed images.

### 3. Generate RDC Data
Run **`rdc-data-gen.ipynb`** to create a synthetic dataset of overlapping bubbles. This uses ground truth data to learn how to correct deformed shapes.
-   *Note: Output is configured to Millimeters (mm).*

### 4. Train RDC Model
Run **`rdc-train.ipynb`** to train the dense neural network using the synthetic data generated in step 3.

### 5. Inference & Demo
You can visualize results in two ways:
-   **Notebook:** Open **`prediction-demo.ipynb`** for a step-by-step walkthrough.
-   **Script:** Run `python demo.py` to launch an interactive viewer.
    -   **Controls:** Use `Next`/`Prev` buttons to toggle between detected bubbles. Click on a bubble to view its radial profile.

## Data Management

The `data/` folder contains extensive datasets (>150k files) and is excluded from this repository.
> **Note:** Please refer to the `Examples/` folder for sample data or generate your own using the provided notebooks.
