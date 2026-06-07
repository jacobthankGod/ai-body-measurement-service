# Fixed ResNet V2 for KORRA Infrastructure
import tensorflow as tf
from . import resnet_utils
import tf_slim as slim

resnet_arg_scope = resnet_utils.resnet_arg_scope

@slim.add_arg_scope
def resnet_v2(inputs,
              blocks,
              num_classes=None,
              is_training=True,
              global_pool=True,
              output_stride=None,
              include_root_block=True,
              spatial_squeeze=True,
              reuse=None,
              scope=None):
  with tf.variable_scope(scope, 'resnet_v2', [inputs], reuse=reuse) as sc:
    end_points_collection = sc.original_name_scope + '_end_points'
    with slim.arg_scope([slim.conv2d, slim.stack, resnet_utils.stack_blocks_dense],
                        outputs_collections=end_points_collection):
      net = inputs
      if include_root_block:
        if output_stride is not None:
          if output_stride % 4 != 0:
            raise ValueError('The output_stride must be a multiple of 4.')
          output_stride /= 4
        with slim.arg_scope([slim.conv2d], activation_fn=None, normalizer_fn=None):
          net = resnet_utils.conv2d_same(net, 64, 7, stride=2, scope='conv1')
        net = slim.max_pool2d(net, [3, 3], stride=2, scope='pool1')

      net = resnet_utils.stack_blocks_dense(net, blocks, output_stride)
      net = slim.batch_norm(net, activation_fn=tf.nn.relu, scope='postnorm')

      if global_pool:
        net = tf.reduce_mean(net, [1, 2], name='pool5', keep_dims=True)
      if num_classes is not None:
        net = slim.conv2d(net, num_classes, [1, 1], activation_fn=None,
                          normalizer_fn=None, scope='logits')
        if spatial_squeeze:
          net = tf.squeeze(net, [1, 2], name='SpatialSqueeze')

      end_points = slim.utils.convert_collection_to_dict(end_points_collection)
      if num_classes is not None:
        end_points['predictions'] = slim.softmax(net, scope='predictions')
      return net, end_points

def resnet_v2_50(inputs,
                 num_classes=None,
                 is_training=True,
                 global_pool=True,
                 output_stride=None,
                 spatial_squeeze=True,
                 reuse=None,
                 scope='resnet_v2_50'):
  blocks = [
      resnet_utils.Block('block1', resnet_utils.bottleneck, [{'depth': 256, 'depth_bottleneck': 64, 'stride': 1}] * 2 + [{'depth': 256, 'depth_bottleneck': 64, 'stride': 2}]),
      resnet_utils.Block('block2', resnet_utils.bottleneck, [{'depth': 512, 'depth_bottleneck': 128, 'stride': 1}] * 3 + [{'depth': 512, 'depth_bottleneck': 128, 'stride': 2}]),
      resnet_utils.Block('block3', resnet_utils.bottleneck, [{'depth': 1024, 'depth_bottleneck': 256, 'stride': 1}] * 5 + [{'depth': 1024, 'depth_bottleneck': 256, 'stride': 2}]),
      resnet_utils.Block('block4', resnet_utils.bottleneck, [{'depth': 2048, 'depth_bottleneck': 512, 'stride': 1}] * 3)
  ]
  return resnet_v2(inputs, blocks, num_classes, is_training=is_training,
                   global_pool=global_pool, output_stride=output_stride,
                   include_root_block=True, spatial_squeeze=spatial_squeeze,
                   reuse=reuse, scope=scope)
