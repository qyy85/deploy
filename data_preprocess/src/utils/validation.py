"""
数据验证工具
用于验证提取的特征数据的正确性
"""
from typing import Dict, Any, List, Optional
import logging


class DataValidator:
    """数据验证器"""
    
    def __init__(self, strict_mode: bool = False):
        """初始化验证器
        
        Args:
            strict_mode: 严格模式，如果为True则抛出异常，否则只记录警告
        """
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)
    
    def validate_edge_data(self, edge_data: Dict[str, Any]) -> bool:
        """验证边数据
        
        Args:
            edge_data: 边数据字典
            
        Returns:
            验证是否通过
        """
        try:
            # 检查必需字段
            required_fields = ['id', 'type', 'features']
            for field in required_fields:
                if field not in edge_data:
                    self._handle_error(f"Missing required field in edge data: {field}")
                    return False
            
            # 验证ID
            if not isinstance(edge_data['id'], int) or edge_data['id'] <= 0:
                self._handle_error(f"Invalid edge ID: {edge_data['id']}")
                return False
            
            # 验证类型
            valid_types = [
                'Line', 'Circle', 'Ellipse', 'Parabola', 'Hyperbola',
                'BSplineCurve', 'BezierCurve', 'OffsetCurve', 'TrimmedCurve', 'Unknown'
            ]
            if edge_data['type'] not in valid_types:
                self._handle_warning(f"Unknown edge type: {edge_data['type']}")
            
            # 验证特征数据
            features = edge_data['features']
            if not isinstance(features, dict):
                self._handle_error("Edge features must be a dictionary")
                return False
            
            # 验证公共特征
            if 'common' in features:
                if not self._validate_common_edge_features(features['common']):
                    return False
            
            # 验证类型特定特征
            if 'type_specific' in features:
                if not self._validate_type_specific_edge_features(
                    features['type_specific'], edge_data['type']
                ):
                    return False
            
            return True
            
        except Exception as e:
            self._handle_error(f"Error validating edge data: {e}")
            return False
    
    def validate_face_data(self, face_data: Dict[str, Any]) -> bool:
        """验证面数据
        
        Args:
            face_data: 面数据字典
            
        Returns:
            验证是否通过
        """
        try:
            # 检查必需字段
            required_fields = ['id', 'type', 'features']
            for field in required_fields:
                if field not in face_data:
                    self._handle_error(f"Missing required field in face data: {field}")
                    return False
            
            # 验证ID
            if not isinstance(face_data['id'], int) or face_data['id'] <= 0:
                self._handle_error(f"Invalid face ID: {face_data['id']}")
                return False
            
            # 验证类型
            valid_types = [
                'Plane', 'CylindricalSurface', 'ConicalSurface', 'SphericalSurface',
                'ToroidalSurface', 'BezierSurface', 'BSplineSurface', 'OffsetSurface',
                'SurfaceOfRevolution', 'SurfaceOfLinearExtrusion', 'Unknown'
            ]
            if face_data['type'] not in valid_types:
                self._handle_warning(f"Unknown face type: {face_data['type']}")
            
            # 验证特征数据
            features = face_data['features']
            if not isinstance(features, dict):
                self._handle_error("Face features must be a dictionary")
                return False
            
            # 验证公共特征
            if 'common' in features:
                if not self._validate_common_face_features(features['common']):
                    return False
            
            # 验证类型特定特征
            if 'type_specific' in features:
                if not self._validate_type_specific_face_features(
                    features['type_specific'], face_data['type']
                ):
                    return False
            
            return True
            
        except Exception as e:
            self._handle_error(f"Error validating face data: {e}")
            return False
    
    def validate_complete_dataset(self, dataset: Dict[str, Any]) -> bool:
        """验证完整数据集
        
        Args:
            dataset: 完整数据集
            
        Returns:
            验证是否通过
        """
        try:
            # 检查顶级结构
            required_sections = ['metadata', 'edges', 'faces']
            for section in required_sections:
                if section not in dataset:
                    self._handle_error(f"Missing required section: {section}")
                    return False
            
            # 验证元数据
            if not self._validate_metadata(dataset['metadata']):
                return False
            
            # 验证边数据
            edges = dataset['edges']
            if not isinstance(edges, list):
                self._handle_error("Edges must be a list")
                return False
            
            for i, edge in enumerate(edges):
                if not self.validate_edge_data(edge):
                    self._handle_error(f"Edge validation failed at index {i}")
                    return False
            
            # 验证面数据
            faces = dataset['faces']
            if not isinstance(faces, list):
                self._handle_error("Faces must be a list")
                return False
            
            for i, face in enumerate(faces):
                if not self.validate_face_data(face):
                    self._handle_error(f"Face validation failed at index {i}")
                    return False
            
            # 验证数量一致性
            metadata = dataset['metadata']
            if len(edges) != metadata.get('total_edges', 0):
                self._handle_warning(f"Edge count mismatch: {len(edges)} vs {metadata.get('total_edges')}")
            
            if len(faces) != metadata.get('total_faces', 0):
                self._handle_warning(f"Face count mismatch: {len(faces)} vs {metadata.get('total_faces')}")
            
            return True
            
        except Exception as e:
            self._handle_error(f"Error validating complete dataset: {e}")
            return False
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """验证元数据"""
        required_fields = ['extractor_version', 'extraction_time', 'total_edges', 'total_faces']
        
        for field in required_fields:
            if field not in metadata:
                self._handle_error(f"Missing metadata field: {field}")
                return False
        
        # 验证数量字段为非负整数
        for count_field in ['total_edges', 'total_faces']:
            value = metadata[count_field]
            if not isinstance(value, int) or value < 0:
                self._handle_error(f"Invalid {count_field}: {value}")
                return False
        
        return True
    
    def _validate_common_edge_features(self, common_features: Dict[str, Any]) -> bool:
        """验证边的公共特征"""
        # 验证参数范围
        if 'parameter_range' in common_features:
            param_range = common_features['parameter_range']
            if not isinstance(param_range, list) or len(param_range) != 2:
                self._handle_error("Parameter range must be a list of two numbers")
                return False
            
            if not all(isinstance(x, (int, float)) for x in param_range):
                self._handle_error("Parameter range values must be numbers")
                return False
        
        # 验证边界盒
        if 'bounding_box' in common_features:
            bbox = common_features['bounding_box']
            if not isinstance(bbox, list) or len(bbox) != 6:
                self._handle_error("Bounding box must be a list of 6 numbers")
                return False
            
            if not all(isinstance(x, (int, float)) for x in bbox):
                self._handle_error("Bounding box values must be numbers")
                return False
        
        return True
    
    def _validate_common_face_features(self, common_features: Dict[str, Any]) -> bool:
        """验证面的公共特征"""
        # 验证UV参数域
        if 'uv_bounds' in common_features:
            uv_bounds = common_features['uv_bounds']
            if not isinstance(uv_bounds, list) or len(uv_bounds) != 4:
                self._handle_error("UV bounds must be a list of 4 numbers")
                return False
            
            if not all(isinstance(x, (int, float)) for x in uv_bounds):
                self._handle_error("UV bounds values must be numbers")
                return False
        
        return True
    
    def _validate_type_specific_edge_features(self, features: Dict[str, Any], edge_type: str) -> bool:
        """验证边的类型特定特征"""
        # 这里可以根据不同的边类型进行具体验证
        # 现在只做基本验证
        return True
    
    def _validate_type_specific_face_features(self, features: Dict[str, Any], face_type: str) -> bool:
        """验证面的类型特定特征"""
        # 这里可以根据不同的面类型进行具体验证
        # 现在只做基本验证
        return True
    
    def _handle_error(self, message: str):
        """处理错误"""
        self.logger.error(message)
        if self.strict_mode:
            raise ValueError(message)
    
    def _handle_warning(self, message: str):
        """处理警告"""
        self.logger.warning(message)