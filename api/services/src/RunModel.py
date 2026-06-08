""" Evaluates a trained model using placeholders. """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
from os.path import exists
import os
import tf_slim as slim
from pathlib import Path

from .tf_smpl import projection as proj_util
from .tf_smpl.batch_smpl import SMPL
from .models import get_encoder_fn_separate
from . import resnet_v2

class RunModel(object):
    def __init__(self, sess=None):
        # Physical path resolution for Cloud Persistence
        root = Path(__file__).resolve().parent.parent.parent.parent
        self.load_path = str(root / 'models' / 'model.ckpt-667589')
        self.smpl_model_path = str(root / 'models' / 'neutral_smpl_with_cocoplus_reg.pkl')

        self.batch_size = 1
        self.img_size = 224
        self.data_format = 'NHMC'

        input_size = (self.batch_size, self.img_size, self.img_size, 3)
        self.images_pl = tf.placeholder(tf.float32, shape=input_size)

        self.num_stage = 3
        self.model_type = 'resnet_fc3_dropout'
        self.joint_type = 'cocoplus'
        self.num_cam = 3
        self.proj_fn = proj_util.batch_orth_proj_idrot
        self.num_theta = 72
        self.total_params = self.num_cam + self.num_theta + 10

        self.smpl = SMPL(self.smpl_model_path, joint_type=self.joint_type)
        self.build_test_model_ief()

        if sess is None:
            config = tf.ConfigProto()
            config.gpu_options.allow_growth = True

            # KORRA CLOUD HARDENING: CPU & Memory Throttling for Render 512MB
            # Limit parallelism to prevent starving the FastAPI event loop
            config.intra_op_parallelism_threads = 1
            config.inter_op_parallelism_threads = 1

            # Limit memory usage for Render tiers
            config.gpu_options.per_process_gpu_memory_fraction = 0.2

            self.sess = tf.Session(config=config)
        else:
            self.sess = sess
        
        self.saver = tf.train.Saver()

    def build_test_model_ief(self):
        self.mean_var = tf.Variable(tf.zeros((1, self.total_params)), name="mean_param", dtype=tf.float32)
        img_enc_fn, threed_enc_fn = get_encoder_fn_separate(self.model_type)
        self.img_feat, self.E_var = img_enc_fn(self.images_pl, is_training=False, reuse=False)
        
        self.all_verts = []
        self.all_kps = []
        self.all_cams = []
        self.all_Js = []
        self.final_thetas = []
        theta_prev = tf.tile(self.mean_var, [self.batch_size, 1])

        for i in range(self.num_stage):
            state = tf.concat([self.img_feat, theta_prev], 1)
            delta_theta, _ = threed_enc_fn(state, num_output=self.total_params, is_training=False, reuse=bool(i > 0))
            theta_here = theta_prev + delta_theta
            cams = theta_here[:, :self.num_cam]
            poses = theta_here[:, self.num_cam:(self.num_cam + self.num_theta)]
            shapes = theta_here[:, (self.num_cam + self.num_theta):]
            verts, Js, _ = self.smpl(shapes, poses, get_skin=True)
            pred_kp = self.proj_fn(Js, cams, name='proj_2d_stage%d' % i)
            self.all_verts.append(verts)
            self.all_kps.append(pred_kp)
            self.all_cams.append(cams)
            self.all_Js.append(Js)
            self.final_thetas.append(theta_here)
            theta_prev = theta_here

    def prepare(self):
        if exists(self.load_path + '.index'):
            print('Restoring checkpoint %s..' % self.load_path)
            self.saver.restore(self.sess, self.load_path)
        else:
            raise FileNotFoundError(f"AI weights not found at {self.load_path}")
            
    def predict_dict(self, images):
        feed_dict = { self.images_pl: images }
        fetch_dict = {
            'joints': self.all_kps[-1],
            'verts': self.all_verts[-1],
            'cams': self.all_cams[-1],
            'joints3d': self.all_Js[-1],
            'theta': self.final_thetas[-1],
        }
        results = self.sess.run(fetch_dict, feed_dict)
        return results
