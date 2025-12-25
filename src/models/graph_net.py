import torch
from torch import nn
import torch.nn.functional as F
from dgl.nn.pytorch.conv import NNConv
from .hetero import HeteroGraphConv
import dgl

class _MLP(nn.Module):
    """Multi-layer Perceptron with linear output"""

    def __init__(self, num_layers, input_dim, hidden_dim, output_dim, dropout=0.5):
        """
        MLP with linear output
        Args:
            num_layers (int): The number of linear layers in the MLP
            input_dim (int): Input feature dimension
            hidden_dim (int): Hidden feature dimensions for all hidden layers
            output_dim (int): Output feature dimension

        Raises:
            ValueError: If the given number of layers is <1
        """
        super(_MLP, self).__init__()
        if num_layers < 1:
            raise ValueError("Number of layers should be positive!")
        
        self.num_layers = num_layers
        self.dropout = nn.Dropout(dropout)
        
        # 统一使用 ModuleList 构建网络层
        self.layers = nn.ModuleList()
        
        if num_layers == 1:
            self.layers.append(nn.Linear(input_dim, output_dim))
        else:
            # 第一层
            self.layers.append(nn.Linear(input_dim, hidden_dim))
            # 中间层
            for _ in range(num_layers - 2):
                self.layers.append(nn.Linear(hidden_dim, hidden_dim))
            # 输出层
            self.layers.append(nn.Linear(hidden_dim, output_dim))

    def forward(self, x):
        h = x
        # 对除最后一层外的所有层应用激活函数和dropout
        for layer in self.layers[:-1]:
            h = layer(h)
            h = F.leaky_relu(h, inplace=True)
            h = self.dropout(h)
        # 最后一层不使用激活函数
        return self.layers[-1](h)


class _HeteroEdgeConv(nn.Module):
    def __init__(
        self,
        edge_feats,
        out_feats,
        node_feats,
        num_mlp_layers=2,
        hidden_mlp_dim=32,
        dropout=0.5,
    ):
        super(_HeteroEdgeConv, self).__init__()
        if isinstance(edge_feats, dict):
            self.mlp = nn.ModuleDict()
            for etype,v in edge_feats.items():
                self.mlp[etype] = _MLP(num_mlp_layers, v, hidden_mlp_dim, out_feats, dropout=dropout)
        self.layer_norm = nn.LayerNorm(out_feats)
        self.eps = torch.nn.Parameter(torch.FloatTensor([0.0]))

    def forward(self, graph, h, efeat):
        efeat_={}
        for srctype, etype, dsttype in graph.canonical_etypes:
            he = efeat[(srctype,etype,dsttype)] 
            he = self.mlp[etype]((1 + self.eps) * he)
            he = self.layer_norm(he)
            efeat_[(srctype,etype,dsttype)] = he
        return efeat_
    
class _HeteroNodeConv(nn.Module):
    def __init__(
        self,
        node_feats,
        out_feats,
        edge_feats,
        num_mlp_layers=2,
        hidden_mlp_dim=32,
        fusion_type="residual",  
        dropout=0.5,
    ):
        """
        This module implements Eq. 1 from the paper where the node features are
        updated using the neighboring node and edge features.

        Args:
            edge_types_dim (dict): 包含边类型、边维度、节点维度信息的字典
            out_feats (int): Output feature dimension
            num_mlp_layers (int, optional): Number of layers used in the MLP. Defaults to 2.
            hidden_mlp_dim (int, optional): Hidden feature dimension in the MLP. Defaults to 64.
            fusion_type (str, optional): Feature fusion type. Options: "residual", "weighted", "attention". Defaults to "residual".
        """
        super(_HeteroNodeConv, self).__init__()
        aggregator_type="sum"
        mods = {}
        
        if isinstance(edge_feats, dict):
            for etype,v in edge_feats.items():
                
                edge_func = nn.Sequential(
                    nn.Linear(v, node_feats, bias=False),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                    nn.Linear(node_feats,node_feats * out_feats, bias=False),
                )
                mods[etype] = NNConv(
                        node_feats, 
                        out_feats=out_feats, 
                        edge_func=edge_func, 
                        aggregator_type=aggregator_type,
                        bias=False
                    )
        self.h_gconv = HeteroGraphConv(mods=mods, aggregate="sum")

        # 为每种节点类型创建批归一化层
        self.layer_norm = nn.LayerNorm(hidden_mlp_dim)
        self.eps = torch.nn.Parameter(torch.FloatTensor([0.0]))
        self.mlp = _MLP(num_mlp_layers, out_feats, hidden_mlp_dim, hidden_mlp_dim, dropout=dropout)
        # 特征融合类型
        self.fusion_type = fusion_type

    def _fuse_features(self, h_original, h_conv):
        """
        特征融合方法
        
        Args:
            h_original: 原始特征 [N, node_feats]
            h_conv: 卷积后的特征 [N, out_feats]
            
        Returns:
            h_fused: 融合后的特征 [N, out_feats]
        """
        # 如果维度不匹配，先投影原始特征
        if self.fusion_type == "residual":
            # 方式1: 残差连接（直接相加）
            h_fused = h_original + h_conv
        return h_fused
    
    def forward(self, graph, h, efeat):
        # 通过异构图卷积
        h = {ntype: (1 + self.eps) * h[ntype] for ntype in h.keys()}

        mod_args = {}
        for stype, etype, dtype in graph.canonical_etypes:
            # 为每个关系准备边特征
            if (stype, etype, dtype) in efeat:
                mod_args[(stype, etype, dtype)] = efeat[(stype, etype, dtype)]
        
        h_dst_node = self.h_gconv(graph, h, mod_args=mod_args)
        
        # 按节点类型分别处理，避免不必要的concat/split
        h_ = {}
        for ntype in h.keys():
            # 获取原始特征和卷积后的特征
            h_original = h[ntype]
            
            # 融合特征
            if ntype in h_dst_node:
                h_conv = h_dst_node[ntype]
                h_fused = self._fuse_features(h_original, h_conv)
            else:
                h_fused = h_original
            
            # 通过MLP和归一化
            h_fused = self.mlp(h_fused)
            h_fused = self.layer_norm(h_fused)
            h_[ntype] = h_fused
        
        return h_


class SemanticAttention(nn.Module):
    def __init__(self, in_size, hidden_size=128):
        super(SemanticAttention, self).__init__()
        self.project = nn.Sequential(
            nn.Linear(in_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1, bias=True),
        )

    def forward(self, z):
        w = self.project(z)
        beta = torch.softmax(w,dim=0)  # (M, 1)
        h = (beta * z).sum(0)  # (D)
        return h
        
class HeteroGraphPooling(nn.Module):
    def __init__(
        self,
        in_size,
        hidden_size=128,
        attention_mode="semantic",
        internal_pool_type="mean",
    ):
        """
        异构图池化模块
        
        Args:
            pool_type (str): 池化类型，'max', 'sum', 'mean'
            dropout (float): dropout比率
        """
        super(HeteroGraphPooling, self).__init__()
        self.attention_mode = attention_mode
        self.internal_pool_type = internal_pool_type

        if attention_mode == "semantic":
            self.semantic_attention = SemanticAttention(in_size=in_size, hidden_size=hidden_size)
     

    def get_sub_graph(self, g, h):
        batch_num_nodes = {}
        for ntype in g.ntypes:
            batch_num_nodes[ntype] = g.batch_num_nodes(ntype)

        batch_size = len(list(batch_num_nodes.values())[0])
        
        # 预分配列表
        sub_graphs = [{} for _ in range(batch_size)]
        
        # 并行处理所有节点类型
        for node_type, num_nodes_per_graph in batch_num_nodes.items():
            if node_type in h:
                # 一次性分割
                split_features = torch.split(
                    h[node_type], 
                    num_nodes_per_graph.tolist(), 
                    dim=0
                )
                # 批量分配
                for i, features in enumerate(split_features):
                    if features.size(0) > 0:
                        sub_graphs[i][node_type] = features
        
        return sub_graphs
        
    def _pool(self, h, pool_type="sum"):
        if pool_type == "sum":
            return torch.sum(h, dim=0)
        if pool_type == "mean":
            return torch.mean(h, dim=0)
        if pool_type == "max":
            return torch.max(h, dim=0)[0]
        raise ValueError(f"Unsupported pool_type: {pool_type}")

    def _pool_node_types(self, type_feature_dict):
        pooled = [
            self._pool(feat, pool_type=self.internal_pool_type)
            for feat in type_feature_dict.values()
            if feat.size(0) > 0
        ]
        if not pooled:
            raise ValueError("图中所有节点类型均为空，无法进行池化")
        return torch.stack(pooled, dim=0)

    def forward(self, g, h):
        if self.attention_mode == "semantic":
            if g.batch_size == 1:
                type_embeddings = self._pool_node_types(h)
                pooled_h = self.semantic_attention(type_embeddings)
                return pooled_h.unsqueeze(0)

            graph = self.get_sub_graph(g, h)
            graph_vectors = []
            for sub_graph in graph:
                type_embeddings = self._pool_node_types(sub_graph)
                graph_vectors.append(self.semantic_attention(type_embeddings))
            graph_vectors = torch.stack(graph_vectors)
            return graph_vectors
            


class UVNetHeteroGraphEncoder(nn.Module):
    def __init__(
        self,
        input_dim,
        input_edge_dim,
        output_dim,
        hidden_dim=32,
        learn_eps=True,
        num_layers=3,
        num_mlp_layers=2,
        fusion_type="residual", 
        internal_pool_type="mean",
        pred_dropout=0.5,
    ):
        """
        This is the graph neural network used for message-passing features in the
        face-adjacency graph.  (see Section 3.2, Message passing in paper)

        Args:
            input_dim ([type]): [description]
            input_edge_dim ([type]): [description]
            output_dim ([type]): [description]
            hidden_dim (int, optional): [description]. Defaults to 64.
            learn_eps (bool, optional): [description]. Defaults to True.
            num_layers (int, optional): [description]. Defaults to 3.
            num_mlp_layers (int, optional): [description]. Defaults to 2.
            fusion_type (str, optional): Feature fusion type for node conv layers. 
                Options: "residual", "weighted", "attention". Defaults to "residual".
        """
        super(UVNetHeteroGraphEncoder, self).__init__()
        self.num_layers = num_layers
        self.learn_eps = learn_eps

        # List of layers for node and edge feature message passing
        self.node_conv_layers = torch.nn.ModuleList()
        self.edge_conv_layers = torch.nn.ModuleList()
        layer_edge_feats = input_edge_dim
        # 统一构建所有节点卷积层
        for layer_idx in range(self.num_layers - 1):
            # 第一层使用 input_dim，后续层使用 hidden_dim
            is_first_layer = (layer_idx == 0)
            node_feat_dim = input_dim if is_first_layer else hidden_dim
            out_feat_dim = input_dim if is_first_layer else hidden_dim
            dropout=0.5 if is_first_layer else 0.5
            # 第一层使用原始边特征维度，后续层边特征维度等于节点特征维度
            # 构建边卷积层（所有层共享）
            self.edge_conv_layers.append(_HeteroEdgeConv(
                    edge_feats=layer_edge_feats,
                    node_feats=node_feat_dim,
                    out_feats=out_feat_dim,
                    hidden_mlp_dim=node_feat_dim,
                    num_mlp_layers=num_mlp_layers,
                    dropout=dropout,
                ))
            layer_edge_feats = {
                    etype: node_feat_dim for etype in input_edge_dim.keys()
                }
            self.node_conv_layers.append(
                _HeteroNodeConv(
                    node_feats=node_feat_dim,
                    out_feats=out_feat_dim,
                    edge_feats=layer_edge_feats,
                    num_mlp_layers=num_mlp_layers,
                    hidden_mlp_dim=hidden_dim,
                    fusion_type=fusion_type,
                    dropout=dropout,
                )
            )
        self.pool = HeteroGraphPooling(
                    in_size=hidden_dim ,
                    hidden_size=hidden_dim,
                    internal_pool_type=internal_pool_type,
                    )
        self.linears_prediction = torch.nn.ModuleList()
        for _ in range(self.num_layers):
            self.linears_prediction.append(nn.Sequential(
                        nn.LayerNorm(hidden_dim),
                        nn.Linear(hidden_dim, output_dim),
                        nn.Dropout(pred_dropout)
                    ))
        self.linears_h = nn.Linear(input_dim, hidden_dim)

    def forward(self, g, h, he):
        # 添加第一层的输出（输入特征）

        h1 = {}
        for ntype in h.keys():
            h1[ntype] = self.linears_h(h[ntype])
        hidden_rep = [h1]

        for i in range(self.num_layers - 1):
            # Update edge features
            he = self.edge_conv_layers[i](g, h, he)
            # Update node features
            h = self.node_conv_layers[i](g, h, he)
            hidden_rep.append(h)

        score_over_layer = 0
        for i, h in enumerate(hidden_rep):
            pooled_h = self.pool(g, h)
            score_over_layer += self.linears_prediction[i](pooled_h)
        return score_over_layer


class DGI(nn.Module):
    """
    自监督对比学习模型（仅核心网络与配置）
    """

    def __init__(
        self,
        input_node_dim,
        edge_emb_dim,
        node_emb_dim=32,
        graph_emb_dim=64,
        hidden_dim=32,
        dropout=0.5,
        num_layers=3,
        num_mlp_layers=2,
        internal_pool_type="mean",
        pred_dropout=0.5,
    ):
        super().__init__()
        self.graph_emb_dim = graph_emb_dim
        self.node_linears = nn.ModuleDict()
        for ntype, dim in input_node_dim.items():
            self.node_linears[ntype] = nn.Linear(dim, node_emb_dim, bias=False)

        self.graph_encoder = UVNetHeteroGraphEncoder(
            input_dim=node_emb_dim,
            input_edge_dim=edge_emb_dim,
            output_dim=graph_emb_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_mlp_layers=num_mlp_layers,
            internal_pool_type=internal_pool_type,
            pred_dropout=pred_dropout,
        )

    def forward(self, batched_graph: dgl.DGLGraph):
        h = {}
        for ntype in batched_graph.ntypes:
            node_feat = batched_graph.nodes[ntype].data["x"]
            h[ntype] = self.node_linears[ntype](node_feat)

        he = {}
        for etype in batched_graph.canonical_etypes:
            edge_feat = batched_graph.edges[etype].data["x"]
            he[etype] = edge_feat

        graph_emb = self.graph_encoder(batched_graph, h, he)
        return graph_emb