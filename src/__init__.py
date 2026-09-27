"""
CodeLearn Studio - Main package
Exports all main classes for easy access
"""

# Core classes
from src.core.algorithm import Algorithm, SortingAlgorithm, AlgorithmStep
from src.core.data_structure import DataStructure
from src.core.exercise import Exercise, ExerciseResult
from src.core.analytics import ProgressTracker

# Sorting algorithms
from src.algorithms.sorting.quick_sort import QuickSort
from src.algorithms.sorting.merge_sort import MergeSort
from src.algorithms.sorting.bubble_sort import BubbleSort
from src.algorithms.sorting.heap_sort import HeapSort
from src.algorithms.sorting.insertion_sort import InsertionSort

# Data structures
from src.data_structures.linked_list import LinkedList
from src.data_structures.dynamic_array import DynamicArray
from src.data_structures.stack import Stack
from src.data_structures.queue import Queue

all = [
    # Core
    'Algorithm',
    'SortingAlgorithm',
    'AlgorithmStep',
    'DataStructure',
    'Exercise',
    'ExerciseResult',
    'ProgressTracker',

    # Algorithms
    'QuickSort',
    'MergeSort',
    'BubbleSort',
    'HeapSort',
    'InsertionSort',

    # Data structures
    'LinkedList',
    'DynamicArray',
    'Stack',
    'Queue',
]

version = "1.0.0"
author = "Your Name"