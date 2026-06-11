$$
s_{dw} = \rho \cdot s_{dw} + (1 - \rho) \cdot dw^2
$$

$$
w = w - \frac{\alpha \cdot dw}{\sqrt{s_{dw}} + \epsilon}
$$

Where:

-  $w  is the parameter vector,
- **\( dw \)** is the gradient of the cost function with regards to the parameters at the current parameter value,
- **\( \alpha \)** is the learning rate,
- **\( s_{dw} \)** is the running average of the square of the gradients (initialized to 0), and
- **\( \rho \)** is the momentum parameter (a new hyperparameter, generally set to 0.9).

A higher **\( \rho \)** will result in a faster convergence. The small additive constant **\( \epsilon \)** ensures numerical stability by avoiding division by zero.