import numpy as np
import tensorflow as tf
import time
import datetime
from datetime import timedelta
import logging
from . import config
import random
from tensorflow.python.framework import function

def gen_data(n=config.BATCH_SIZE, block_len=config.BLOCK_LEN):
    return np.random.randint(0, 2, size=(n, block_len))*2-1

def gen_ham_data(n=config.BATCH_SIZE, block_len=config.BLOCK_LEN):
    return np.random.randint(0, 2, size=(n, block_len))

def init_weights(name, shape):
    return tf.get_variable(name, shape=shape,
            initializer=tf.contrib.layers.xavier_initializer())

@function.Defun()
def binarize_grad(x, dy):
    return dy

@function.Defun(grad_func=binarize_grad)
def binarize(x):
    return tf.sign(x)

def binarize_forward(x):
    return tf.sign(x)

def binarize_forward_0(x):
    return tf.sign(x)*2-1

@function.Defun()
def bsc_grad(x, dy):
    return dy

@function.Defun(grad_func=bsc_grad)
def bsc(x):
    msg_len = config.MSG_LEN 
    batch_size = config.BATCH_SIZE
    num_change = np.random.randint(config.NUM_CHANGE)
    if num_change == 0:
      return tf.identity(x)

    indices = np.squeeze(np.random.randint(msg_len, size=[num_change, batch_size]))
    update = np.ones((batch_size, msg_len))
    update[range(batch_size), indices] = -1
    return tf.multiply(x, tf.convert_to_tensor(update, dtype=tf.float32))

def bsc_p(bit, p=config.ERR_PROB):
    return bit if np.random.random() >= p else tf.negative(bit)

def bsc_forward(x, msg_len, batch_size, n_change):
  if n_change == 0:
      return tf.identity(x)
      
  num_change = n_change #np.random.randint(n_change)
  indices = np.squeeze(np.random.randint(msg_len, size=[num_change, batch_size]))
  update = np.ones((batch_size, msg_len))
  update[range(batch_size), indices] = -1
  return tf.multiply(x, tf.convert_to_tensor(update, dtype=tf.float32))


class TrainFormatter(logging.Formatter):
    def __init__(self):
        self.iter_time = time.time()
        self.epoch_time = time.time()
        self.epoch = 0
        super(TrainFormatter, self).__init__('%(asctime)s/%(name)s: %(levelname)s - %(message)s')

    def format(self, record):
        try:
            return super(TrainFormatter, self).format(record)
        except:
            return self.train_format(record, record.msg, record.args)

    def train_format(self, record, iteration, args):
        iter_elapsed = timedelta(seconds=(time.time() - self.iter_time)).total_seconds()
        epoch_elapsed = timedelta(seconds=(time.time() - self.epoch_time)).total_seconds()

        if len(args) > 2:
            self.epoch_time = time.time()
            self.epoch = args[2]
            epoch = True
        else:
            epoch = False
        err = args[0]
        bin_err = args[1]

        self.iter_time = time.time()

        if abs(iter_elapsed - epoch_elapsed) < 0.001:
            iter_elapsed = epoch_elapsed / 2000

        message = '[epoch:' + str(self.epoch) + '/step:' + str(iteration) + ']'
        message += 'Epoch Error:' if epoch else ' Error:'
        message += str(err)
        message += ' Bin:' + str(bin_err)
        message += ' (Step: ' + '{0:.3f}'.format(iter_elapsed) + ' Epoch: ' + str(epoch_elapsed)[:6] + ')'

        record.msg = message
        record.args = ()

        return super(TrainFormatter, self).format(record)
