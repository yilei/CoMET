#!/usr/bin/env python
# coding=utf-8
"""
    CoMET - Convolutional Motif Extraction Tool
    -------------------------------------------
    CoMET is an automated tool for the discovery of protein motifs from arbitrarily
    large protein sequence datasets.

    (c) 2015-2017 Massachusetts Institute of Technology

    For more information contact:
    karydis [at] mit.edu
"""
import sys
import time

import keras.backend as K
import numpy as np
from absl import flags
from keras.utils.np_utils import to_categorical

import nets
from evolutron.motifs import motif_extraction
from evolutron.templates import callback_templates as cb
from evolutron.tools import Handle, load_dataset

seed = 7
np.random.seed(seed)

flags.DEFINE_string("infile", '', 'The protein dataset file to be trained on.')
flags.DEFINE_string("key", 'fam', 'The key to use for codes.')
flags.DEFINE_boolean("no_pad", False, 'Toggle to disable padding protein sequences. Batch size will auto-change to 1.')
flags.DEFINE_enum("mode", 'unsupervised', ['family', 'unsupervised'], 'The mode to train CoMET.')
flags.DEFINE_integer("epochs", 50, 'The number of training epochs to perform.', lower_bound=1)
flags.DEFINE_integer("batch_size", 50, 'The size of the mini-batch.', lower_bound=1)
flags.DEFINE_float("validation_split", 0.2, "The fraction of data to use for cross-validation.", lower_bound=0.0,
                   upper_bound=1.0)

flags.DEFINE_string("model", '', 'Continue training the given model. Other architecture options are unused.')

flags.DEFINE_boolean("motifs", True, 'Toggle to enable/disable motif extraction.')

flags.DEFINE_string("data_dir", '', 'The directory to store CoMET output data.')

FLAGS = flags.FLAGS

try:
    FLAGS(sys.argv)
except flags.Error as e:
    print(e)
    print(FLAGS)
    sys.exit(1)


def family(dataset, handle):
    # TODO: be able to submit train and test files separately
    # Find input shape
    x_data, y_data = dataset
    if type(x_data) == np.ndarray:
        input_shape = x_data[0].shape
    elif type(x_data) == list:
        input_shape = (None, x_data[0].shape[1])
    else:
        raise TypeError('Something went wrong with the dataset type')

    y_data = to_categorical(y_data)

    output_dim = y_data.shape[1]

    if FLAGS.model:
        conv_net = nets.build_cofam_model(saved_model=FLAGS.model)
        print('Loaded model')
    else:
        print('Building model ...')
        conv_net = nets.build_cofam_model(input_shape,
                                          output_dim)

    callbacks = cb.standard(patience=20, reduce_factor=.05)

    print('Started training at {}'.format(time.asctime()))
    conv_net.fit(x_data, y_data,
                 epochs=FLAGS.epochs,
                 batch_size=FLAGS.batch_size,
                 validation_split=FLAGS.validation_split,
                 callbacks=callbacks)

    handle.model = conv_net.name
    conv_net.save_train_history(handle, data_dir=FLAGS.data_dir)
    conv_net.save(handle, data_dir=FLAGS.data_dir)

    # Extract the motifs from the convolutional layers
    if FLAGS.motifs:
        for depth, conv_layer in enumerate(conv_net.get_conv_layers()):
            conv_scores = conv_layer.output
            # Compile function that spits out the outputs of the correct convolutional layer
            boolean_mask = K.any(K.not_equal(conv_net.input, 0.0), axis=-1, keepdims=True)
            conv_scores = conv_scores * K.cast(boolean_mask, K.floatx())

            custom_fun = K.function([conv_net.input], [conv_scores])
            # Start visualizations
            motif_extraction(custom_fun, x_data, conv_layer.filters,
                             conv_layer.kernel_size[0], handle, depth, data_dir=FLAGS.data_dir)


def unsupervised(dataset, handle):
    x_data = dataset[0]
    # Find input shape
    if type(x_data) == np.ndarray:
        input_shape = x_data[0].shape
    elif type(x_data) == list:
        input_shape = (None, x_data[0].shape[1])
    else:
        raise TypeError('Something went wrong with the dataset type')

    if FLAGS.model:
        conv_net = nets.build_coder_model(saved_model=FLAGS.model)
        print('Loaded model')
    else:
        print('Building model ...')
        conv_net = nets.build_coder_model(input_shape)

    handle.model = conv_net.name

    conv_net.display_network_info()

    callbacks = cb.standard(patience=20, reduce_factor=.05)

    print('Started training at {}'.format(time.asctime()))

    conv_net.fit(x_data, x_data,
                 epochs=FLAGS.epochs,
                 batch_size=FLAGS.batch_size,
                 validation_split=FLAGS.validation_split,
                 callbacks=callbacks)

    conv_net.save_train_history(handle, data_dir=FLAGS.data_dir)
    conv_net.save(handle, data_dir=FLAGS.data_dir)

    # Extract the motifs from the convolutional layers
    if FLAGS.motifs:
        for depth, conv_layer in enumerate(conv_net.get_conv_layers()):
            conv_scores = conv_layer.output
            # Compile function that spits out the outputs of the correct convolutional layer
            boolean_mask = K.any(K.not_equal(conv_net.input, 0.0), axis=-1, keepdims=True)
            conv_scores = conv_scores * K.cast(boolean_mask, K.floatx())

            custom_fun = K.function([conv_net.input], [conv_scores])
            # Start visualizations
            motif_extraction(custom_fun, x_data, conv_layer.filters,
                             conv_layer.kernel_size[0], handle, depth, data_dir=FLAGS.data_dir)


def main():
    if FLAGS.no_pad:
        FLAGS.batch_size = 1

    if FLAGS.model:
        handle = Handle.from_filename(FLAGS.model)
        assert handle.ftype == 'model'
        assert handle.model in ['DeepCoDER', 'DeepCoFAM'], 'The model file provided is for another program.'
    else:
        handle = Handle(**FLAGS.flag_values_dict())

    # Load the dataset
    print("Loading data...")
    dataset_options = {'padded': not FLAGS.no_pad, 'infile': FLAGS.infile}

    if FLAGS.mode == 'unsupervised' or handle.model == 'DeepCoDER':
        dataset = load_dataset(**dataset_options)
        unsupervised(dataset, handle)
    elif FLAGS.mode == 'family' or handle.model == 'DeepCoFAM':
        dataset = load_dataset(**dataset_options, codes=True, code_key=FLAGS.key)
        family(dataset, handle)
    else:
        raise IOError('Invalid mode of operation.')


if __name__ == '__main__':
    main()
