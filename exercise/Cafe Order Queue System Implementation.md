## Cafe Order Queue System Implementation

It's time to demonstrate what you've learned about queues in C++! Your mission is to construct a queue system for a bustling cafe. Remember, orders are processed in a specific sequence. Begin by defining a class to manage orders, ensuring that you can add and serve them efficiently. The `serve_order` function should return `-1` when there are no more orders to serve, instead of throwing an exception. Your journey through queues begins now — implement this essential component of the cafe's infrastructure.

---

### Starter Code

```cpp
#ifndef SOLUTION_HPP_
#define SOLUTION_HPP_

#include <queue>
#include <iostream>

class CafeOrderQueue {
public:
    void add_order(int order_id);

    int serve_order();

private:
    std::queue<int> order_queue;
};

#endif  // SOLUTION_HPP_


#include "solution.hpp"

void CafeOrderQueue::add_order(int order_id) {
    // TODO: Add an order to the queue
}

int CafeOrderQueue::serve_order() {
    // TODO: Serve (remove) the first order in the queue; return -1 if there are no orders
    return 0; // Placeholder return
}

int main() {
    CafeOrderQueue cafeQueue;

    // Add some orders
    cafeQueue.add_order(101);
    cafeQueue.add_order(102);
    cafeQueue.add_order(103);

    // Serve orders
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;

    // Try to serve another order from an empty queue
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;

    return 0;
}
```

---

### Building the Solution

- **`add_order`:** a `std::queue<int>` appends new elements with `.push(order_id)`, placing the order at the back of the line.
- **`serve_order`:** a queue serves orders **FIFO** (first-in, first-out) — the front element is always served next.
  - First check `order_queue.empty()`. If the queue has no orders, return `-1` immediately instead of accessing `.front()` on an empty queue (which is undefined behavior).
  - Otherwise, read the front order with `.front()`, remove it with `.pop()`, and return the saved ID.

---

### Completed Code

```cpp
#ifndef SOLUTION_HPP_
#define SOLUTION_HPP_

#include <queue>
#include <iostream>

class CafeOrderQueue {
public:
    void add_order(int order_id);

    int serve_order();

private:
    std::queue<int> order_queue;
};

#endif  // SOLUTION_HPP_


#include "solution.hpp"

void CafeOrderQueue::add_order(int order_id) {
    order_queue.push(order_id);
}

int CafeOrderQueue::serve_order() {
    if (order_queue.empty()) {
        return -1;
    }
    int order_id = order_queue.front();
    order_queue.pop();
    return order_id;
}

int main() {
    CafeOrderQueue cafeQueue;

    // Add some orders
    cafeQueue.add_order(101);
    cafeQueue.add_order(102);
    cafeQueue.add_order(103);

    // Serve orders
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;

    // Try to serve another order from an empty queue
    std::cout << "Served Order ID: " << cafeQueue.serve_order() << std::endl;

    return 0;
}
```

---

### Output

```
Served Order ID: 101
Served Order ID: 102
Served Order ID: 103
Served Order ID: -1
```

---

### Output Trace

| Call | `order_queue` before | Action | Returned |
|------|------------------------|--------|-----------|
| `add_order(101)` | `{}` | push `101` | — |
| `add_order(102)` | `{101}` | push `102` | — |
| `add_order(103)` | `{101, 102}` | push `103` | — |
| `serve_order()` | `{101, 102, 103}` | pop front | `101` |
| `serve_order()` | `{102, 103}` | pop front | `102` |
| `serve_order()` | `{103}` | pop front | `103` |
| `serve_order()` | `{}` (empty) | no pop | `-1` |

> **Key takeaway:** `std::queue` only exposes `.front()`, `.push()`, `.pop()`, and `.empty()` — there's no `[]` indexing like a vector or array. Always check `.empty()` before calling `.front()`/`.pop()`; calling either on an empty queue is undefined behavior rather than a thrown exception, which is exactly why `serve_order` must guard against it explicitly and return a sentinel value like `-1`.
