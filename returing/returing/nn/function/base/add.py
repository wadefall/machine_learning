from returing.nn.function.function import Function
from returing.nn.tensor.tensor import Tensor
import numpy as np


class Add(Function):

    def __init__(self):
        super(Add, self).__init__()

    def forward(self, inputs):

        a, b = inputs

        c_data = a.data + b.data
        c = Tensor(c_data)

        self.saved_context = a.data.shape, b.data.shape

        return c,

    def backward(self, grads):
        a_grad_shape, b_grad_shape = self.saved_context
        self.saved_context = None

        a_grad_data = np.ones(a_grad_shape)
        b_grad_data = np.ones(b_grad_shape)

        c_grad = grads
        if isinstance(c_grad, Tensor):
            c_grad_data = c_grad.data
            a_grad_data *= c_grad_data
            b_grad_data *= c_grad_data

        a_grad = Tensor(a_grad_data)
        b_grad = Tensor(b_grad_data)

        return a_grad, b_grad










