"""
LVGL 字体位图压缩算法

实现 RLE (Run-Length Encoding) 压缩算法，用于压缩字形位图数据。
参考 lv_font_conv/lib/font/compress.js

压缩算法说明：
1. RLE (Run-Length Encoding) 游程编码
2. 支持 XOR 预过滤器以提高压缩率
3. 针对 LVGL 优化的变体 (Modified I3BN)

算法特点：
- 最小重复次数为 1
- 使用 1-bit 标记重复 (最多 10 次)
- 使用 6-bit 计数器表示更长的重复 (最多 63+10+1=74 次)
"""

from typing import List, Optional
import numpy as np
from io import BytesIO


class BitStream:
    """
    位流写入器
    
    支持按位写入数据，自动处理字节边界。
    """
    
    def __init__(self):
        self.buffer = BytesIO()
        self.current_byte = 0
        self.bit_position = 0  # 当前字节中的位位置 (0-7)
        
    def write_bits(self, value: int, num_bits: int) -> None:
        """
        写入指定位数的值
        
        Args:
            value: 要写入的值
            num_bits: 位数 (1-32)
        """
        if num_bits <= 0 or num_bits > 32:
            raise ValueError(f"num_bits 必须在 1-32 之间，当前为 {num_bits}")
        
        # 确保值不会溢出
        mask = (1 << num_bits) - 1
        value &= mask
        
        # 逐位写入
        for i in range(num_bits - 1, -1, -1):
            bit = (value >> i) & 1
            self.current_byte = (self.current_byte << 1) | bit
            self.bit_position += 1
            
            # 写满一个字节
            if self.bit_position == 8:
                self.buffer.write(bytes([self.current_byte]))
                self.current_byte = 0
                self.bit_position = 0
    
    def flush(self) -> bytes:
        """
        刷新缓冲区，返回所有数据
        
        如果有未写满的字节，会填充 0 并写入。
        """
        # 如果有未写完的位，填充 0 并写入
        if self.bit_position > 0:
            self.current_byte <<= (8 - self.bit_position)
            self.buffer.write(bytes([self.current_byte]))
            self.current_byte = 0
            self.bit_position = 0
        
        data = self.buffer.getvalue()
        self.buffer = BytesIO()
        return data
    
    @property
    def byte_count(self) -> int:
        """已写入的字节数"""
        count = len(self.buffer.getvalue())
        if self.bit_position > 0:
            count += 1
        return count


def count_same(pixels: np.ndarray, offset: int) -> int:
    """
    计算从指定偏移开始的连续相同像素数量
    
    Args:
        pixels: 像素数组
        offset: 起始偏移
        
    Returns:
        连续相同像素的数量
    """
    if offset >= len(pixels):
        return 0
    
    value = pixels[offset]
    count = 1
    
    for i in range(offset + 1, len(pixels)):
        if pixels[i] != value:
            break
        count += 1
    
    return count


def compress_rle(
    pixels: np.ndarray,
    bpp: int,
    min_repeat: int = 1
) -> bytes:
    """
    使用 RLE 算法压缩像素数据（无 XOR 预过滤）
    
    Args:
        pixels: 像素数组 (一维)
        bpp: 每像素位数 (1-4)
        min_repeat: 进入 RLE 模式的最小重复次数
        
    Returns:
        压缩后的字节数据
        
    算法说明：
    1. 如果连续像素 <= min_repeat，直接写入
    2. 如果连续像素 > min_repeat:
       - 先写入 min_repeat 个原始值
       - 如果剩余 <= 10 个，用 1-bit 标记每个重复
       - 如果剩余 > 10 个，用 11 个 1-bit + 6-bit 计数器
    """
    if bpp < 1 or bpp > 4:
        raise ValueError(f"BPP 必须在 1-4 之间，当前为 {bpp}")
    
    if len(pixels) == 0:
        return b''
    
    # 常量定义
    RLE_SKIP_COUNT = min_repeat          # 最小重复数进入 RLE
    RLE_BIT_COLLAPSED_COUNT = 10         # 使用 1-bit 标记的最大重复数
    RLE_COUNTER_BITS = 6                 # 计数器位数
    RLE_COUNTER_MAX = (1 << RLE_COUNTER_BITS) - 1  # 63
    RLE_MAX_REPEATS = RLE_COUNTER_MAX + RLE_BIT_COLLAPSED_COUNT + 1  # 74
    
    bs = BitStream()
    offset = 0
    
    while offset < len(pixels):
        pixel = pixels[offset]
        same = count_same(pixels, offset)
        
        # 限制重复数量
        if same > RLE_MAX_REPEATS + RLE_SKIP_COUNT:
            same = RLE_MAX_REPEATS + RLE_SKIP_COUNT
        
        offset += same
        
        # 不够 RLE，直接写入
        if same <= RLE_SKIP_COUNT:
            for _ in range(same):
                bs.write_bits(pixel, bpp)
            continue
        
        # 写入跳过的头部
        for _ in range(RLE_SKIP_COUNT):
            bs.write_bits(pixel, bpp)
        
        same -= RLE_SKIP_COUNT
        
        # 使用 bit 扩展
        if same <= RLE_BIT_COLLAPSED_COUNT:
            bs.write_bits(pixel, bpp)
            for i in range(same):
                if i < same - 1:
                    bs.write_bits(1, 1)  # 重复标记
                else:
                    bs.write_bits(0, 1)  # 最后一个
            continue
        
        # 使用计数器
        same -= RLE_BIT_COLLAPSED_COUNT + 1
        
        bs.write_bits(pixel, bpp)
        for _ in range(RLE_BIT_COLLAPSED_COUNT + 1):
            bs.write_bits(1, 1)
        bs.write_bits(same, RLE_COUNTER_BITS)
    
    return bs.flush()


def apply_xor_prefilter(pixels: np.ndarray) -> np.ndarray:
    """
    应用 XOR 预过滤器
    
    将每行像素与前一行进行 XOR 操作，以提高压缩率。
    第一行保持不变。
    
    Args:
        pixels: 像素数组 (二维: height x width)
        
    Returns:
        过滤后的像素数组 (一维)
    """
    if pixels.ndim != 2:
        raise ValueError("XOR 预过滤需要二维数组 (height, width)")
    
    height, width = pixels.shape
    filtered = np.zeros_like(pixels)
    
    # 第一行不变
    filtered[0] = pixels[0]
    
    # 后续行与前一行 XOR
    for y in range(1, height):
        filtered[y] = pixels[y] ^ pixels[y - 1]
    
    return filtered.flatten()


def compress_rle_with_xor(
    pixels: np.ndarray,
    bpp: int,
    width: int,
    height: int,
    min_repeat: int = 1
) -> bytes:
    """
    使用 RLE + XOR 预过滤压缩像素数据
    
    Args:
        pixels: 像素数组 (一维或二维)
        bpp: 每像素位数 (1-4)
        width: 图像宽度
        height: 图像高度
        min_repeat: 进入 RLE 模式的最小重复次数
        
    Returns:
        压缩后的字节数据
    """
    # 转换为二维数组
    if pixels.ndim == 1:
        pixels = pixels.reshape(height, width)
    elif pixels.shape != (height, width):
        raise ValueError(f"像素数组形状 {pixels.shape} 与指定尺寸 ({height}, {width}) 不匹配")
    
    # 应用 XOR 预过滤
    filtered = apply_xor_prefilter(pixels)
    
    # RLE 压缩
    return compress_rle(filtered, bpp, min_repeat)


def decompress_rle(
    data: bytes,
    bpp: int,
    expected_pixels: int
) -> np.ndarray:
    """
    解压 RLE 数据（用于测试）
    
    Args:
        data: 压缩数据
        bpp: 每像素位数
        expected_pixels: 期望的像素数量
        
    Returns:
        解压后的像素数组
    """
    if bpp < 1 or bpp > 4:
        raise ValueError(f"BPP 必须在 1-4 之间，当前为 {bpp}")
    
    # 常量定义
    RLE_SKIP_COUNT = 1
    RLE_BIT_COLLAPSED_COUNT = 10
    RLE_COUNTER_BITS = 6
    
    pixels = []
    byte_offset = 0
    bit_offset = 0
    
    def read_bits(num_bits: int) -> int:
        """从数据中读取指定位数"""
        nonlocal byte_offset, bit_offset
        
        value = 0
        for _ in range(num_bits):
            if byte_offset >= len(data):
                return 0
            
            bit = (data[byte_offset] >> (7 - bit_offset)) & 1
            value = (value << 1) | bit
            bit_offset += 1
            
            if bit_offset == 8:
                byte_offset += 1
                bit_offset = 0
        
        return value
    
    while len(pixels) < expected_pixels:
        # 读取像素值
        pixel = read_bits(bpp)
        pixels.append(pixel)
        
        # 检查是否有重复
        repeat_count = 0
        
        # 读取 1-bit 标记
        while repeat_count < RLE_BIT_COLLAPSED_COUNT:
            bit = read_bits(1)
            if bit == 0:
                break
            pixels.append(pixel)
            repeat_count += 1
        
        # 如果达到最大 1-bit 重复，读取计数器
        if repeat_count == RLE_BIT_COLLAPSED_COUNT:
            counter = read_bits(RLE_COUNTER_BITS)
            for _ in range(counter):
                pixels.append(pixel)
    
    return np.array(pixels[:expected_pixels], dtype=np.uint8)


def calculate_compression_ratio(
    original_size: int,
    compressed_size: int
) -> float:
    """
    计算压缩率
    
    Args:
        original_size: 原始大小 (字节)
        compressed_size: 压缩后大小 (字节)
        
    Returns:
        压缩率 (0.0-1.0, 越小越好)
    """
    if original_size == 0:
        return 0.0
    return compressed_size / original_size


if __name__ == '__main__':
    # 简单测试
    print("🧪 RLE 压缩算法测试\n")
    
    # 测试 1: 简单重复
    pixels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2], dtype=np.uint8)
    compressed = compress_rle(pixels, bpp=4)
    print(f"测试 1 - 简单重复:")
    print(f"  原始: {pixels}")
    print(f"  原始大小: {len(pixels) * 4 // 8} 字节 (4-bit)")
    print(f"  压缩大小: {len(compressed)} 字节")
    print(f"  压缩率: {calculate_compression_ratio(len(pixels) * 4 // 8, len(compressed)):.2%}\n")
    
    # 测试 2: 无重复
    pixels = np.array([0, 1, 2, 3, 4, 5, 6, 7], dtype=np.uint8)
    compressed = compress_rle(pixels, bpp=4)
    print(f"测试 2 - 无重复:")
    print(f"  原始: {pixels}")
    print(f"  原始大小: {len(pixels) * 4 // 8} 字节 (4-bit)")
    print(f"  压缩大小: {len(compressed)} 字节")
    print(f"  压缩率: {calculate_compression_ratio(len(pixels) * 4 // 8, len(compressed)):.2%}\n")
    
    # 测试 3: 长重复
    pixels = np.array([5] * 100, dtype=np.uint8)
    compressed = compress_rle(pixels, bpp=4)
    print(f"测试 3 - 长重复:")
    print(f"  原始: [5] * 100")
    print(f"  原始大小: {len(pixels) * 4 // 8} 字节 (4-bit)")
    print(f"  压缩大小: {len(compressed)} 字节")
    print(f"  压缩率: {calculate_compression_ratio(len(pixels) * 4 // 8, len(compressed)):.2%}\n")
    
    print("✅ 测试完成!")
