import os
import pickle
import datetime

import tensorflow as tf

from utils import ops
from utils import distances
from utils import losses
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error
from tensorflow.contrib.tensorboard.plugins import projector


class SiameseCNNLSTM(object):
    """
    A LSTM based deep Siamese network for text similarity.
    Uses an character embedding layer, followed by a biLSTM and Energy Loss 
    layer.
    """

    def __init__(self, train_options):
        self.args = train_options
        self.create_placeholders()
        self.create_scalars()
        self.create_experiment_dirs()
        self.load_train_options()
        self.save_train_options()

    def create_scalars(self):
        self.global_step = tf.Variable(0, name="global_step", trainable=False)
        self.dropout_keep_prob = self.args.get("dropout")

    def create_placeholders(self):
        self.input_s1 = tf.placeholder(tf.int32, [None,
                                                  self.args.get("sequence_length")],
                                       name="input_s1")
        self.input_s2 = tf.placeholder(tf.int32, [None,
                                                  self.args.get("sequence_length")],
                                       name="input_s2")
        self.input_sim = tf.placeholder(tf.float32, [None], name="input_sim")

    def create_optimizer(self):
        self.optimizer = ops.get_optimizer(self.args["optimizer"]) \
                                                (self.args["learning_rate"])

    def compute_gradients(self):
        self.grads_and_vars = self.optimizer.compute_gradients(self.loss)
        self.tr_op_set = self.optimizer.apply_gradients(self.grads_and_vars,
                                              global_step=self.global_step)

    def build_model(self, metadata_path=None, embedding_weights=None):

        with tf.name_scope("embedding"):
            self.embedding_weights, self.config = ops.embedding_layer(
                                            metadata_path, embedding_weights)
            self.embedded_s1 = tf.nn.embedding_lookup(self.embedding_weights,
                                                      self.input_s1)
            self.embedded_s2 = tf.nn.embedding_lookup(self.embedding_weights,
                                                      self.input_s2)

        with tf.name_scope("SIAMESE_CNN_LSTM"):
            self.s1_cnn_out = ops.multi_filter_conv_block(self.embedded_s1,
                                        self.args["n_filters"],
                                        dropout_keep_prob=self.args["dropout"])
            self.s1_lstm_out = ops.lstm_block(self.s1_cnn_out,
                                       self.args["hidden_units"],
                                       dropout=self.args["dropout"],
                                       layers=self.args["rnn_layers"],
                                       dynamic=False,
                                       bidirectional=self.args["bidirectional"])

            self.s2_cnn_out = ops.multi_filter_conv_block(self.embedded_s2,
                                          self.args["n_filters"], reuse=True,
                                          dropout_keep_prob=self.args["dropout"])
            self.s2_lstm_out = ops.lstm_block(self.s2_cnn_out,
                                       self.args["hidden_units"],
                                       dropout=self.args["dropout"],
                                       layers=self.args["rnn_layers"],
                                       dynamic=False, reuse=True,
                                       bidirectional=self.args["bidirectional"])
            self.distance = distances.exponential(self.s1_lstm_out,
                                                  self.s2_lstm_out)

        with tf.name_scope("loss"):
            self.loss = losses.mean_squared_error(self.input_sim, self.distance)

            if self.args["l2_reg_beta"] > 0.0:
                self.regularizer = ops.get_regularizer(self.args["l2_reg_beta"])
                self.loss = tf.reduce_mean(self.loss + self.regularizer)

        #### Evaluation Measures.
        with tf.name_scope("Pearson_correlation"):
            self.pco, self.pco_update = tf.contrib.metrics.streaming_pearson_correlation(
                    self.distance, self.input_sim, name="pearson")
        with tf.name_scope("MSE"):
            self.mse, self.mse_update = tf.metrics.mean_squared_error(
                    self.input_sim, self.distance,  name="mse")

    def create_experiment_dirs(self):
        self.exp_dir = os.path.join(self.args["data_dir"],
                               'experiments', self.args["experiment_name"])
        if not os.path.exists(self.exp_dir):
            os.makedirs(self.exp_dir)
        print("All experiment related files will be "
              "saved in {}\n".format(self.exp_dir))
        self.checkpoint_dir = os.path.join(self.exp_dir, "checkpoints")
        self.val_results_dir = os.path.join(self.exp_dir, "val_results")
        self.test_results_dir = os.path.join(self.exp_dir, "test_results")
        self.checkpoint_prefix = os.path.join(self.checkpoint_dir, "model")
        self.train_options_path = os.path.join(self.exp_dir,
                                               'train_options.pkl')
        self.dev_summary_dir = os.path.join(self.exp_dir, "summaries",
                                         "validation")

        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
        if not os.path.exists(self.val_results_dir):
            os.makedirs(self.val_results_dir)
        if not os.path.exists(self.test_results_dir):
            os.makedirs(self.test_results_dir)

    def create_histogram_summary(self):
        grad_summaries = []
        for g, v in self.grads_and_vars:
            if g is not None:
                grad_hist_summary = tf.summary.histogram(
                    "{}/grad/hist".format(v.name), g)
                grad_summaries.append(grad_hist_summary)

        self.grad_summaries_merged = tf.summary.merge(grad_summaries)
        print("defined gradient summaries")

    def create_scalar_summary(self, sess):
        # Summaries for loss and accuracy
        self.loss_summary = tf.summary.scalar("loss", self.loss)
        self.pearson_summary = tf.summary.scalar("pco", self.pco)
        self.mse_summary = tf.summary.scalar("mse", self.mse)

        # Train Summaries
        self.train_summary_op = tf.summary.merge([self.loss_summary,
                                                  self.pearson_summary,
                                                  self.mse_summary])

        self.train_summary_writer = tf.summary.FileWriter(self.checkpoint_dir,
                                                     sess.graph)
        projector.visualize_embeddings(self.train_summary_writer,
                                       self.config)

        # Dev summaries
        self.dev_summary_op = tf.summary.merge([self.loss_summary,
                                                self.pearson_summary,
                                                self.mse_summary])

        self.dev_summary_writer = tf.summary.FileWriter(self.dev_summary_dir,
                                                   sess.graph)

    def initialize_saver(self):
        self.saver = tf.train.Saver(tf.global_variables(),
                                    max_to_keep=self.args["max_checkpoints"])

    def initialize_variables(self, sess):
        sess.run(tf.global_variables_initializer())
        sess.run(tf.local_variables_initializer())
        print("initialized all variables")

    def save_graph(self):
        graph_def = tf.get_default_graph().as_graph_def()
        graphpb_txt = str(graph_def)
        with open(os.path.join(self.checkpoint_dir, "graphpb.txt"), 'w') as f:
            f.write(graphpb_txt)

    def save_train_options(self):
        pickle.dump(self.args, open(self.train_options_path, 'wb'))
        print('Saved Training options')

    def load_train_options(self):
        if os.path.exists(self.train_options_path):
            self.args = pickle.load(open(self.train_options_path, 'rb'))
            print('Loaded Training options')
        else:
            print('Could not find training options so using currently given '
                  'values.')

    def show_train_params(self):
        print("\nParameters:")
        for attr, value in sorted(self.args.items()):
            print("{}={}".format(attr.upper(), value))

    def load_saved_model(self, sess):
        print('Trying to resume training from a previous checkpoint' +
              str(tf.train.latest_checkpoint(self.checkpoint_dir)))
        if tf.train.latest_checkpoint(self.checkpoint_dir) is not None:
            self.saver.restore(sess, tf.train.latest_checkpoint(
                                                    self.checkpoint_dir))
            print('Successfully loaded model. Resuming training.')
        else:
            print('Could not load checkpoints.  Training a new model')

    def easy_setup(self, sess):
        print('Computing Gradients')
        self.compute_gradients()

        print('Defining Summaries with Embedding Visualizer')
        self.create_histogram_summary()
        self.create_scalar_summary(sess)

        print('Initializing Saver')
        self.initialize_saver()

        print('Initializing Variables')
        self.initialize_variables(sess)

        print('Saving Graph')
        self.save_graph()

        print('Loading Saved Model')
        self.load_saved_model(sess)

    def train_step(self, sess, s1_batch, s2_batch, sim_batch,
                   epochs_completed, verbose=True):
            """
            A single train step
            """
            feed_dict = {
                self.input_s1: s1_batch,
                self.input_s2: s2_batch,
                self.input_sim: sim_batch,
            }
            ops = [self.tr_op_set, self.global_step, self.loss, self.distance]
            if hasattr(self, 'train_summary_op'):
                ops.append(self.train_summary_op)
                _, step, loss, sim, summaries = sess.run(ops,
                    feed_dict)
                self.train_summary_writer.add_summary(summaries, step)
            else:
                _, step, loss, sim = sess.run(ops, feed_dict)

            pco = pearsonr(sim, sim_batch)
            mse = mean_squared_error(sim_batch, sim)

            if verbose:
                time_str = datetime.datetime.now().isoformat()
                print("Epoch: {}\tTRAIN {}: Current Step{}\tLoss{:g}\t"
                      "PCO:{}\tMSE={}".format(epochs_completed,
                        time_str, step, loss, pco, mse))
            return pco, mse, loss, step

    def evaluate_step(self, sess, s1_batch, s2_batch, sim_batch, verbose=True):
        """
        A single evaluation step
        """
        feed_dict = {
            self.input_s1: s1_batch,
            self.input_s2: s2_batch,
            self.input_sim: sim_batch
        }
        ops = [self.global_step, self.loss, self.distance, self.pco,
               self.pco_update, self.mse, self.mse_update]
        if hasattr(self, 'self.dev_summary_op'):
            ops.append(self.dev_summary_op)
            step, loss, sim, pco, _, mse, _, summaries = sess.run(ops,
                                                                  feed_dict)
            self.dev_summary_writer.add_summary(summaries, step)
        else:
            step, loss, sim, pco, _, mse, _ = sess.run(ops, feed_dict)

        time_str = datetime.datetime.now().isoformat()
        pco = pearsonr(sim, sim_batch)
        mse = mean_squared_error(sim_batch, sim)
        if verbose:
            print("EVAL{}:step{}\tloss{:g}\t pco:{}\tmse:{}".format(time_str,
                                                        step, loss, pco, mse))
        return loss, pco, mse, sim

