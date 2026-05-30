In Markdown cells of Jupyter Notebook, you can write mathematical formulas using LaTeX syntax inside dollar signs (`$`). Here’s how to do it:

### Inline Math
- Use single dollar signs `$` for inline formulas.
- Example: Write `$\sin(x)$` in the Markdown cell, and it will render as \( \sin(x) \).

### Display Math
- Use double dollar signs `$$` for formulas displayed on their own line.
- Example:
  ```markdown
  $$ \int_a^b f(x) \,dx $$
  ```
  will render as:
  \[
  \int_a^b f(x) \,dx
  \]

### Common Examples
Here are a few examples of mathematical formulas:
1. **Inline**: `$f(x) = ax^2 + bx + c$` renders as \( f(x) = ax^2 + bx + c \).
2. **Display**:
   ```markdown
   $$ E = mc^2 $$
   ```
   renders as:
   \[
   E = mc^2
   \]

### Additional Tips
- Use `\` to escape special characters (e.g., `\sin`, `\int`, `\frac`).
- Use `{}` to group terms (e.g., `x^{n+1}` for \( x^{n+1} \)).
- Use `\begin{align} ... \end{align}` for aligned equations.

### Example of a Full Markdown Cell:
```markdown
This is an inline formula: $\sin(x) + \cos(x)$.

And here is a displayed formula:

$$ f(x) = \frac{\sin(x)}{x} $$

Aligned equations:

$$
\begin{align}
a + b &= c \\
d - e &= f
\end{align}
$$
```

Try these in a Markdown cell, and run it to see the rendered formulas!