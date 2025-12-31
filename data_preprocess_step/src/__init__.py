# -*- coding: utf-8 -*-
"""
BRep 特征提取模块
基于 pythonocc-core 的 BRep 结构数据特征提取工具
"""

from .feature_extract import FeatureExtractor
from .graph import HeterogeneousGraph
__version__ = "1.0.0"
__author__ = "BRep Feature Extractor Team"

# 导出主要类
__all__ = ['FeatureExtractor', 'HeterogeneousGraph']