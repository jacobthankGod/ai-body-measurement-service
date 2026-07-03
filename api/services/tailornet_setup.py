"""TailorNet path configuration — replaces global_var.py for deployment."""
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Base data directory for TailorNet assets
TAILORNET_DATA_DIR = os.path.join(ROOT_DIR, 'tailornet_data')
os.makedirs(TAILORNET_DATA_DIR, exist_ok=True)

# SMPL model files — download from SMPL website / TailorNet dataset
SMPL_PATH_NEUTRAL = os.path.join(TAILORNET_DATA_DIR, 'smpl', 'SMPL_python_v.1.1.0', 'smpl', 'models', 'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl')
SMPL_PATH_MALE = os.path.join(TAILORNET_DATA_DIR, 'smpl', 'SMPL_python_v.1.1.0', 'smpl', 'models', 'basicmodel_m_lbs_10_207_0_v1.1.0.pkl')
SMPL_PATH_FEMALE = os.path.join(TAILORNET_DATA_DIR, 'smpl', 'SMPL_python_v.1.1.0', 'smpl', 'models', 'basicmodel_f_lbs_10_207_0_v1.1.0.pkl')

# Model weights root — each garment has a subfolder like t-shirt_male_weights/
MODEL_WEIGHTS_PATH = os.path.join(TAILORNET_DATA_DIR, 'model_weights')

# Dataset files needed for inference
GAR_INFO_FILE = 'garment_class_info.pkl'
POSE_SPLIT_FILE = 'split_static_pose_shape.npz'

# SMPL joint indices affecting each garment
VALID_THETA = {
    't-shirt': [0, 1, 2, 3, 6, 9, 12, 13, 14, 16, 17, 18, 19],
    'old-t-shirt': [0, 1, 2, 3, 6, 9, 12, 13, 14, 16, 17, 18, 19],
    'shirt': [0, 1, 2, 3, 6, 9, 12, 13, 14, 16, 17, 18, 19, 20, 21],
    'pant': [0, 1, 2, 4, 5, 7, 8],
    'short-pant': [0, 1, 2, 4, 5],
    'skirt': [0, 1, 2, 4, 5],
}

AVAILABLE_GARMENTS = list(VALID_THETA.keys())
GENDERS = ['neutral', 'male', 'female']
