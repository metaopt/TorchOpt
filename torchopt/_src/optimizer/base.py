# Copyright 2022 MetaOPT Team. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from typing import Iterable

import jax
import torch

from torchopt._src.base import GradientTransformation
from torchopt._src.update import apply_updates


class Optimizer(object):
    """A high-level base class that has the similar with `torch.optim.Optimizer`."""

    def __init__(self, params: Iterable, impl: GradientTransformation):
        """The `init` function.
        Args:
            params (iterable):
                An iterable of `torch.Tensor`s. Specifies what Tensors should be
                optimized.
            impl (GradientTransformation):
                A low level optimizer function, it could be a optimizer function
                provided by `alias.py` or a customized `chain` provided by
                `combine.py`.
                Note that use `MetaOptimizer(sgd())` or `MetaOptimizer(chain(sgd()))`
                is equivalent to `SGD`.
        """

        if not isinstance(params, list):
            params = list(params)
        self.impl = impl
        self.param_groups = []  # type: ignore
        self.param_tree_groups = []  # type: ignore
        self.state_groups = []  # type: ignore
        self.add_param_group(params)

    def zero_grad(self, set_to_none: bool = False):
        """Sets the gradients of all optimized `torch.Tensor`s to zero.

        The behavior is similar to `torch.optim.Optimizer.zero_grad`.

        Args:
            set_to_none (bool):
                Instead of setting to zero, set the grads to None.
        """

        for group in self.param_groups:
            if set_to_none:

                def f(p):
                    p.grad = None
                    return None

            else:

                def f(p):
                    if p.grad is None:
                        return None
                    if p.grad.grad_fn is not None:
                        p.grad.detach_()
                    else:
                        p.grad.requires_grad_(False)
                    p.grad.zero_()
                    return None

            jax.tree_map(f, group)

    def state_dict(self):
        """Returns the state of the optimizer."""

        return self.state_groups

    def load_state_dict(self, state_dict):
        """Loads the optimizer state.

        Args:
            state_dict (dict):
                Optimizer state. Should be an object returned from a call to :meth:`state_dict`.
        """

        self.state_groups = state_dict

    def step(self, closure=None):
        """Performs a single optimization step (parameter update).

        The behavior is similar to `torch.optim.Optimizer.step`.

        Args:
            closure (callable, optional):
                A closure that reevaluates the model and returns the loss.
        """

        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        def f(p):
            return p.grad

        for param, state in zip(self.param_groups, self.state_groups):
            grad = jax.tree_map(f, param)
            updates, _ = self.impl.update(grad, state)
            apply_updates(param, updates)

        return loss

    def add_param_group(self, params):
        params, tree = jax.tree_flatten(params)
        params = tuple(params)
        self.param_groups.append(params)
        self.param_tree_groups.append(tree)
        self.state_groups.append(self.impl.init(params))
