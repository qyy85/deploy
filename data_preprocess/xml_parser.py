import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from .node import NodeFactory
from .edge import EdgeFactory

class XMLParser:
    """XML解析器类"""
    
    def __init__(self):
        self.supported_node_types = NodeFactory.get_supported_types()
        self.supported_edge_types = EdgeFactory.get_supported_types()
    
    def parse(self, xml_content: str) -> Dict[str, List[Dict]]:
        """解析XML内容，返回结构化数据"""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            try:
                # 尝试处理编码问题
                root = ET.fromstring(xml_content.encode('utf-8').decode('gb2312', errors='ignore'))
            except Exception as e:
                raise ValueError(f"XML解析失败: {e}")
        
        parsed_data = {
            'nodes': [],
            'edges': []
        }
        
        # 解析节点
        self._parse_nodes(root, parsed_data)
        
        # 解析边
        self._parse_edges(root, parsed_data)
        
        return parsed_data
    
    def _parse_nodes(self, root: ET.Element, parsed_data: Dict):
        """解析节点数据"""
        point_set = root.find(".//Item[@type='Point_Set']")
        if point_set is not None:
            for point in point_set.findall("./Item[@type='Point']"):
                raw_id = point.get('id')
                params_elem = point.find('./Params')
                
                if params_elem is None or len(params_elem) == 0:
                    continue
                
                # 提取参数
                params = []
                for param in params_elem:
                    param_data = {
                        'name': param.get('name', ''),
                        'type': param.get('type', ''),
                        'value': param.get('value', '')
                    }
                    params.append(param_data)
                
                # 第一个参数通常是节点类型
                node_type = params[0].get('value', 'unknown') if params else 'unknown'
                
                if node_type in self.supported_node_types:
                    parsed_data['nodes'].append({
                        'id': raw_id,
                        'type': node_type,
                        'params': params
                    })
                else:
                    print(f"Warning: 不支持的节点类型 '{node_type}', 跳过节点 {raw_id}")
    
    def _parse_edges(self, root: ET.Element, parsed_data: Dict):
        """解析边数据"""
        line_set = root.find(".//Item[@type='Line_Set']")
        if line_set is not None:
            for line in line_set.findall("./Item"):
                params_elem = line.find('./Params')
                
                if params_elem is None or len(params_elem) == 0:
                    continue
                
                # 提取参数
                params = []
                for param in params_elem:
                    param_data = {
                        'name': param.get('name', ''),
                        'type': param.get('type', ''),
                        'value': param.get('value', '')
                    }
                    params.append(param_data)
                
                # 解析边信息
                edge_info = self._extract_edge_info(params)
                if edge_info:
                    parsed_data['edges'].append(edge_info)
    
    def _extract_edge_info(self, params: List[Dict]) -> Optional[Dict]:
        """从参数中提取边信息"""
        connection_type = "unknown"
        src_id = None
        dst_id = None
        
        for param in params:
            name = param.get('name', '')
            value = param.get('value', '')
            
            if name == "连接类型":
                if value == "倒圆连接":
                    connection_type = "arc"
                elif value == "直接连接":
                    connection_type = "straight"
            elif name == "面序号一":
                src_id = value
            elif name == "面序号二":
                dst_id = value
        
        # 验证边信息
        if (connection_type in self.supported_edge_types and 
            src_id is not None and dst_id is not None):
            return {
                'type': connection_type,
                'src_id': src_id,
                'dst_id': dst_id,
                'params': params
            }
        else:
            if connection_type not in self.supported_edge_types:
                print(f"Warning: 不支持的边类型 '{connection_type}'")
            if src_id is None or dst_id is None:
                print(f"Warning: 边缺少端点信息: src={src_id}, dst={dst_id}")
            return None