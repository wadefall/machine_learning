from returing.nn.module.module import Module

from returing.nn.function.base.reshape import Reshape
from returing.nn.function.base.repeat import Repeat
from returing.nn.function.base.batch_matmul import BatchMatMul
from returing.nn.function.base.get_sub_tensor import GetSubTensor
from returing.nn.function.base.concat import Concat
from returing.nn.function.base.transpose import Transpose
from returing.nn.function.base.sum_fn import BatchSum
from returing.nn.function.base.add_fn import BatchAdd

from returing.nn.function.conv.padding2d import Padding2D


class Conv2DCell(Module):

    def __init__(self, **kwargs):
        super(Conv2DCell, self).__init__()

        self.n_input_channel = kwargs['n_input_channel']
        self.input_width = kwargs['input_width']
        self.input_height = kwargs['input_height']
        self.kernel_size = kwargs['kernel_size']
        self.stride = kwargs['stride']
        self.padding = kwargs['padding']
        self.n_output_channel = kwargs['n_output_channel']
        self.is_bias = kwargs['is_bias']

    def forward(self, inputs):
        X, W, bias = inputs

        (self.n_samples, n_input_channel, input_width, input_height) = X.shape()

        self.output_width = int((input_width - self.kernel_size + 2 * self.padding)
                                / self.stride + 1)
        self.output_height = int((input_height - self.kernel_size + 2 * self.padding)
                                 / self.stride + 1)

        self.output_shape = (self.n_samples,
                             self.n_output_channel,
                             self.output_width,
                             self.output_height)

        # X: [n_samples, n_in_ch, in_w, in_h]
        # padding_X: [n_samples, n_in_ch, in_w+2p, in_h+2p]
        padding_X, = Padding2D(padding=self.padding)(X)

        #y_pred = Tensor()

        pred_tensor_list = []

        for oC_idx in range(self.n_output_channel):
            # W: [n_out_ch, n_in_ch, K, K]
            # W_oC: [n_in_ch, K, K]
            coord_tuple = ((oC_idx, oC_idx+1),
                           (0, self.n_input_channel),
                           (0, self.kernel_size),
                           (0, self.kernel_size))
            W_oC, = GetSubTensor(coord_tuple=coord_tuple)(W)

            for w_idx in range(self.output_width):
                for h_idx in range(self.output_height):

                    # X:[n_samples, n_in_ch, in_w+2p, in_h+2p]
                    coord_tuple = ((0, self.n_samples),
                                   (0, self.n_input_channel),
                                   (w_idx*self.stride, w_idx*self.stride + self.kernel_size),
                                   (h_idx*self.stride, h_idx*self.stride + self.kernel_size))

                    # sub_X: [n_samples, n_in_ch, K, K]
                    sub_X, = GetSubTensor(coord_tuple=coord_tuple)(padding_X, )

                    # sub_X: [n_samples, n_in_ch, K, K]
                    sub_X, = BatchMatMul()(sub_X, W_oC)

                    # x: [n_samples, ]
                    x, = BatchSum()(sub_X)

                    pred_tensor_list.append(x)

        # From tuple of tensor to `One` tensor
        # Two dims, [n_out_ch * out_w * out_h, n_samples]
        y_pred, = Concat()(*tuple(pred_tensor_list))

        target_shape = (self.n_output_channel,
                        self.output_width,
                        self.output_height,
                        self.n_samples)
        y_pred, = Reshape(target_shape=target_shape)(y_pred)

        # Raw: [n_out_ch, out_w, out_h, n_samples]
        # Target: [n_samples, n_out_ch, out_w, out_h]
        y_pred, = Transpose(axes=(3, 0, 1, 2))(y_pred)

        if self.is_bias:
            # bias --> [n_out_ch * out_w * out_h, ]
            repeat_times = self.output_width * self.output_height
            bias, = Repeat(repeat_times=repeat_times)(bias)

            # bias --> [n_out_ch, out_w, out_h]
            target_shape = (self.n_output_channel,
                            self.output_width,
                            self.output_height)
            bias, = Reshape(target_shape=target_shape)(bias)

            # y_pred: [n_samples, n_out_ch, out_w, out_h]
            # bias: [n_out_ch, out_w, out_h]
            y_pred, = BatchAdd()(y_pred, bias)

        return y_pred,