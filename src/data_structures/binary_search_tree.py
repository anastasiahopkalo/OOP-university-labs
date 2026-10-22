from src.core.data_structure import DataStructure
from typing import TypeVar, List, Optional

T = TypeVar('T')


class BinarySearchTree(DataStructure[T]):
    class Node:
        def __init__(self, data):
            self.data = data
            self.left = None
            self.right = None

    def __init__(self):
        super().__init__("BinarySearchTree")
        self._root = None

    @property
    def root(self) -> Optional["BinarySearchTree.Node"]:
        return self._root

    # position ігнорується: місце вузла визначається його значенням
    def insert(self, data: T, position: int = None):
        if self._root is None:
            self._root = self.Node(data)
            self._size += 1
            return
        current = self._root
        while True:
            if data < current.data:
                if current.left is None:
                    current.left = self.Node(data)
                    break
                current = current.left
            elif data > current.data:
                if current.right is None:
                    current.right = self.Node(data)
                    break
                current = current.right
            else:
                return  # дублікати не зберігаються
        self._size += 1

    def delete(self, position: int) -> T:
        """Видаляє елемент з індексом position у відсортованому (in-order) порядку."""
        values = self.inorder()
        if not 0 <= position < len(values):
            return None
        value = values[position]
        self.remove(value)
        return value

    def remove(self, value: T) -> bool:
        parent = None
        current = self._root
        while current and current.data != value:
            parent = current
            current = current.left if value < current.data else current.right
        if current is None:
            return False

        if current.left and current.right:
            # Два нащадки: замінюємо найменшим значенням правого піддерева
            succ_parent = current
            succ = current.right
            while succ.left:
                succ_parent = succ
                succ = succ.left
            current.data = succ.data
            parent, current = succ_parent, succ

        child = current.left or current.right
        if parent is None:
            self._root = child
        elif parent.left is current:
            parent.left = child
        else:
            parent.right = child
        self._size -= 1
        return True

    def find(self, target: T) -> int:
        """Повертає глибину вузла (0 - корінь) або -1, якщо його немає."""
        current = self._root
        depth = 0
        while current:
            if target == current.data:
                return depth
            current = current.left if target < current.data else current.right
            depth += 1
        return -1

    def contains(self, target: T) -> bool:
        return self.find(target) != -1

    def get_all(self) -> List[T]:
        return self.inorder()

    def height(self) -> int:
        def _height(node):
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))
        return _height(self._root)

    def min(self) -> Optional[T]:
        node = self._root
        while node and node.left:
            node = node.left
        return node.data if node else None

    def max(self) -> Optional[T]:
        node = self._root
        while node and node.right:
            node = node.right
        return node.data if node else None

    def inorder(self) -> List[T]:
        result = []

        def _walk(node):
            if node:
                _walk(node.left)
                result.append(node.data)
                _walk(node.right)
        _walk(self._root)
        return result

    def preorder(self) -> List[T]:
        result = []

        def _walk(node):
            if node:
                result.append(node.data)
                _walk(node.left)
                _walk(node.right)
        _walk(self._root)
        return result

    def postorder(self) -> List[T]:
        result = []

        def _walk(node):
            if node:
                _walk(node.left)
                _walk(node.right)
                result.append(node.data)
        _walk(self._root)
        return result

    def level_order(self) -> List[T]:
        result = []
        level = [self._root] if self._root else []
        while level:
            next_level = []
            for node in level:
                result.append(node.data)
                next_level.extend(n for n in (node.left, node.right) if n)
            level = next_level
        return result
