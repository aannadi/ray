from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.utils.annotations import PublicAPI
from ray.rllib.utils import try_import_tf
from ray.rllib.utils.annotations import override

tf = try_import_tf()


@PublicAPI
class TFModelV2(ModelV2):
    """TF version of ModelV2.

    Note that this class by itself is not a valid model unless you
    implement forward() in a subclass."""

    def __init__(self, obs_space, action_space, num_outputs, model_config,
                 name):
        """Initialize a TFModelV2.

        Here is an example implementation for a subclass
        ``MyModelClass(TFModelV2)``::

            def __init__(self, *args, **kwargs):
                super(MyModelClass, self).__init__(*args, **kwargs)
                input_layer = tf.keras.layers.Input(...)
                hidden_layer = tf.keras.layers.Dense(...)(input_layer)
                output_layer = tf.keras.layers.Dense(...)(hidden_layer)
                value_layer = tf.keras.layers.Dense(...)(hidden_layer)
                self.base_model = tf.keras.Model(
                    input_layer, [output_layer, value_layer])
                self.register_variables(self.base_model.variables)
        """

        ModelV2.__init__(
            self,
            obs_space,
            action_space,
            num_outputs,
            model_config,
            name,
            framework="tf")
        self.var_list = []
        if tf.executing_eagerly():
            self.graph = None
        else:
            self.graph = tf.get_default_graph()

    def context(self):
        """Returns a contextmanager for the current TF graph."""
        if self.graph:
            return self.graph.as_default()
        else:
            return ModelV2.context(self)

    def forward(self, input_dict, state, seq_lens):
        """Call the model with the given input tensors and state.

        Any complex observations (dicts, tuples, etc.) will be unpacked by
        __call__ before being passed to forward(). To access the flattened
        observation tensor, refer to input_dict["obs_flat"].

        This method can be called any number of times. In eager execution,
        each call to forward() will eagerly evaluate the model. In symbolic
        execution, each call to forward creates a computation graph that
        operates over the variables of this model (i.e., shares weights).

        Custom models should override this instead of __call__.

        Args:
            input_dict (dict): dictionary of input tensors, including "obs",
                "obs_flat", "prev_action", "prev_reward", "is_training"
            state (list): list of state tensors with sizes matching those
                returned by get_initial_state + the batch dimension
            seq_lens (Tensor): 1d tensor holding input sequence lengths

        Returns:
            (outputs, state): The model output tensor of size
                [BATCH, num_outputs]

        Examples:
            >>> def forward(self, input_dict, state, seq_lens):
            >>>     model_out, self._value_out = self.base_model(
            ...         input_dict["obs"])
            >>>     return model_out, state
        """
        raise NotImplementedError

    def update_ops(self):
        """Return the list of update ops for this model.

        For example, this should include any BatchNorm update ops."""
        return []

    def register_variables(self, variables):
        """Register the given list of variables with this model."""
        self.var_list.extend(variables)

    @override(ModelV2)
    def variables(self, as_dict=False):
        if as_dict:
            return {v.name: v for v in self.var_list}
        return list(self.var_list)

    @override(ModelV2)
    def trainable_variables(self, as_dict=False):
        if as_dict:
            return {
                k: v
                for k, v in self.variables(as_dict=True).items() if v.trainable
            }
        return [v for v in self.variables() if v.trainable]
