"""Day 24: Transformer - 自注意力机制"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class SelfAttention(nn.Module):
    """自注意力机制"""
    
    def __init__(self, embed_size, heads):
        super(SelfAttention, self).__init__()
        
        self.embed_size = embed_size
        self.heads = heads
        self.head_dim = embed_size // heads
        
        assert self.head_dim * heads == embed_size, "embed_size必须能被heads整除"
        
        self.values = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.keys = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.queries = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.fc_out = nn.Linear(heads * self.head_dim, embed_size)
    
    def forward(self, values, keys, queries, mask=None):
        N = queries.shape[0]
        value_len, key_len, query_len = values.shape[1], keys.shape[1], queries.shape[1]
        
        # 分头
        values = values.reshape(N, value_len, self.heads, self.head_dim)
        keys = keys.reshape(N, key_len, self.heads, self.head_dim)
        queries = queries.reshape(N, query_len, self.heads, self.head_dim)
        
        # 线性变换
        values = self.values(values)
        keys = self.keys(keys)
        queries = self.queries(queries)
        
        # 计算注意力分数
        energy = torch.einsum("nqhd,nkhd->nhqk", [queries, keys])
        
        if mask is not None:
            energy = energy.masked_fill(mask == 0, float("-1e20"))
        
        attention = torch.softmax(energy / (self.embed_size ** (1/2)), dim=3)
        
        # 加权求和
        out = torch.einsum("nhqk,nvhd->nqhd", [attention, values]).reshape(
            N, query_len, self.heads * self.head_dim
        )
        
        return self.fc_out(out)


class TransformerBlock(nn.Module):
    """Transformer块"""
    
    def __init__(self, embed_size, heads, dropout, forward_expansion):
        super(TransformerBlock, self).__init__()
        
        self.attention = SelfAttention(embed_size, heads)
        self.norm1 = nn.LayerNorm(embed_size)
        self.norm2 = nn.LayerNorm(embed_size)
        
        self.feed_forward = nn.Sequential(
            nn.Linear(embed_size, forward_expansion * embed_size),
            nn.ReLU(),
            nn.Linear(forward_expansion * embed_size, embed_size),
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, value, key, query, mask):
        attention = self.attention(value, key, query, mask)
        
        # 残差连接 + LayerNorm
        x = self.dropout(self.norm1(attention + query))
        forward = self.feed_forward(x)
        out = self.dropout(self.norm2(forward + x))
        
        return out


class PositionalEncoding(nn.Module):
    """位置编码"""
    
    def __init__(self, embed_size, max_len=5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, embed_size)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, embed_size, 2).float() * (-math.log(10000.0) / embed_size))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class SimpleTransformer(nn.Module):
    """简单Transformer模型"""
    
    def __init__(self, vocab_size, embed_size, num_heads, num_layers, forward_expansion, dropout):
        super(SimpleTransformer, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, embed_size)
        self.positional_encoding = PositionalEncoding(embed_size)
        
        self.layers = nn.ModuleList([
            TransformerBlock(embed_size, heads=num_heads, dropout=dropout, forward_expansion=forward_expansion)
            for _ in range(num_layers)
        ])
        
        self.fc_out = nn.Linear(embed_size, vocab_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, mask=None):
        # 嵌入 + 位置编码
        out = self.dropout(self.embedding(x) * math.sqrt(self.embed_size if hasattr(self, 'embed_size') else 64))
        out = self.positional_encoding(out)
        
        # Transformer层
        for layer in self.layers:
            out = layer(out, out, out, mask)
        
        return self.fc_out(out)


if __name__ == "__main__":
    print("Transformer教程\n")
    
    # 测试自注意力
    embed_size = 64
    heads = 8
    
    attention = SelfAttention(embed_size, heads)
    x = torch.randn(2, 10, embed_size)  # batch=2, seq_len=10
    out = attention(x, x, x)
    print(f"自注意力输出形状: {out.shape}")
    
    # 测试Transformer块
    transformer_block = TransformerBlock(embed_size, heads, dropout=0.1, forward_expansion=4)
    out = transformer_block(x, x, x, mask=None)
    print(f"Transformer块输出形状: {out.shape}")
    
    # 测试位置编码
    pos_encoding = PositionalEncoding(embed_size)
    out = pos_encoding(x)
    print(f"位置编码输出形状: {out.shape}")
    
    print("\n教程完成！")